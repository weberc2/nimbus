import os
from typing import Dict, List, NamedTuple, Optional, Tuple

from spec import (
    NestedPropertySpec,
    NonPrimitiveListPropertySpec,
    NonPrimitiveMapPropertySpec,
    NonPrimitivePropertyType,
    NonPrimitiveScalarPropertySpec,
    PrimitiveListPropertySpec,
    PrimitiveMapPropertySpec,
    PrimitiveScalarPropertySpec,
    PrimitiveType,
    PropertySpec,
    PropertyType,
    ResourceSpec,
    Specification,
    load,
)
from typing_extensions import Protocol


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

    def serialize_python_method_definition(self, indent: str) -> str:
        formatted_arguments = ", ".join(
            ["self"]
            + [f"{arg_name}: {arg_type}" for arg_name, arg_type in self.arguments]
        )
        output = (
            f"{indent}def {self.name}({formatted_arguments}) -> {self.return_type}:"
        )
        for stmt in self.body:
            output += f"\n{stmt.serialize_python_statement(indent+'    ')}"
        return output


KEYWORDS = "None"


class PythonTypeClass(NamedTuple):
    name: str
    module: Optional[str]
    required_properties: List[Tuple[str, PythonTypeReference]]
    optional_properties: List[Tuple[str, PythonTypeReference]]
    methods: List[PythonMethod]

    def python_type_reference(self) -> PythonTypeReference:
        return PythonTypeReference(
            name=self.name, type_arguments=[], module=self.module
        )

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
    parent_type_module: Optional[str] = None

    def python_type_reference(self) -> PythonTypeReference:
        return PythonTypeReference(
            name=self.name, type_arguments=[], module=self.module
        )

    def serialize_python_type_definition(self, indent: str) -> Tuple[str, List[str]]:
        return (
            f"{indent}{self.name} = typing.NewType('"
            f"{self.name}', {self.parent_type})",
            ["typing"]
            if self.parent_type_module is None
            else ["typing", self.parent_type_module],
        )


def _dict_type(
    key_type: PythonTypeReference, value_type: PythonTypeReference
) -> PythonTypeReference:
    return PythonTypeReference(
        name="Dict", type_arguments=[key_type, value_type], module="typing"
    )


def _list_type(item_type: PythonTypeReference) -> PythonTypeReference:
    return PythonTypeReference(name="List", type_arguments=[item_type], module="typing")


def _cfntype(name: str) -> PythonTypeReference:
    return PythonTypeReference(name=name, type_arguments=[], module="libcfn.types")


def _proptype(name: str) -> PythonTypeReference:
    return _cfntype(f"Property{name}")


BUILTIN_STR = PythonTypeReference(name="str", type_arguments=[], module=None)
TYPING_ANY = PythonTypeReference(name="Any", type_arguments=[], module="typing")
TYPE_REF_STRING = _proptype("String")
TYPE_REF_INTEGER = _proptype("Integer")
TYPE_REF_LONG = _proptype("Long")
TYPE_REF_BOOLEAN = _proptype("Boolean")
TYPE_REF_DOUBLE = _proptype("Double")
TYPE_REF_TIMESTAMP = _proptype("Timestamp")
TYPE_REF_JSON = _proptype("JSON")
TYPE_REF_TAG = _cfntype("Tag")


