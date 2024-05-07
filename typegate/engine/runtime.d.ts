// Copyright Metatype OÜ, licensed under the Elastic License 2.0.
// SPDX-License-Identifier: Elastic-2.0

declare global {
  const Meta: MetaNS;
}

type MetaNS = {
  version: () => string;
  typescriptFormatCode: (source: string) => string;
  typegraphValidate: (json: string) => string;
  validatePrismaRuntimeData: (obj: any) => void;
  wasmtimeWit: (inp: WasmInput) => string;

  prisma: {
    registerEngine: (
      inp: PrismaRegisterEngineInp,
    ) => Promise<void>;
    unregisterEngine: (engine_name: string) => Promise<void>;
    query: (inp: PrismaQueryInp) => Promise<string>;
    diff: (
      inp: PrismaDiffInp,
    ) => Promise<[string, ParsedDiff[]] | undefined | null>;
    apply: (inp: PrismaDevInp) => Promise<PrismaApplyOut>;
    deploy: (inp: PrismaDeployInp) => Promise<PrismaDeployOut>;
    create: (inp: PrismaCreateInp) => Promise<PrismaCreateOut>;
    reset: (datasource: string) => Promise<boolean>;
    unpack: (inp: UnpackInp) => void;
    archive: (path: string) => string | undefined | null;
  };

  temporal: {
    clientRegister: (inp: TemporalRegisterInput) => Promise<void>;
    clientUnregister: (client_id: string) => void;
    workflowStart: (
      inp: TemporalWorkflowStartInput,
    ) => Promise<string>;
    workflowSignal: (
      inp: TemporalWorkflowSignalInput,
    ) => Promise<void>;
    workflowQuery: (
      inp: TemporalWorkflowQueryInput,
    ) => Promise<Array<string>>;
    workflowDescribe: (
      inp: TemporalWorkflowDescribeInput,
    ) => Promise<TemporalWorkflowDescribeOutput>;
  };

  deno: {
    transformTypescript: (inp: string) => string;
  };

  wit_wire: {
    init: (
      componentPath: string,
      instanceId: string,
      args: WitWireInitArgs,
    ) => Promise<WitWireInitResponse>;
    destroy: (
      instanceId: string,
    ) => Promise<void>;
    handle: (
      instanceId: string,
      args: WitWireReq,
    ) => Promise<WitWireHandleResponse>;
  };
};

interface WasmInput {
  func: string;
  wasm: string;
  args: Array<string>;
}
interface PrismaRegisterEngineInp {
  datamodel: string;
  engine_name: string;
}
interface PrismaQueryInp {
  engine_name: string;
  // deno-lint-ignore no-explicit-any
  query: any;
  datamodel: string;
}
interface PrismaDiffInp {
  datasource: string;
  datamodel: string;
  script: boolean;
}
interface PrismaDevInp {
  datasource: string;
  datamodel: string;
  migrations: string | undefined | null;
  reset_database: boolean;
}
type PrismaApplyOut =
  | {
    ResetRequired: {
      reset_reason: string;
    };
  }
  | {
    Ok: {
      applied_migrations: Array<string>;
      reset_reason: string | undefined | null;
    };
  };
interface PrismaDeployOut {
  migration_count: number;
  applied_migrations: Array<string>;
}
interface PrismaCreateInp {
  datasource: string;
  datamodel: string;
  migrations: string | undefined | null;
  migration_name: string;
  apply: boolean;
}
interface PrismaCreateOut {
  created_migration_name: string | undefined | null;
  migrations: string | undefined | null;
  apply_err: string | undefined | null;
}
interface PrismaDeployInp {
  datasource: string;
  datamodel: string;
  migrations: string;
}
interface UnpackInp {
  dest: string;
  migrations: string;
}
interface TemporalRegisterInput {
  url: string;
  namespace: string;
  client_id: string;
}
interface TemporalWorkflowStartInput {
  client_id: string;
  workflow_id: string;
  workflow_type: string;
  task_queue: string;
  request_id: string | undefined | null;
  args: Array<string>;
}
interface TemporalWorkflowSignalInput {
  client_id: string;
  workflow_id: string;
  run_id: string;
  signal_name: string;
  request_id: string | undefined | null;
  args: string | undefined | null;
}
interface TemporalWorkflowQueryInput {
  client_id: string;
  workflow_id: string;
  run_id: string;
  query_type: string;
  args: string | undefined | null;
}
interface TemporalWorkflowDescribeInput {
  client_id: string;
  workflow_id: string;
  run_id: string;
}
interface TemporalWorkflowDescribeOutput {
  start_time: number | undefined | null;
  close_time: number | undefined | null;
  state: number | undefined | null;
}
interface TemporalWorkflowDescribeOutput {
  start_time: number | undefined | null;
  close_time: number | undefined | null;
  state: number | undefined | null;
}
interface PythonRegisterInp {
  vm: string;
  name: string;
  code: string;
}
interface PythonUnregisterInp {
  vm: string;
  name: string;
}
interface PythonApplyInp {
  vm: string;
  id: number;
  name: string;
  /**
   * stringified json array
   */
  args: string;
}
interface WasiVmInitConfig {
  vm_name: string;
  pylib_path: string;
  wasi_mod_path: string;
  preopens: Array<string>;
}
interface TableDiff {
  column: string;
  diff: {
    action: "Added" | "Removed" | "Altered";
    type_diff: "NullableToRequired" | "RequiredToNullable" | null | undefined;
  };
}
interface ParsedDiff {
  table: string;
  diff: TableDiff[];
}

export type WitWireReq = {
  op_name: string;
  in_json: string;
};

export type WitWireHandleError =
  | {
    InstanceNotFound: string;
  }
  | {
    ModuleErr: string;
  }
  | {
    MatErr: string;
  };

export type WitWireMatInfo = {
  op_name: string;
  mat_title: string;
  mat_hash: string;
  mat_data_json: string;
};

export type WitWireInitArgs = {
  metatype_version: string;
  expected_ops: WitWireMatInfo[];
};

export type WitWireInitResponse = object;
export type WitWireInitError =
  | {
    VersionMismatch: string;
  }
  | {
    UnexpectedMat: string;
  }
  | {
    ModuleErr: string;
  }
  | {
    Other: string;
  };

export type WitWireHandleResponse =
  | {
    Ok: string;
  }
  | "NoHandler"
  | {
    InJsonErr: string;
  }
  | {
    HandlerErr: string;
  };
