// Copyright Metatype OÜ under the Elastic License 2.0 (ELv2). See LICENSE.md for usage.

use crate::codegen;
use crate::typegraph::{LoaderResult, TypegraphLoader};
use crate::utils::{ensure_venv, BasicAuth, Node};
use anyhow::{bail, Context, Error, Result};
use clap::Parser;
use colored::Colorize;
use common::typegraph::Typegraph;
use globset::Glob;
use ignore::gitignore::Gitignore;
use ignore::Match;
use indoc::indoc;
use notify::event::ModifyKind;
use notify::{
    recommended_watcher, Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher,
};
use reqwest::Url;
use serde_json::{self, json};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::thread::sleep;
use std::time::Duration;
use tiny_http::{Header, Response, Server};

use super::Action;

#[derive(Parser, Debug)]
pub struct Dev {
    /// Address of the typegate
    #[clap(short, long, value_parser, default_value_t = String::from("http://localhost:7890"))]
    gate: String,

    #[clap(short, long, value_parser, default_value_t = String::from("admin"))]
    username: String,

    #[clap(short, long, value_parser)]
    password: Option<String>,

    #[clap(long, value_parser, default_value_t = 5000)]
    port: u32,
}

fn log_err(err: Error) {
    println!("{}", format!("{err:?}").red());
}

impl Action for Dev {
    fn run(&self, dir: String) -> Result<()> {
        ensure_venv(&dir)?;

        let auth = if let Some(password) = &self.password {
            BasicAuth::new(self.username.clone(), password.clone())
        } else {
            BasicAuth::as_user(self.username.clone())?
        };

        let node = Node::new(&self.gate, Some(auth.clone()))?;

        let loaded = TypegraphLoader::new()
            .working_dir(&dir)
            .load_folder(".")
            .context("Error while loading typegraphs from folder");
        match loaded {
            Ok(loaded) => {
                push_loaded_typegraphs(loaded, &node);
            }
            Err(err) => log_err(err),
        }

        let watch_path = dir.clone();
        let _watcher = watch(dir.clone(), move |paths| {
            let loaded = TypegraphLoader::new()
                .working_dir(&watch_path)
                .skip_deno_modules()
                .load_files(paths);
            for (_path, res) in loaded.into_iter() {
                if let Result::Ok(tgs) = res {
                    for tg in tgs.into_iter() {
                        codegen::deno::codegen(tg, watch_path.clone())
                            .expect("could not run deno codegen");
                    }
                }
            }

            let loaded = TypegraphLoader::new().load_files(paths);

            push_loaded_typegraphs(loaded, &node);
        })
        .unwrap();

        let server = Server::http(format!("0.0.0.0:{}", self.port)).unwrap();

        for request in server.incoming_requests() {
            let url = Url::parse(&format!("http://dummy{}", request.url()))?;
            let query: HashMap<String, String> = url.query_pairs().into_owned().collect();

            let response = match url.path() {
                "/dev" => match query.get("node") {
                    Some(node) => {
                        let tgs = TypegraphLoader::new().working_dir(&dir).load_folder(&dir)?;
                        let node = Node::new(node, Some(auth.clone()))?;
                        push_loaded_typegraphs(tgs, &node);
                        Response::from_string(json!({"message": "reloaded"}).to_string())
                            .with_header(
                                "Content-Type: application/json".parse::<Header>().unwrap(),
                            )
                    }
                    _ => Response::from_string(json!({"error": "missing query 'node"}).to_string())
                        .with_status_code(400)
                        .with_header("Content-Type: application/json".parse::<Header>().unwrap()),
                },
                _ => Response::from_string(json!({"error": "not found"}).to_string())
                    .with_status_code(404)
                    .with_header("Content-Type: application/json".parse::<Header>().unwrap()),
            };

            request.respond(response)?;
        }

        Ok(())
    }
}

fn watch<H>(dir: String, handler: H) -> Result<RecommendedWatcher>
where
    H: Fn(&Vec<PathBuf>) + Send + 'static,
{
    let mut watcher = recommended_watcher(move |res: Result<Event, notify::Error>| {
        let event = res.unwrap();
        let paths = get_paths(&event);

        if !paths.is_empty() {
            match event.kind {
                EventKind::Create(_)
                | EventKind::Remove(_)
                | EventKind::Modify(ModifyKind::Data(_))
                | EventKind::Modify(ModifyKind::Name(_)) => {
                    println!("file change {:?}", event);
                    handler(&paths);
                }
                _ => {}
            }
        }
    })
    .unwrap();

    watcher
        .configure(
            Config::default()
                .with_poll_interval(Duration::from_secs(1))
                .with_compare_contents(true),
        )
        .unwrap();

    watcher
        .watch(Path::new(&dir), RecursiveMode::Recursive)
        .unwrap();
    Ok(watcher)
}

fn get_paths(event: &Event) -> Vec<PathBuf> {
    let gi = Gitignore::new(Path::new(".gitignore")).0;
    let gs = Glob::new("*.py").unwrap().compile_matcher();

    event
        .paths
        .iter()
        .filter(|path| {
            !matches!(
                gi.matched_path_or_any_parents(path, false),
                Match::Ignore(_)
            )
        })
        .filter(|path| gs.is_match(path))
        .map(|path| path.to_path_buf())
        .collect()
}

pub fn push_loaded_typegraphs(loaded: LoaderResult, node: &Node) {
    // TODO concurrent pushing
    for (path, res) in loaded.into_iter() {
        match res.with_context(|| format!("Error while loading typegraphs from {path}")) {
            Result::Ok(tgs) => {
                println!("Loaded typegraphs from {path}:");
                for tg in tgs.iter() {
                    print!("  → Pushing typegraph {name}...", name = tg.name().unwrap());
                    match push_typegraph(tg, node, 3) {
                        Ok(_) => {
                            println!(" {}", "Done.".to_owned().green());
                        }
                        Err(e) => {
                            println!("Could not push typegraph:\n{e:?}");
                        }
                    }
                }
                println!();
            }
            Result::Err(err) => {
                log_err(err);
            }
        }
    }
}

pub fn push_typegraph(tg: &Typegraph, node: &Node, backoff: u32) -> Result<()> {
    use crate::utils::graphql::{Error as GqlError, GraphqlErrorMessages, Query};
    let query = node.post("/typegate")?.gql(
        indoc! {"
            mutation InsertTypegraph {
                addTypegraph(fromString: $tg) {
                    name
                }
            }"}
        .to_string(),
        Some(json!({ "tg": serde_json::to_string(tg)? })),
    );

    query.map(|_| ()).or_else(|e| {
        use GqlError::*;
        match e {
            EndpointNotReachable(e) => {
                if backoff > 1 {
                    println!("retry: {e:?}");
                    sleep(Duration::from_secs(5));
                    push_typegraph(tg, node, backoff - 1)
                } else {
                    bail!("node unreachable: {e}")
                }
            }
            FailedQuery(e) => {
                if backoff > 1 {
                    println!("retry:\n{}", e.error_messages().dimmed());
                    sleep(Duration::from_secs(5));
                    push_typegraph(tg, node, backoff - 1)
                } else {
                    bail!("typegraph push error:\n{}", e.error_messages().dimmed())
                }
            }
            InvalidResponse(e) => {
                if backoff > 1 {
                    println!("retry:\n{}", e);
                    sleep(Duration::from_secs(5));
                    push_typegraph(tg, node, backoff - 1)
                } else {
                    bail!("Invalid HTTP response: {e}")
                }
            }
        }
    })
}