class PythonTypeBuilder(NamedTuple):
    namespace: Dict[NonPrimitivePropertyType, PropertyType]
    module: str

    def build_primitive_type(
        self, primitive_type: PrimitiveType
    ) -> PythonTypeReference:
        if primitive_type == PrimitiveType.String:
            return TYPE_REF_STRING
        if primitive_type == PrimitiveType.Boolean:
            return TYPE_REF_BOOLEAN
        if primitive_type == PrimitiveType.Integer:
            return TYPE_REF_INTEGER
        if primitive_type == PrimitiveType.Long:
            return TYPE_REF_LONG
        if primitive_type == PrimitiveType.Double:
            return TYPE_REF_DOUBLE
        if primitive_type == PrimitiveType.Timestamp:
            return TYPE_REF_TIMESTAMP
        if primitive_type == PrimitiveType.Json:
            return TYPE_REF_JSON
        raise TypeError(
            f"Invalid PrimitiveType: {primitive_type} ({type(primitive_type)})"
        )

    def build_primitive_list_type(
        self, spec: PrimitiveListPropertySpec
    ) -> PythonTypeReference:
        return _list_type(self.build_primitive_type(spec.PrimitiveItemType))

    def class_from_properties(
        self, name: str, properties: Dict[str, PropertySpec]
    ) -> PythonTypeClass:
        required_properties = []
        optional_properties = []
        for property_name, property_spec in properties.items():
            property_type_reference = self.build_spec(property_name, property_spec)
            if isinstance(property_spec, NestedPropertySpec):
                raise Exception(
                    "NestedPropertySpecs shouldn't live under other nested property specs?"
                )

            # All other property spec types have a `Required` attribute
            if property_spec.Required:
                required_properties.append((property_name, property_type_reference))
            else:
                optional_properties.append((property_name, property_type_reference))
        return PythonTypeClass(
            name=name,
            module=self.module,
            required_properties=required_properties,
            optional_properties=optional_properties,
            methods=[],
        )

    def build_nested_property_type(
        self, name: str, spec: NestedPropertySpec
    ) -> PythonTypeReference:
        return PythonTypeReference(name=name, type_arguments=[], module=self.module)

    def build_primitive_map_property_spec(
        self, spec: PrimitiveMapPropertySpec
    ) -> PythonTypeReference:
        return _dict_type(
            TYPE_REF_STRING, self.build_primitive_type(spec.PrimitiveItemType)
        )

    def build_non_primitive_map_property_spec(
        self, spec: NonPrimitiveMapPropertySpec
    ) -> PythonTypeReference:
        value_type_reference = self.build_non_primitive_property_type(spec.ItemType)
        return _dict_type(TYPE_REF_STRING, value_type_reference)

    def build_non_primitive_property_type(
        self, property_type: NonPrimitivePropertyType
    ) -> PythonTypeReference:
        if property_type == "Tag":
            return TYPE_REF_TAG
        # NOTE: It's a hard error if property_type is not in self.namespace
        return self.build_type(str(property_type), self.namespace[property_type])

    def build_non_primitive_list_type(
        self, spec: NonPrimitiveListPropertySpec
    ) -> PythonTypeReference:
        item_type_reference = self.build_non_primitive_property_type(spec.ItemType)
        return _list_type(item_type_reference)

    def build_spec(self, name: str, spec: PropertySpec) -> PythonTypeReference:
        if isinstance(spec, PrimitiveScalarPropertySpec):
            return self.build_primitive_type(spec.PrimitiveType)
        if isinstance(spec, NonPrimitiveScalarPropertySpec):
            return self.build_non_primitive_property_type(spec.Type)
        if isinstance(spec, PrimitiveListPropertySpec):
            return self.build_primitive_list_type(spec)
        if isinstance(spec, NonPrimitiveListPropertySpec):
            return self.build_non_primitive_list_type(spec)
        if isinstance(spec, PrimitiveMapPropertySpec):
            return self.build_primitive_map_property_spec(spec)
        if isinstance(spec, NonPrimitiveMapPropertySpec):
            return self.build_non_primitive_map_property_spec(spec)
        raise TypeError(f"Invalid PropertySpec: {spec}")

    def build_type(self, name: str, spec: PropertyType) -> PythonTypeReference:
        if isinstance(spec, PrimitiveScalarPropertySpec):
            return self.build_primitive_type(spec.PrimitiveType)
        if isinstance(spec, NonPrimitiveListPropertySpec):
            return self.build_non_primitive_list_type(spec)
        if isinstance(spec, NestedPropertySpec):
            return self.build_nested_property_type(name, spec)
        raise TypeError(f"Invalid PropertySpec: {spec}")

    @staticmethod
    def _primitive_type_reference_expression(
        property_variable: str, primitive_type: PrimitiveType
    ) -> str:
        if primitive_type == PrimitiveType.Boolean:
            return f"libcfn.types.property_boolean_reference({property_variable})"
        if primitive_type == PrimitiveType.Double:
            return f"libcfn.types.property_double_reference({property_variable})"
        if primitive_type == PrimitiveType.Integer:
            return f"libcfn.types.property_integer_reference({property_variable})"
        if primitive_type == PrimitiveType.Json:
            return f"{property_variable}"
        if primitive_type == PrimitiveType.Long:
            return f"libcfn.types.property_long_reference({property_variable})"
        if primitive_type == PrimitiveType.String:
            return f"libcfn.types.property_string_reference({property_variable})"
        if primitive_type == PrimitiveType.Timestamp:
            return f"property_timestamp_reference({property_variable})"
        raise TypeError(
            f"Invalid PrimitiveType: {primitive_type} ({type(primitive_type)})"
        )

    @staticmethod
    def _non_primitive_property_type_reference_expression(
        module, property_variable: str, property_type: NonPrimitivePropertyType
    ) -> str:
        if str(property_type) == "Tag":
            module = "libcfn.types"
        return f"{module}.{property_type}.reference({property_variable})"

    @staticmethod
    def _reference_expression(
        module, property_variable: str, property_spec: PropertySpec
    ) -> str:
        base_expr: str = ""
        if isinstance(property_spec, PrimitiveScalarPropertySpec):
            base_expr = PythonTypeBuilder._primitive_type_reference_expression(
                property_variable, property_spec.PrimitiveType
            )
        elif isinstance(property_spec, NonPrimitiveScalarPropertySpec):
            base_expr = PythonTypeBuilder._non_primitive_property_type_reference_expression(
                module, property_variable, property_spec.Type
            )
        elif isinstance(property_spec, PrimitiveListPropertySpec):
            reference_expression = PythonTypeBuilder._primitive_type_reference_expression(
                "x", property_spec.PrimitiveItemType
            )
            base_expr = f"[{reference_expression} for x in {property_variable}]"
        elif isinstance(property_spec, NonPrimitiveListPropertySpec):
            reference_expression = PythonTypeBuilder._non_primitive_property_type_reference_expression(
                module, "x", property_spec.ItemType
            )
            base_expr = f"[{reference_expression} for x in {property_variable}]"
        elif isinstance(property_spec, PrimitiveMapPropertySpec):
            reference_expression = PythonTypeBuilder._primitive_type_reference_expression(
                "value", property_spec.PrimitiveItemType
            )
            base_expr = f"{{key: {reference_expression} for key, value in {property_variable}.items()}}"
        elif isinstance(property_spec, NonPrimitiveMapPropertySpec):
            reference_expression = PythonTypeBuilder._non_primitive_property_type_reference_expression(
                module, "value", property_spec.ItemType
            )
            base_expr = f"{{key: {reference_expression} for key, value in {property_variable}.items()}}"
        else:
            raise NotImplementedError(
                f"_reference_expression() is not implemented for {property_spec} ({type(property_spec)})"
            )

        if property_spec.Required:
            return base_expr
        return f"{base_expr} if {property_variable} is not None else None"

    @staticmethod
    def _build_resource_to_cloudformation_method(
        module: str, resource_id: str, spec: ResourceSpec
    ) -> PythonCustomStatement:
        output = f"output: {_dict_type(BUILTIN_STR, TYPING_ANY)} = {{}}"
        for property_name, property_spec in spec.Properties.items():
            reference_expression = PythonTypeBuilder._reference_expression(
                module, f"self.{property_name}", property_spec
            )
            if not property_spec.Required:
                output += f"\n{property_name} = {reference_expression}"
                output += f"\nif {property_name} is not None:"
                output += f"\n     output['{property_name}'] = {property_name}"
            else:
                output += f"\noutput['{property_name}'] = {reference_expression}"
        output += "\nreturn output"
        return PythonCustomStatement(content=output)

    def build_resource(self, resource_id: str, spec: ResourceSpec) -> PythonTypeClass:
        idx = resource_id.rfind("::")
        name = resource_id[0 if idx < 0 else idx + 2 :]
        python_class = self.class_from_properties(name, spec.Properties)
        python_class = PythonTypeClass(
            name=python_class.name,
            module=python_class.module,
            required_properties=[("logical_id", BUILTIN_STR)]
            + python_class.required_properties,
            optional_properties=python_class.optional_properties,
            methods=[
                PythonMethod(
                    name="resource_to_cloudformation",
                    arguments=[],
                    return_type=_dict_type(BUILTIN_STR, TYPING_ANY),
                    body=[
                        PythonTypeBuilder._build_resource_to_cloudformation_method(
                            self.module, resource_id, spec
                        )
                    ],
                )
            ],
        )
        return python_class


