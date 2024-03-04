// const { core } = Deno[Deno.internal];
const { core } = Deno;
const { ops } = core;
// const fastops = core.ensureFastOps(); // TODO: investigate

// NOTE: use the following import if ever switching to snaphsots
// import * as ops from "ext:core/ops";

function getOp(name) {
  // Note: always get the op right away.
  // the core.ops object is a proxy
  // that retrieves the named op
  // when requested i.e. not a
  // hashmap prepopulated by the ops.
  // If we don't get the op now, the
  // proxy behvior won't be avail later at runtime
  const op = ops[name];
  if (!op) {
    throw Error(`op: ${name} not found`);
  }
  return op;
}

globalThis.Meta = {
  prisma: {
    registerEngine: getOp("op_prisma_register_engine"),
    unregisterEngine: getOp("op_prisma_unregister_engine"),
    query: getOp("op_prisma_query"),
    diff: getOp("op_prisma_diff"),
    apply: getOp("op_prisma_apply"),
    deploy: getOp("op_prisma_deploy"),
    create: getOp("op_prisma_create"),
    reset: getOp("op_prisma_reset"),
    unpack: getOp("op_unpack"),
    archive: getOp("op_archive"),
  },
  temporal: {
    clientRegister: getOp("op_temporal_register"),
    clientUnregister: getOp("op_temporal_unregister"),
    workflowStart: getOp("op_temporal_workflow_start"),
    workflowSignal: getOp("op_temporal_workflow_signal"),
    workflowQuery: getOp("op_temporal_workflow_query"),
    workflowDescribe: getOp("op_temporal_workflow_describe"),
  },
  python: {
    registerVm: getOp("op_register_virtual_machine"),
    unregisterVm: getOp("op_unregister_virtual_machine"),
    registerLambda: getOp("op_register_lambda"),
    unregisterLambda: getOp("op_unregister_lambda"),
    applyLambda: getOp("op_apply_lambda"),
    registerDef: getOp("op_register_def"),
    unregisterDef: getOp("op_unregister_def"),
    applyDef: getOp("op_apply_def"),
    registerModule: getOp("op_register_module"),
    unregisterModule: getOp("op_unregister_module"),
  },
  deno: {
    transformTypescript: getOp("op_deno_transform_typescript"),
  },
  version: getOp("op_get_version"),
  typescriptFormatCode: getOp("op_typescript_format_code"),
  typegraphValidate: getOp("op_typegraph_validate"),
  validatePrismaRuntimeData: getOp("op_validate_prisma_runtime_data"),
  wasmedgeWasi: getOp("op_wasmedge_wasi"),
};
