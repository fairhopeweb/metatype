// Copyright Metatype OÜ, licensed under the Elastic License 2.0.
// SPDX-License-Identifier: Elastic-2.0

import { testDir } from "test-utils/dir.ts";
import { gql, Meta } from "../utils/mod.ts";
import * as path from "std/path/mod.ts";

const cwd = path.join(testDir, "type_nodes");

Meta.test(
  {
    name: "Union type",
    introspection: true,
    port: true,
    systemTypegraphs: true,
  },
  async (t) => {
    const e = await t.engineFromTgDeployPython(
      "type_nodes/union_node_quantifier.py",
      cwd,
    );

    await t.should("work with optionals and list arguments", async () => {
      await gql`
        query {
          registerPhone(
            phone: {
              name: "LG"
              battery: 5000
              metadatas: [
                {
                  label: "IMEI"
                  content: "1234567891011"
                  source: "Factory1234"
                }
                { label: "ref", content: "LG_1234" }
              ]
            }
          ) {
            message
            type
            phone {
              ... on BasicPhone {
                name
                metadatas {
                  label
                  content
                  source
                }
              }
              ... on SmartPhone {
                name
                metadatas {
                  label
                  content
                  source
                }
              }
            }
          }
        }
      `
        .expectData({
          registerPhone: {
            message: "LG registered",
            type: "Basic",
            phone: {
              name: "LG",
              metadatas: [
                {
                  label: "IMEI",
                  content: "1234567891011",
                  source: "Factory1234",
                },
                {
                  label: "ref",
                  content: "LG_1234",
                },
              ],
            },
          },
        })
        .on(e);
    });

    await t.should("work with optional field completed", async () => {
      await gql`
        query {
          registerPhone(
            phone: { name: "SAMSUNG", camera: 50, battery: 5000, os: "Android" }
          ) {
            message
            type
            phone {
              ... on SmartPhone {
                name
                os
              }
              ... on BasicPhone {
                name
                os
              }
            }
          }
        }
      `
        .expectData({
          registerPhone: {
            message: "SAMSUNG registered",
            type: "Smartphone",
            phone: {
              name: "SAMSUNG",
              os: "Android",
            },
          },
        })
        .on(e);
    });
  },
);
