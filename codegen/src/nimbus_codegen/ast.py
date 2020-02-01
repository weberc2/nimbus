from typing import List, NamedTuple, Optional, Tuple, Union

from typing_extensions import Protocol

KEYWORDS = ("None",)


class _Type(Protocol):
    """Workaround for mypy's lack of support for recursive types."""

    def serialize_type(self) -> str:
        ...

    def modules(self) -> List[str]:
        ...


class Type(NamedTuple):
    name: str
    type_arguments: List["_Type"]
    module: Optional[str] = None

    @staticmethod
    def new(
        name: str,
        module: Optional[str] = None,
        type_arguments: Optional[List[_Type]] = None,
    ) -> "Type":
        return Type(
            name=name,
            module=module,
            type_arguments=[] if type_arguments is None else type_arguments,
        )

    @staticmethod
    def dict_type_ref(key_type: "Type", value_type: "Type") -> "Type":
        return Type(name="Dict", type_arguments=[key_type, value_type], module="typing")

    @staticmethod
    def list_type_ref(item_type: "Type") -> "Type":
        return Type(name="List", type_arguments=[item_type], module="typing")

    def serialize_type(self) -> str:
        base = f"{self.name}"
        if len(self.type_arguments) > 0:
            base += (
                f"[{','.join([arg.serialize_type() for arg in self.type_arguments])}]"
            )
        if self.module is not None:
            return f"{self.module}.{base}"
        return base

    def __str__(self) -> str:
        raise Exception("ERROR")

    def modules(self) -> List[str]:
        modules = [] if self.module is None else [self.module]
        for typearg in self.type_arguments:
            modules.extend(typearg.modules())
        return modules


class TypeDef(Protocol):
    def serialize_type_def(self) -> Tuple[str, List[str]]:
        ...


class Stmt(Protocol):
    def serialize_stmt(self) -> str:
        ...


class CustomStmt(NamedTuple):
    content: str

    def serialize_stmt(self) -> str:
        return self.content


class Block(NamedTuple):
    stmts: List[Stmt]

    def serialize(self) -> str:
        if len(self.stmts) < 1:
            return "    pass"
        output = ""
        for stmt in self.stmts:
            output += "\n    " + stmt.serialize_stmt()
        return output


class Method(NamedTuple):
    name: str
    arguments: List[Tuple[str, Type]]
    return_type: Type
    body: Block
    decorators: List[str]

    @staticmethod
    def new(
        name: str,
        arguments: Optional[List[Tuple[str, Type]]] = None,
        return_type: Optional[Type] = None,
        body: Optional[Block] = None,
        decorators: Optional[List[str]] = None,
    ) -> "Method":
        return Method(
            name=name,
            arguments=[] if arguments is None else arguments,
            return_type=Type.new("None") if return_type is None else return_type,
            body=body if body is not None else Block([]),
            decorators=[] if decorators is None else decorators,
        )

    def serialize_method(self) -> str:
        formatted_arguments = ", ".join(
            ["self"]
            + [
                f"{arg_name}: {arg_type.serialize_type()}"
                for arg_name, arg_type in self.arguments
            ]
        )
        output = ""
        for decorator in self.decorators:
            output += f"@{decorator}\n"
        output += f"def {self.name}({formatted_arguments}) -> {self.return_type.serialize_type()}:"
        return output + self.body.serialize().replace("\n", "\n    ")

    def modules(self) -> List[str]:
        # TODO: this doesn't account for modules depended upon by the body
        modules = self.return_type.modules()
        if self.arguments is not None:
            for _, argtype in self.arguments:
                modules.extend(argtype.modules())
        return modules


class ClassDef(NamedTuple):
    name: str
    module: Optional[str]
    required_properties: List[Tuple[str, Type]]
    optional_properties: List[Tuple[str, Type]]
    methods: List[Method]

    def serialize_type_def(self) -> Tuple[str, List[str]]:
        imports = ["typing"]
        output = f"class {self.name}(typing.NamedTuple):"
        for property_name, property_type in self.required_properties:
            property_name = (
                property_name if property_name not in KEYWORDS else f"{property_name}_"
            )
            output += f"\n    {property_name}: '{property_type.serialize_type()}'"
            imports.extend(property_type.modules())
        for property_name, property_type in self.optional_properties:
            property_name = (
                property_name if property_name not in KEYWORDS else f"{property_name}_"
            )
            output += f"\n    {property_name}: typing.Optional['{property_type.serialize_type()}'] = None"
            imports.extend(property_type.modules())
        for method in self.methods:
            output += "\n    " + method.serialize_method().replace("\n", "\n    ")
            imports.extend(method.modules())
        return output, imports


