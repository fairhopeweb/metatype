# This file was @generated by metagen and is intended
# to be generated again on subsequent metagen runs.

import typing
import dataclasses as dc
import json
import urllib.request as request
import urllib.error
import http.client as http_c


def selection_to_nodes(
    selection: "SelectionErased",
    metas: typing.Dict[str, "NodeMetaFn"],
    parent_path: str,
) -> typing.List["SelectNode[typing.Any]"]:
    out = []
    flags = selection.get("_")
    if flags is not None and not isinstance(flags, SelectionFlags):
        raise Exception(
            f"selection field '_' should be of type SelectionFlags but found {type(flags)}"
        )
    select_all = True if flags is not None and flags.select_all else False
    found_nodes = set(selection.keys())
    for node_name, meta_fn in metas.items():
        found_nodes.discard(node_name)

        node_selection = selection.get(node_name)
        if node_selection is False or (node_selection is None and not select_all):
            # this node was not selected
            continue

        meta = meta_fn()

        # we splat out any aliasing of nodes here
        node_instances = (
            [(key, val) for key, val in node_selection.items.items()]
            if isinstance(node_selection, Alias)
            else [(node_name, node_selection)]
        )

        for instance_name, instance_selection in node_instances:
            # print(parent_path, instance_selection, meta.sub_nodes, instance_selection, flags)
            if instance_selection is False or (
                instance_selection is None and not select_all
            ):
                # this instance was not selected
                continue
            if isinstance(instance_selection, Alias):
                raise Exception(
                    f"nested Alias node discovered at {parent_path}.{instance_name}"
                )

            instance_args: typing.Optional[NodeArgs] = None
            if meta.arg_types is not None:
                arg = instance_selection

                if isinstance(arg, tuple):
                    arg = arg[0]

                # arg types are always TypedDicts
                if not isinstance(arg, dict):
                    raise Exception(
                        f"node at {parent_path}.{instance_name} is a node that "
                        + "requires arguments "
                        + f"but detected argument is typeof {type(arg)}"
                    )

                # convert arg dict to NodeArgs
                expected_args = {key: val for key, val in meta.arg_types.items()}
                instance_args = {}
                for key, val in arg.items():
                    ty_name = expected_args.pop(key)
                    if ty_name is None:
                        raise Exception(
                            f"unexpected argument ${key} at {parent_path}.{instance_name}"
                        )
                    instance_args[key] = NodeArgValue(ty_name, val)

            sub_nodes: SubNodes = None
            if meta.sub_nodes is not None or meta.variants is not None:
                sub_selections = instance_selection

                # if node requires both selection and arg, it must be
                # a CompositeSelectArgs which is a tuple selection
                if meta.arg_types is not None:
                    if not isinstance(sub_selections, tuple):
                        raise Exception(
                            f"node at {parent_path}.{instance_name} is a composite "
                            + "that requires an argument object "
                            + f"but selection is typeof {type(sub_selections)}"
                        )
                    sub_selections = sub_selections[1]

                # we got a tuple selection when this shouldn't be the case
                elif isinstance(sub_selections, tuple):
                    raise Exception(
                        f"node at {parent_path}.{instance_name} "
                        + "is a composite that takes no arguments "
                        + f"but selection is typeof {type(instance_selection)}",
                    )

                # flags are recursive for any subnode that's not specified
                if sub_selections is None:
                    sub_selections = {"_": flags}

                # selection types are always TypedDicts as well
                if not isinstance(sub_selections, dict):
                    raise Exception(
                        f"node at {parent_path}.{instance_name} "
                        + "is a no argument composite but first element of "
                        + f"selection is typeof {type(instance_selection)}",
                    )

                if meta.sub_nodes is not None:
                    if meta.variants is not None:
                        raise Exception(
                            "unreachable: union/either NodeMetas can't have subnodes"
                        )
                    sub_nodes = selection_to_nodes(
                        typing.cast("SelectionErased", sub_selections),
                        meta.sub_nodes,
                        f"{parent_path}.{instance_name}",
                    )
                else:
                    assert meta.variants is not None
                    union_selections: typing.Dict[str, typing.List[SelectNode]] = {}
                    for variant_ty, variant_meta in meta.variants.items():
                        variant_meta = variant_meta()

                        # this union member is a scalar
                        if variant_meta.sub_nodes is None:
                            continue

                        variant_select = sub_selections.pop(variant_ty, None)
                        nodes = (
                            selection_to_nodes(
                                typing.cast("SelectionErased", variant_select),
                                variant_meta.sub_nodes,
                                f"{parent_path}.{instance_name}.variant({variant_ty})",
                            )
                            if variant_select is not None
                            else []
                        )

                        # we select __typename for each variant
                        # even if the user is not interested in the variant
                        nodes.append(
                            SelectNode(
                                node_name="__typename",
                                instance_name="__typename",
                                args=None,
                                sub_nodes=None,
                            )
                        )

                        union_selections[variant_ty] = nodes

                    if len(sub_selections) > 0:
                        raise Exception(
                            f"node at {parent_path}.{instance_name} "
                            + "has none of the variants called "
                            + str(sub_selections.keys()),
                        )
                    sub_nodes = union_selections

            node = SelectNode(node_name, instance_name, instance_args, sub_nodes)
            out.append(node)

    found_nodes.discard("_")
    if len(found_nodes) > 0:
        raise Exception(
            f"unexpected nodes found in selection set at {parent_path}: {found_nodes}",
        )
    return out


