from typing import Dict, List, Tuple

from .ast import (
    PythonCustomStatement,
    PythonMethod,
    PythonType,
    PythonTypeClass,
    PythonTypeNewType,
    PythonTypeReference,
)
from .refexpr import reference_expression
from .spec import (
    CompoundPropertyTypeDefinition,
    NonPrimitiveListPropertyTypeReference,
    PrimitiveScalarPropertyTypeReference,
    PropertyTypeDefinition,
    PropertyTypeReference,
    ResourceSpec,
    Specification,
)
from .typeref import ToPythonTypeRef

_Props = List[Tuple[str, PythonTypeReference]]


def _property_type_refs(
    module: str, props: Dict[str, PropertyTypeReference]
) -> Tuple[_Props, _Props]:
    required = []
    optional = []
    for property_name, typeref in props.items():
        property_python_type_reference = ToPythonTypeRef.from_property(
            property_name, module, typeref
        )
        # All other property spec types have a `Required` attribute
        if typeref.Required:
            required.append((property_name, property_python_type_reference))
        else:
            optional.append((property_name, property_python_type_reference))
    return required, optional


BUILTIN_STR = PythonTypeReference.new("str", None)
TYPE_REF_JSON = PythonTypeReference.dict_type_ref(
    BUILTIN_STR, PythonTypeReference.new("Any", "typing")
)


def _resource_to_cloudformation_method(
    module: str, resource_id: str, spec: ResourceSpec
) -> PythonMethod:
    output = f"output: {TYPE_REF_JSON} = {{}}"
    for property_name, typeref in spec.Properties.items():
        refexpr = reference_expression(module, f"self.{property_name}", typeref)
        if not typeref.Required:
            output += f"\n{property_name} = {refexpr}"
            output += f"\nif {property_name} is not None:"
            output += f"\n     output['{property_name}'] = {property_name}"
        else:
            output += f"\noutput['{property_name}'] = {refexpr}"
    output += "\nreturn output"
    return PythonMethod.new(
        name="resource_to_cloudformation",
        return_type=TYPE_REF_JSON,
        body=[PythonCustomStatement(content=output)],
    )


class _ToPythonType:
    @staticmethod
    def from_resource_spec(
        module: str, resource_id: str, spec: ResourceSpec
    ) -> PythonTypeClass:
        idx = resource_id.rfind("::")
        required_props, optional_props = _property_type_refs(module, spec.Properties)
        return PythonTypeClass(
            name=resource_id[0 if idx < 0 else idx + 2 :],
            module=module,
            required_properties=[("logical_id", BUILTIN_STR)] + required_props,
            optional_properties=optional_props,
            methods=[
                PythonMethod.new(
                    # Sometimes there are '.'s in the attribute names. For
                    # example, AWS::RedShift::Cluster has attributes
                    # Endpoint.Address and Endpoint.Port. We could make
                    # Cluster.GetEndpoint() return an object with
                    # `GetAddress()` and `GetPort()` methods, but for now
                    # replacing it with an underscore is easier.
                    name=f"Get{attr_name.replace('.', '_')}",
                    return_type=PythonTypeReference.new(
                        name="AttributeString", module="nimbus_core"
                    ),
                    body=[
                        PythonCustomStatement(
                            content=f"return {{'Fn::GetAtt': f'{{self.logical_id}}.{attr_name}'}}",
                        )
                    ],
                )
                for attr_name, attr_spec in spec.Attributes.items()
            ]
            + [_resource_to_cloudformation_method(module, resource_id, spec)],
        )

    @staticmethod
    def from_property_type(
        module: str, name: str, definition: PropertyTypeDefinition
    ) -> PythonType:
        if isinstance(definition, CompoundPropertyTypeDefinition):
            required_props, optional_props = _property_type_refs(
                module, definition.Properties
            )
            return PythonTypeClass(
                name=name,
                module=module,
                required_properties=required_props,
                optional_properties=optional_props,
                methods=[
                    PythonMethod.new(
                        name="reference",
                        return_type=TYPE_REF_JSON,
                        body=[
                            PythonCustomStatement(content="raise NotImplementedError()")
                        ],
                    ),
                ],
            )
        elif isinstance(definition, PrimitiveScalarPropertyTypeReference):
            return PythonTypeNewType(
                name=name,
                module=module,
                parent_type=ToPythonTypeRef.from_primitive_type(
                    definition.PrimitiveType
                ),
            )
        elif isinstance(definition, NonPrimitiveListPropertyTypeReference):
            return PythonTypeNewType(
                name=name,
                module=module,
                parent_type=ToPythonTypeRef.from_non_primitive_list_property(
                    module, definition
                ),
            )
        raise TypeError(
            f"Invalid PropertyTypeDefinition: {definition}" " (type {type(definition)})"
        )


def resource_namespace(
    module: str, spec: Specification, resource_id: str
) -> List[PythonType]:
    # Build type definitions for all property types in the resource's namespace
    # as well as the type definition for the resource itself.
    prefix = f"{resource_id}."
    return [
        _ToPythonType.from_property_type(module, name[len(prefix) :], defn)
        for name, defn in spec.PropertyTypes.items()
        if name.startswith(prefix)
    ] + [
        _ToPythonType.from_resource_spec(
            module, resource_id, spec.ResourceTypes[resource_id]
        )
    ]
