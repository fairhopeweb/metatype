// skip:start
import { Policy, t, typegraph } from "@typegraph/sdk";
import { HttpRuntime } from "@typegraph/sdk/runtimes/http";

// skip:end

typegraph(
  {
    name: "triggers",
    // skip:next-line
    cors: { allowOrigin: ["https://metatype.dev", "http://localhost:3000"] },
  },
  (g) => {
    // skip:start
    const pub = Policy.public();
    const http = new HttpRuntime("https://random.org/api");
    // skip:end
    // ...
    g.expose(
      {
        flip: http.get(t.struct({}), t.enum_(["head", "tail"]), {
          path: "/flip_coin",
        }),
      },
      pub,
    );
  },
);