#
# --- --- Util types --- --- #
#

Out = typing.TypeVar("Out", covariant=True)

T = typing.TypeVar("T")

ArgT = typing.TypeVar("ArgT", bound=typing.Mapping[str, typing.Any])
SelectionT = typing.TypeVar("SelectionT")


#
# --- --- Graph node types --- --- #
#


SubNodes = typing.Union[
    None,
    # atomic composite
    typing.List["SelectNode"],
    # union/either selection
    typing.Dict[str, typing.List["SelectNode"]],
]


@dc.dataclass
class SelectNode(typing.Generic[Out]):
    node_name: str
    instance_name: str
    args: typing.Optional["NodeArgs"]
    sub_nodes: SubNodes


@dc.dataclass
class QueryNode(SelectNode[Out]):
    pass


@dc.dataclass
class MutationNode(SelectNode[Out]):
    pass


NodeMetaFn = typing.Callable[[], "NodeMeta"]


@dc.dataclass
class NodeMeta:
    sub_nodes: typing.Optional[typing.Dict[str, NodeMetaFn]] = None
    variants: typing.Optional[typing.Dict[str, NodeMetaFn]] = None
    arg_types: typing.Optional[typing.Dict[str, str]] = None


#
# --- --- Argument types --- --- #
#


@dc.dataclass
class NodeArgValue:
    type_name: str
    value: typing.Any


NodeArgs = typing.Dict[str, NodeArgValue]


class PlaceholderValue(typing.Generic[T]):
    def __init__(self, key: str):
        self.key = key


PlaceholderArgs = typing.Dict[str, PlaceholderValue]


class PreparedArgs:
    def get(self, key: str) -> PlaceholderValue:
        return PlaceholderValue(key)


#
# --- --- Selection types --- --- #
#


class Alias(typing.Generic[SelectionT]):
    """
    Request multiple instances of a single node under different
    aliases.
    """

    def __init__(self, **aliases: SelectionT):
        self.items = aliases


ScalarSelectNoArgs = typing.Union[bool, Alias[typing.Literal[True]], None]
ScalarSelectArgs = typing.Union[
    ArgT,
    PlaceholderArgs,
    Alias[typing.Union[ArgT, PlaceholderArgs]],
    typing.Literal[False],
    None,
]
CompositeSelectNoArgs = typing.Union[
    SelectionT, Alias[SelectionT], typing.Literal[False], None
]
CompositeSelectArgs = typing.Union[
    typing.Tuple[typing.Union[ArgT, PlaceholderArgs], SelectionT],
    Alias[typing.Tuple[typing.Union[ArgT, PlaceholderArgs], SelectionT]],
    typing.Literal[False],
    None,
]


# FIXME: ideally this would be a TypedDict
# to allow full dict based queries but
# we need to reliably identify SelectionFlags at runtime
# but TypedDicts don't allow instanceof
@dc.dataclass
class SelectionFlags:
    select_all: typing.Union[bool, None] = None


class Selection(typing.TypedDict, total=False):
    _: SelectionFlags


SelectionErased = typing.Mapping[
    str,
    typing.Union[
        SelectionFlags,
        ScalarSelectNoArgs,
        ScalarSelectArgs[typing.Mapping[str, typing.Any]],
        CompositeSelectNoArgs["SelectionErased"],
        # FIXME: should be possible to make SelectionT here `SelectionErased` recursively
        # but something breaks
        CompositeSelectArgs[typing.Mapping[str, typing.Any], typing.Any],
    ],
]

