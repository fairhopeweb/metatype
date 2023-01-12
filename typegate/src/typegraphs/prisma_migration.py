from typegraph.graphs.typegraph import Auth
from typegraph.graphs.typegraph import Rate
from typegraph.graphs.typegraph import TypeGraph
from typegraph.materializers.deno import FunMat
from typegraph.materializers.prisma import PrismaApplyMat
from typegraph.materializers.prisma import PrismaCreateMat
from typegraph.materializers.prisma import PrismaDeployMat
from typegraph.materializers.prisma import PrismaDiffMat
from typegraph.policies import Policy
from typegraph.types import types as t

# from typegraph.materializers.prisma import PrismaMigrateMat

with TypeGraph(
    "typegate/prisma_migration",
    auths=[Auth.basic(["admin"])],
    rate=Rate(
        window_sec=60,
        window_limit=128,
        query_limit=8,
        local_excess=5,
        context_identifier="user",
    ),
) as g:
    admin_only = Policy(
        FunMat("(_args, { context }) => context.user === 'admin'")
    ).named("admin_only")

    base = t.struct(
        {
            "typegraph": t.string(),
            "runtime": t.string().optional(),
            # base64-encoded gzipped tar migrations folder
            "migrations": t.string().optional(),
        }
    )

    g.expose(
        diff=t.func(
            t.struct(
                {
                    "typegraph": t.string(),
                    "runtime": t.string().optional(),
                    "script": t.boolean(),
                }
            ),
            t.struct(
                {
                    "diff": t.string().optional(),
                    "runtimeName": t.string(),
                }
            ),
            PrismaDiffMat(),
        )
        .rate(calls=True)
        .add_policy(admin_only),
        # apply pending migrations
        apply=t.func(
            base.compose({"resetDatabase": t.boolean()}),
            t.struct(
                {
                    "databaseReset": t.boolean(),
                    "appliedMigrations": t.array(t.string()),
                }
            ),
            PrismaApplyMat(),
        )
        .rate(calls=True)
        .add_policy(admin_only),
        # create migration
        create=t.func(
            base.compose({"name": t.string(), "apply": t.boolean()}),
            t.struct(
                {
                    "createdMigrationName": t.string(),
                    "appliedMigrations": t.array(t.string()),
                    "migrations": t.string(),
                    "runtimeName": t.string(),
                }
            ),
            PrismaCreateMat(),
        )
        .rate(calls=True)
        .add_policy(admin_only),
        # apply migrations -- prod
        deploy=t.func(
            base.compose({"migrations": t.string()}),
            t.struct(
                {
                    "migrationCount": t.integer(),
                    "appliedMigrations": t.array(t.string()),
                }
            ),
            PrismaDeployMat(),
        )
        .rate(calls=True)
        .add_policy(admin_only),
    )