class NewTypeDef(NamedTuple):
    name: str
    parent_type: Type
    module: Optional[str] = None

    def serialize_type_def(self) -> Tuple[str, List[str]]:
        return (
            f"{self.name} = typing.NewType('"
            f"{self.name}', {self.parent_type.serialize_type()})",
            ["typing"]
            if self.parent_type.module is None
            else ["typing", self.parent_type.module],
        )


class Expr(Protocol):
    def serialize_expr(self) -> str:
        ...

    # def serialize_stmt(self) -> str:
    #     return self.serialize_expr()


class CallExpr(NamedTuple):
    fn: Expr
    args: List[Expr]

    def serialize_expr(self) -> str:
        return "{}({})".format(
            ", ".join([arg.serialize_expr() for arg in self.args]),
            self.fn.serialize_expr(),
        )


class ReturnStmt(NamedTuple):
    value: Expr

    def serialize_stmt(self) -> str:
        return f"return {self.value.serialize_expr()}"


class DictLiteral(NamedTuple):
    entries: List[Tuple[Expr, Expr]]

    def serialize_expr(self) -> str:
        return (
            "{"
            + ", ".join(
                [
                    f"{keyexpr.serialize_expr()}: {valexpr.serialize_expr()}"
                    for keyexpr, valexpr in self.entries
                ]
            )
            + "}"
        )


class Attr(NamedTuple):
    parent: Expr
    label: str

    def serialize_expr(self) -> str:
        return f"{self.parent.serialize_expr()}.{self.label}"


class Variable(NamedTuple):
    label: Union[str, Attr]

    def serialize_expr(self) -> str:
        if isinstance(self.label, str):
            return self.label
        return self.label.serialize_expr()


class DeclareAssignStmt(NamedTuple):
    label: str
    type_: Type
    value: Expr

    def serialize_stmt(self) -> str:
        return f"{self.label}: {self.type_.serialize_type()} = {self.value.serialize_expr()}"


class StringLiteral(NamedTuple):
    s: str
    quote: str = '"'

    def serialize_expr(self) -> str:
        return self.quote + self.s + self.quote


class DictKeyAccess(NamedTuple):
    dict_: Expr
    key: Expr

    def serialize_expr(self) -> str:
        return f"{self.dict_.serialize_expr()}[{self.key.serialize_expr()}]"


class AssignStmt(NamedTuple):
    left: Union[Variable, DictKeyAccess]
    right: Expr

    def serialize_stmt(self) -> str:
        return f"{self.left.serialize_expr()} = {self.right.serialize_expr()}"


class CustomExpr(NamedTuple):
    contents: str

    def serialize_expr(self) -> str:
        return self.contents


class IsNotExpr(NamedTuple):
    left: Expr
    right: Expr

    def serialize_expr(self) -> str:
        return f"{self.left.serialize_expr()} is not {self.right.serialize_expr()}"


class NoneLiteral(NamedTuple):
    def serialize_expr(self) -> str:
        return "None"


class IfStmt(NamedTuple):
    condition: Expr
    body: Block

    def serialize_stmt(self) -> str:
        return f"if {self.condition.serialize_expr()}:" + self.body.serialize().replace(
            "\n", "\n    "
        )


class ElifStmt(NamedTuple):
    if_stmt: IfStmt
    elif_condition: Expr
    elif_body: Block

    def serialize_stmt(self) -> str:
        return (
            f"{self.if_stmt.serialize_stmt()}\n"
            + f"elif {self.elif_condition.serialize_expr}:"
            + self.elif_body.serialize().replace("\n", "\n    ")
        )


class ElseStmt(NamedTuple):
    previous: Union[IfStmt, ElifStmt]
    else_body: Block

    def serialize_stmt(self) -> str:
        return f"{self.previous.serialize_stmt()}\nelse:" + self.else_body.serialize().replace(
            "\n", "\n    "
        )