def generate_resource(
    module: str, spec: Specification, resource_id: str
) -> List[PythonType]:
    builder = PythonTypeBuilder(
        namespace={
            NonPrimitivePropertyType(key[len(resource_id) + 1 :]): value
            for key, value in spec.PropertyTypes.items()
            if key.startswith(resource_id)
        },
        module=module,
    )

    # Build type definitions for all property types in the resource's namespace.
    typedefs: List[PythonType] = []
    for property_type_name, property_type in spec.PropertyTypes.items():
        prefix = f"{resource_id}."
        if property_type_name.startswith(prefix) and isinstance(
            property_type, NestedPropertySpec
        ):
            class_ = builder.class_from_properties(
                name=property_type_name[len(prefix) :],
                properties=property_type.Properties,
            )
            typedefs.append(
                PythonTypeClass(
                    name=class_.name,
                    module=class_.module,
                    required_properties=class_.required_properties,
                    optional_properties=class_.optional_properties,
                    methods=[
                        PythonMethod(
                            name="reference",
                            arguments=[],
                            return_type=_dict_type(BUILTIN_STR, TYPING_ANY),
                            body=[
                                PythonCustomStatement(
                                    content="raise NotImplementedError()"
                                )
                            ],
                        )
                    ],
                )
            )

    # Build the type definition for the resource class.
    typedefs.append(
        builder.build_resource(resource_id, spec.ResourceTypes[resource_id])
    )

    return typedefs