#
# --- --- GraphQL types --- --- #
#


@dc.dataclass
class GraphQLTransportOptions:
    headers: typing.Dict[str, str]


@dc.dataclass
class GraphQLRequest:
    addr: str
    method: str
    headers: typing.Dict[str, str]
    body: bytes


@dc.dataclass
class GraphQLResponse:
    req: GraphQLRequest
    status: int
    headers: typing.Dict[str, str]
    body: bytes


def convert_query_node_gql(
    ty_to_gql_ty_map: typing.Dict[str, str],
    node: SelectNode,
    variables: typing.Dict[str, NodeArgValue],
):
    out = (
        f"{node.instance_name}: {node.node_name}"
        if node.instance_name != node.node_name
        else node.node_name
    )
    if node.args is not None:
        arg_row = ""
        for key, val in node.args.items():
            name = f"in{len(variables)}"
            variables[name] = val
            arg_row += f"{key}: ${name}, "
        if len(arg_row):
            out += f"({arg_row[:-2]})"

    # if it's a dict, it'll be a union selection
    if isinstance(node.sub_nodes, dict):
        sub_node_list = ""
        for variant_ty, sub_nodes in node.sub_nodes.items():
            # fetch the gql variant name so we can do
            # type assertions
            gql_ty = ty_to_gql_ty_map[variant_ty]
            if gql_ty is None:
                raise Exception(
                    f"unreachable: no graphql type found for variant {variant_ty}"
                )
            gql_ty = gql_ty.strip("!")

            sub_node_list += f"... on {gql_ty} {{ "
            for node in sub_nodes:
                sub_node_list += (
                    f"{convert_query_node_gql(ty_to_gql_ty_map, node, variables)} "
                )
            sub_node_list += "}"
        out += f" {{ {sub_node_list}}}"
    elif isinstance(node.sub_nodes, list):
        sub_node_list = ""
        for node in node.sub_nodes:
            sub_node_list += (
                f"{convert_query_node_gql(ty_to_gql_ty_map, node, variables)} "
            )
        out += f" {{ {sub_node_list}}}"
    return out


class GraphQLTransportBase:
    def __init__(
        self,
        addr: str,
        opts: GraphQLTransportOptions,
        ty_to_gql_ty_map: typing.Dict[str, str],
    ):
        self.addr = addr
        self.opts = opts
        self.ty_to_gql_ty_map = ty_to_gql_ty_map

    def build_gql(
        self,
        query: typing.Mapping[str, SelectNode],
        ty: typing.Union[typing.Literal["query"], typing.Literal["mutation"]],
        name: str = "",
    ):
        variables: typing.Dict[str, NodeArgValue] = {}
        root_nodes = ""
        for key, node in query.items():
            fixed_node = SelectNode(node.node_name, key, node.args, node.sub_nodes)
            root_nodes += f"  {convert_query_node_gql(self.ty_to_gql_ty_map, fixed_node, variables)}\n"
        args_row = ""
        for key, val in variables.items():
            args_row += f"${key}: {self.ty_to_gql_ty_map[val.type_name]}, "

        if len(args_row):
            args_row = f"({args_row[:-2]})"

        doc = f"{ty} {name}{args_row} {{\n{root_nodes}}}"
        variables = {key: val.value for key, val in variables.items()}
        # print(doc, variables)
        return (doc, variables)

    def build_req(
        self,
        doc: str,
        variables: typing.Dict[str, typing.Any],
        opts: typing.Optional[GraphQLTransportOptions] = None,
    ):
        headers = {}
        headers.update(self.opts.headers)
        if opts:
            headers.update(opts.headers)
        headers.update(
            {
                "accept": "application/json",
                "content-type": "application/json",
            }
        )
        data = json.dumps({"query": doc, "variables": variables}).encode("utf-8")
        return GraphQLRequest(
            addr=self.addr,
            method="POST",
            headers=headers,
            body=data,
        )

    def handle_response(self, res: GraphQLResponse):
        if res.status != 200:
            raise Exception(f"graphql request failed with status {res.status}", res)
        if res.headers.get("content-type") != "application/json":
            raise Exception("unexpected content-type in graphql response", res)
        parsed = json.loads(res.body)
        if parsed.get("errors"):
            raise Exception("graphql errors in response", parsed)
        return parsed["data"]


