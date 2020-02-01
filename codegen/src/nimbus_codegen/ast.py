from typing import List, NamedTuple, Optional, Tuple

from typing_extensions import Protocol

KEYWORDS = ("None",)


class _Type(Protocol):
    """Workaround for mypy's lack of support for recursive types."""

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        base = f"{self.name}"
        if len(self.type_arguments) > 0:
            base += f"[{','.join([str(arg) for arg in self.type_arguments])}]"
        if self.module is not None:
            return f"{self.module}.{base}"
        return base

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


class Method(NamedTuple):
    name: str
    arguments: List[Tuple[str, Type]]
    return_type: Type
    body: List[Stmt]
    decorators: List[str]

    @staticmethod
    def new(
        name: str,
        arguments: Optional[List[Tuple[str, Type]]] = None,
        return_type: Optional[Type] = None,
        body: Optional[List[Stmt]] = None,
        decorators: Optional[List[str]] = None,
    ) -> "Method":
        return Method(
            name=name,
            arguments=[] if arguments is None else arguments,
            return_type=Type.new("None") if return_type is None else return_type,
            body=[CustomStmt("pass")] if body is None else body,
            decorators=[] if decorators is None else decorators,
        )

    def serialize_method(self) -> str:
        formatted_arguments = ", ".join(
            ["self"]
            + [f"{arg_name}: {arg_type}" for arg_name, arg_type in self.arguments]
        )
        output = ""
        for decorator in self.decorators:
            output += f"@{decorator}\n"
        output += f"def {self.name}({formatted_arguments}) -> {self.return_type}:"
        for stmt in self.body:
            output += "\n    " + stmt.serialize_stmt().replace("\n", "\n    ")
        return output

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
            output += f"\n    {property_name}: '{property_type}'"
            imports.extend(property_type.modules())
        for property_name, property_type in self.optional_properties:
            property_name = (
                property_name if property_name not in KEYWORDS else f"{property_name}_"
            )
            output += (
                f"\n    {property_name}: typing.Optional['{property_type}'] = None"
            )
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
            f"{self.name} = typing.NewType('" f"{self.name}', {self.parent_type})",
            ["typing"]
            if self.parent_type.module is None
            else ["typing", self.parent_type.module],
        )