def render_module(module: str, typedefs: List[PythonType]) -> str:
    typedef_output = ""
    import_output = f"from . import {module}"
    imports = {module}
    for typedef in typedefs:
        typedefstr, typedefimports = typedef.serialize_python_type_definition(indent="")
        typedef_output += f"\n\n{typedefstr}"
        for import_ in typedefimports:
            if import_ not in imports:
                import_output += f"\nimport {import_}"
            imports.add(import_)
    return f"{import_output}{typedef_output}"


def _resource_type_to_relpath(resource_type: str) -> str:
    if resource_type.startswith("AWS::"):
        resource_type = resource_type[len("AWS::") :]
    return f"{resource_type.lower().replace('::', '/')}.py"


def _resource_type_to_module(resource_type: str) -> str:
    idx = resource_type.rfind("::")
    if idx < 0:
        return resource_type
    return resource_type[idx + len("::") :].lower()


def generate_resource_file(
    spec: Specification, resource_type: str, directory: str
) -> None:
    filepath = os.path.join(directory, _resource_type_to_relpath(resource_type))
    module = _resource_type_to_module(resource_type)

    # Generate the directory that the target file will live in
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Make it a package
    with open(os.path.join(os.path.dirname(filepath), "__init__.py"), "w") as f:
        f.write("")

    # Render the file
    with open(filepath, "w") as f:
        f.write(render_module(module, generate_resource(module, spec, resource_type)))


def generate_resource_files(spec: Specification, directory: str) -> None:
    for resource_type in spec.ResourceTypes:
        generate_resource_file(spec, resource_type, directory)


if __name__ == "__main__":
    generate_resource_files(load(), "/tmp/output/src/awscfn")