class GraphQLTransportUrlib(GraphQLTransportBase):
    def fetch(
        self,
        doc: str,
        variables: typing.Dict[str, typing.Any],
        opts: typing.Optional[GraphQLTransportOptions],
    ):
        req = self.build_req(doc, variables, opts)
        try:
            with request.urlopen(
                request.Request(
                    url=req.addr, method=req.method, headers=req.headers, data=req.body
                )
            ) as res:
                http_res: http_c.HTTPResponse = res
                return self.handle_response(
                    GraphQLResponse(
                        req,
                        status=http_res.status,
                        body=http_res.read(),
                        headers={key: val for key, val in http_res.headers.items()},
                    )
                )
        except request.HTTPError as res:
            return self.handle_response(
                GraphQLResponse(
                    req,
                    status=res.status or 599,
                    body=res.read(),
                    headers={key: val for key, val in res.headers.items()},
                )
            )
        except urllib.error.URLError as err:
            raise Exception(f"URL error: {err.reason}")

    def query(
        self,
        inp: typing.Dict[str, QueryNode[Out]],
        opts: typing.Optional[GraphQLTransportOptions] = None,
        name: str = "",
    ) -> typing.Dict[str, Out]:
        doc, variables = self.build_gql(
            {key: val for key, val in inp.items()}, "query", name
        )
        return self.fetch(doc, variables, opts)

    def mutation(
        self,
        inp: typing.Dict[str, MutationNode[Out]],
        opts: typing.Optional[GraphQLTransportOptions] = None,
        name: str = "",
    ) -> typing.Dict[str, Out]:
        doc, variables = self.build_gql(
            {key: val for key, val in inp.items()}, "mutation", name
        )
        return self.fetch(doc, variables, opts)

    def prepare_query(
        self,
        fun: typing.Callable[[PreparedArgs], typing.Dict[str, QueryNode[Out]]],
        name: str = "",
    ) -> "PreparedRequestUrlib[Out]":
        return PreparedRequestUrlib(self, fun, "query", name)

    def prepare_mutation(
        self,
        fun: typing.Callable[[PreparedArgs], typing.Dict[str, MutationNode[Out]]],
        name: str = "",
    ) -> "PreparedRequestUrlib[Out]":
        return PreparedRequestUrlib(self, fun, "mutation", name)


class PreparedRequestBase(typing.Generic[Out]):
    def __init__(
        self,
        transport: GraphQLTransportBase,
        fun: typing.Callable[[PreparedArgs], typing.Mapping[str, SelectNode[Out]]],
        ty: typing.Union[typing.Literal["query"], typing.Literal["mutation"]],
        name: str = "",
    ):
        dry_run_node = fun(PreparedArgs())
        doc, variables = transport.build_gql(dry_run_node, ty, name)
        self.doc = doc
        self._mapping = variables
        self.transport = transport

    def resolve_vars(
        self,
        args: typing.Mapping[str, typing.Any],
        mappings: typing.Dict[str, typing.Any],
    ):
        resolved: typing.Dict[str, typing.Any] = {}
        for key, val in mappings.items():
            if isinstance(val, PlaceholderValue):
                resolved[key] = args[val.key]
            elif isinstance(val, dict):
                self.resolve_vars(args, val)
            else:
                resolved[key] = val
        return resolved


class PreparedRequestUrlib(PreparedRequestBase[Out]):
    def __init__(
        self,
        transport: GraphQLTransportUrlib,
        fun: typing.Callable[[PreparedArgs], typing.Mapping[str, SelectNode[Out]]],
        ty: typing.Union[typing.Literal["query"], typing.Literal["mutation"]],
        name: str = "",
    ):
        super().__init__(transport, fun, ty, name)
        self.transport = transport

    def perform(
        self,
        args: typing.Mapping[str, typing.Any],
        opts: typing.Optional[GraphQLTransportOptions] = None,
    ) -> typing.Dict[str, Out]:
        resolved_vars = self.resolve_vars(args, self._mapping)
        return self.transport.fetch(self.doc, resolved_vars, opts)


#
# --- --- QueryGraph types --- --- #
#


class QueryGraphBase:
    def __init__(self, ty_to_gql_ty_map: typing.Dict[str, str]):
        self.ty_to_gql_ty_map = ty_to_gql_ty_map

    def graphql_sync(
        self, addr: str, opts: typing.Optional[GraphQLTransportOptions] = None
    ):
        return GraphQLTransportUrlib(
            addr, opts or GraphQLTransportOptions({}), self.ty_to_gql_ty_map
        )


