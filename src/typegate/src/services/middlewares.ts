// Copyright Metatype OÜ, licensed under the Mozilla Public License Version 2.0.
// SPDX-License-Identifier: MPL-2.0

import { globalConfig } from "../config.ts";
import type { QueryEngine } from "../engine/query_engine.ts";
import { getLogger } from "../log.ts";

const logger = getLogger(import.meta);

export function baseUrl(request: Request): string {
  const { headers, url } = request;

  const forwarded_scheme = headers.get("x-forwarded-scheme");
  const forwarded_host = headers.get("x-forwarded-host");

  return (forwarded_scheme && forwarded_host)
    ? `${forwarded_scheme}://${forwarded_host}`
    : new URL(url).origin;
}

export function resolveIdentifier(
  request: Request,
  engine: QueryEngine,
  context: Record<string, unknown>,
  connInfo: Deno.NetAddr,
): string {
  if (engine.tg.tg.meta.rate?.context_identifier) {
    const contextId = context[engine.tg.tg.meta.rate?.context_identifier] as
      | string
      | undefined;
    if (contextId) {
      if (typeof contextId === "string") {
        return contextId;
      }
      logger.warn(
        `invalid context identifier type at ${engine.tg.tg.meta.rate?.context_identifier}, only string is supported, got: ${contextId}`,
      );
    }
  }

  if (globalConfig.trust_proxy) {
    const headerIp = request.headers.get(globalConfig.trust_header_ip);
    if (headerIp) {
      return headerIp;
    }
  }

  return connInfo.hostname;
}

export function addHeaders(
  res: Response,
  headers: Record<string, string>,
): Response {
  for (const [k, v] of Object.entries(headers)) {
    res.headers.set(k, v);
  }
  return res;
}
