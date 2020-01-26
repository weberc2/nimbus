from typing import List, NamedTuple, Optional, Tuple

from typing_extensions import Protocol

KEYWORDS = "None"


class _PythonTypeReference(Protocol):
    """Workaround for mypy's lack of support for recursive types."""

    def __str__(self) -> str:
        ...

    def modules(self) -> List[str]:
        ...


class PythonTypeReference(NamedTuple):
    name: str
    type_arguments: List["_PythonTypeReference"]
    module: Optional[str] = None

    @staticmethod
    def new(
        name: str,
        module: Optional[str] = None,
        type_arguments: Optional[List[_PythonTypeReference]] = None,
    ) -> "PythonTypeReference":
        return PythonTypeReference(
            name=name,
            module=module,
            type_arguments=[] if type_arguments is None else type_arguments,
        )

    @staticmethod
    def dict_type_ref(
        key_type: "PythonTypeReference", value_type: "PythonTypeReference"
    ) -> "PythonTypeReference":
        return PythonTypeReference(
            name="Dict", type_arguments=[key_type, value_type], module="typing"
        )

    @staticmethod
    def list_type_ref(item_type: "PythonTypeReference") -> "PythonTypeReference":
        return PythonTypeReference(
            name="List", type_arguments=[item_type], module="typing"
        )

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


class PythonType(Protocol):
    def python_type_reference(self) -> PythonTypeReference:
        ...

    def serialize_python_type_definition(self, indent: str) -> Tuple[str, List[str]]:
        ...


class PythonStatement(Protocol):
    def serialize_python_statement(self, indent: str) -> str:
        ...


class PythonCustomStatement(NamedTuple):
    content: str

    def serialize_python_statement(self, indent: str) -> str:
        return indent + self.content.replace("\n", f"\n{indent}")


class PythonMethod(NamedTuple):
    name: str
    arguments: List[Tuple[str, PythonTypeReference]]
    return_type: PythonTypeReference
    body: List[PythonStatement]
    decorators: List[str]

    @staticmethod
    def new(
        name: str,
        arguments: Optional[List[Tuple[str, PythonTypeReference]]] = None,
        return_type: Optional[PythonTypeReference] = None,
        body: Optional[List[PythonStatement]] = None,
        decorators: Optional[List[str]] = None,
    ) -> "PythonMethod":
        return PythonMethod(
            name=name,
            arguments=[] if arguments is None else arguments,
            return_type=PythonTypeReference.new("None")
            if return_type is None
            else return_type,
            body=[PythonCustomStatement("pass")] if body is None else body,
            decorators=[] if decorators is None else decorators,
        )

    def serialize_python_method_definition(self, indent: str) -> str:
        formatted_arguments = ", ".join(
            ["self"]
            + [f"{arg_name}: {arg_type}" for arg_name, arg_type in self.arguments]
        )
        output = ""
        for decorator in self.decorators:
            output += f"{indent}@{decorator}\n"
        output += (
            f"{indent}def {self.name}({formatted_arguments}) -> {self.return_type}:"
        )
        for stmt in self.body:
            output += f"\n{stmt.serialize_python_statement(indent+'    ')}"
        return output


class PythonTypeClass(NamedTuple):
    name: str
    module: Optional[str]
    required_properties: List[Tuple[str, PythonTypeReference]]
    optional_properties: List[Tuple[str, PythonTypeReference]]
    methods: List[PythonMethod]

    def python_type_reference(self) -> PythonTypeReference:
        return PythonTypeReference.new(self.name, self.module)

    def serialize_python_type_definition(self, indent: str) -> Tuple[str, List[str]]:
        imports = ["typing"]
        output = f"{indent}class {self.name}(typing.NamedTuple):"
        for property_name, property_type in self.required_properties:
            property_name = (
                property_name if property_name not in KEYWORDS else f"{property_name}_"
            )
            output += f"\n{indent}    {property_name}: '{property_type}'"
            imports.extend(property_type.modules())
        for property_name, property_type in self.optional_properties:
            property_name = (
                property_name if property_name not in KEYWORDS else f"{property_name}_"
            )
            output += f"\n{indent}    {property_name}: typing.Optional['{property_type}'] = None"
            imports.extend(property_type.modules())
        for method in self.methods:
            output += f"\n{method.serialize_python_method_definition(indent+'    ')}"
        return output, imports


class PythonTypeNewType(NamedTuple):
    name: str
    parent_type: PythonTypeReference
    module: Optional[str] = None

    def python_type_reference(self) -> PythonTypeReference:
        return PythonTypeReference.new(self.name, self.module)

    def serialize_python_type_definition(self, indent: str) -> Tuple[str, List[str]]:
        return (
            f"{indent}{self.name} = typing.NewType('"
            f"{self.name}', {self.parent_type})",
            ["typing"]
            if self.parent_type.module is None
            else ["typing", self.parent_type.module],
        )