#
# --- --- Typegraph types --- --- #
#


class NodeDescs:
    @staticmethod
    def scalar():
        return NodeMeta()

    @staticmethod
    def Post():
        return NodeMeta(
            sub_nodes={
                "id": NodeDescs.scalar,
                "slug": NodeDescs.scalar,
                "title": NodeDescs.scalar,
            },
        )

    @staticmethod
    def RootCompositeArgsFn():
        return_node = NodeDescs.Post()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
            arg_types={
                "id": "RootScalarArgsFnOutput",
            },
        )

    @staticmethod
    def RootGetPostsFn():
        return_node = NodeDescs.Post()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
        )

    @staticmethod
    def RootScalarArgsFn():
        return_node = NodeDescs.scalar()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
            arg_types={
                "id": "UserIdStringUuid",
                "slug": "PostSlugString",
                "title": "PostSlugString",
            },
        )

    @staticmethod
    def RootScalarUnionFn():
        return_node = NodeDescs.scalar()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
            arg_types={
                "id": "RootScalarArgsFnOutput",
            },
        )

    @staticmethod
    def User():
        return NodeMeta(
            sub_nodes={
                "id": NodeDescs.scalar,
                "email": NodeDescs.scalar,
                "posts": NodeDescs.Post,
            },
        )

    @staticmethod
    def RootCompositeUnionFnOutput():
        return NodeMeta(
            variants={
                "post": NodeDescs.Post,
                "user": NodeDescs.User,
            },
        )

    @staticmethod
    def RootCompositeUnionFn():
        return_node = NodeDescs.RootCompositeUnionFnOutput()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
            arg_types={
                "id": "RootScalarArgsFnOutput",
            },
        )

    @staticmethod
    def RootCompositeNoArgsFn():
        return_node = NodeDescs.Post()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
        )

    @staticmethod
    def RootScalarNoArgsFn():
        return_node = NodeDescs.scalar()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
        )

    @staticmethod
    def RootMixedUnionFnOutput():
        return NodeMeta(
            variants={
                "post": NodeDescs.Post,
                "user": NodeDescs.User,
            },
        )

    @staticmethod
    def RootMixedUnionFn():
        return_node = NodeDescs.RootMixedUnionFnOutput()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
            arg_types={
                "id": "RootScalarArgsFnOutput",
            },
        )

    @staticmethod
    def RootGetUserFn():
        return_node = NodeDescs.User()
        return NodeMeta(
            sub_nodes=return_node.sub_nodes,
            variants=return_node.variants,
        )


UserIdStringUuid = str

PostSlugString = str

Post = typing.TypedDict(
    "Post",
    {
        "id": UserIdStringUuid,
        "slug": PostSlugString,
        "title": PostSlugString,
    },
    total=False,
)

RootScalarArgsFnOutput = str

RootCompositeArgsFnInput = typing.TypedDict(
    "RootCompositeArgsFnInput",
    {
        "id": RootScalarArgsFnOutput,
    },
    total=False,
)

UserEmailStringEmail = str

UserPostsPostList = typing.List[Post]

User = typing.TypedDict(
    "User",
    {
        "id": UserIdStringUuid,
        "email": UserEmailStringEmail,
        "posts": UserPostsPostList,
    },
    total=False,
)

RootCompositeUnionFnOutput = typing.Union[
    Post,
    User,
]


RootScalarUnionFnOutputT1Integer = int

RootMixedUnionFnOutput = typing.Union[
    Post,
    User,
    RootScalarArgsFnOutput,
    RootScalarUnionFnOutputT1Integer,
]


RootScalarUnionFnOutput = typing.Union[
    RootScalarArgsFnOutput,
    RootScalarUnionFnOutputT1Integer,
]


PostSelections = typing.TypedDict(
    "PostSelections",
    {
        "_": SelectionFlags,
        "id": ScalarSelectNoArgs,
        "slug": ScalarSelectNoArgs,
        "title": ScalarSelectNoArgs,
    },
    total=False,
)

UserSelections = typing.TypedDict(
    "UserSelections",
    {
        "_": SelectionFlags,
        "id": ScalarSelectNoArgs,
        "email": ScalarSelectNoArgs,
        "posts": CompositeSelectNoArgs["PostSelections"],
    },
    total=False,
)

