// Copyright Metatype OÜ, licensed under the Mozilla Public License Version 2.0.
// SPDX-License-Identifier: MPL-2.0

import { gql, Meta } from "../utils/mod.ts";

Meta.test(
  {
    name: "Union type",
    introspection: true,
  },
  async (t) => {
    const e = await t.engine(
      "type_nodes/union_node_quantifier.py",
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
                  source: null,
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