RootCompositeUnionFnOutputSelections = typing.TypedDict(
    "RootCompositeUnionFnOutputSelections",
    {
        "_": SelectionFlags,
        "post": CompositeSelectNoArgs["PostSelections"],
        "user": CompositeSelectNoArgs["UserSelections"],
    },
    total=False,
)

RootMixedUnionFnOutputSelections = typing.TypedDict(
    "RootMixedUnionFnOutputSelections",
    {
        "_": SelectionFlags,
        "post": CompositeSelectNoArgs["PostSelections"],
        "user": CompositeSelectNoArgs["UserSelections"],
    },
    total=False,
)


class QueryGraph(QueryGraphBase):
    def __init__(self):
        super().__init__(
            {
                "UserIdStringUuid": "String!",
                "PostSlugString": "String!",
                "RootScalarArgsFnOutput": "String!",
                "post": "post!",
                "user": "user!",
            }
        )

    def get_user(self, select: UserSelections) -> QueryNode[User]:
        node = selection_to_nodes(
            {"getUser": select}, {"getUser": NodeDescs.RootGetUserFn}, "$q"
        )[0]
        return QueryNode(node.node_name, node.instance_name, node.args, node.sub_nodes)

    def get_posts(self, select: PostSelections) -> QueryNode[Post]:
        node = selection_to_nodes(
            {"getPosts": select}, {"getPosts": NodeDescs.RootGetPostsFn}, "$q"
        )[0]
        return QueryNode(node.node_name, node.instance_name, node.args, node.sub_nodes)

    def scalar_no_args(self) -> QueryNode[PostSlugString]:
        node = selection_to_nodes(
            {"scalarNoArgs": True}, {"scalarNoArgs": NodeDescs.RootScalarNoArgsFn}, "$q"
        )[0]
        return QueryNode(node.node_name, node.instance_name, node.args, node.sub_nodes)

    def scalar_args(
        self, args: typing.Union[Post, PlaceholderArgs]
    ) -> MutationNode[RootScalarArgsFnOutput]:
        node = selection_to_nodes(
            {"scalarArgs": args}, {"scalarArgs": NodeDescs.RootScalarArgsFn}, "$q"
        )[0]
        return MutationNode(
            node.node_name, node.instance_name, node.args, node.sub_nodes
        )

    def composite_no_args(self, select: PostSelections) -> MutationNode[Post]:
        node = selection_to_nodes(
            {"compositeNoArgs": select},
            {"compositeNoArgs": NodeDescs.RootCompositeNoArgsFn},
            "$q",
        )[0]
        return MutationNode(
            node.node_name, node.instance_name, node.args, node.sub_nodes
        )

    def composite_args(
        self,
        args: typing.Union[RootCompositeArgsFnInput, PlaceholderArgs],
        select: PostSelections,
    ) -> MutationNode[Post]:
        node = selection_to_nodes(
            {"compositeArgs": (args, select)},
            {"compositeArgs": NodeDescs.RootCompositeArgsFn},
            "$q",
        )[0]
        return MutationNode(
            node.node_name, node.instance_name, node.args, node.sub_nodes
        )

    def scalar_union(
        self, args: typing.Union[RootCompositeArgsFnInput, PlaceholderArgs]
    ) -> QueryNode[RootScalarUnionFnOutput]:
        node = selection_to_nodes(
            {"scalarUnion": args}, {"scalarUnion": NodeDescs.RootScalarUnionFn}, "$q"
        )[0]
        return QueryNode(node.node_name, node.instance_name, node.args, node.sub_nodes)

    def composite_union(
        self,
        args: typing.Union[RootCompositeArgsFnInput, PlaceholderArgs],
        select: RootCompositeUnionFnOutputSelections,
    ) -> QueryNode[RootCompositeUnionFnOutput]:
        node = selection_to_nodes(
            {"compositeUnion": (args, select)},
            {"compositeUnion": NodeDescs.RootCompositeUnionFn},
            "$q",
        )[0]
        return QueryNode(node.node_name, node.instance_name, node.args, node.sub_nodes)

    def mixed_union(
        self,
        args: typing.Union[RootCompositeArgsFnInput, PlaceholderArgs],
        select: RootMixedUnionFnOutputSelections,
    ) -> QueryNode[RootMixedUnionFnOutput]:
        node = selection_to_nodes(
            {"mixedUnion": (args, select)},
            {"mixedUnion": NodeDescs.RootMixedUnionFn},
            "$q",
        )[0]
        return QueryNode(node.node_name, node.instance_name, node.args, node.sub_nodes)
