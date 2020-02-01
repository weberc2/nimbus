from typing import Dict, List, Tuple

import nimbus_codegen.ast as py
from .refexpr import reference_expression
from .spec import (
    PrimitiveScalarAttributeSpec,
    PrimitiveType,
    CompoundPropertyTypeDefinition,
    NonPrimitiveListPropertyTypeReference,
    PrimitiveScalarPropertyTypeReference,
    PropertyTypeDefinition,
    PropertyTypeReference,
    ResourceSpec,
    Specification,
)
from .typeref import ToPythonType

_Props = List[Tuple[str, py.Type]]


def _property_type_refs(
    module: str, props: Dict[str, PropertyTypeReference]
) -> Tuple[_Props, _Props]:
    required = []
    optional = []
    for property_name, typeref in props.items():
        property_python_type_reference = ToPythonType.from_property(
            property_name, module, typeref
        )
        # All other property spec types have a `Required` attribute
        if typeref.Required:
            required.append((property_name, property_python_type_reference))
        else:
            optional.append((property_name, property_python_type_reference))
    return required, optional


BUILTIN_STR = py.Type.new("str", None)
TYPE_JSON = py.Type.dict_type_ref(BUILTIN_STR, py.Type.new("Any", "typing"))

TYPE_RESOURCE_LOGICAL_ID = py.Type(
    name="Callable",
    module="typing",
    type_arguments=[
        py.Type(
            name="",
            type_arguments=[py.Type.new(name="Resource", module="nimbus_core")],
        ),
        BUILTIN_STR,
    ],
)
TYPE_PARAMETER_LOGICAL_ID = py.Type(
    name="Callable",
    module="typing",
    type_arguments=[
        py.Type(
            name="",
            type_arguments=[py.Type.new(name="Parameter", module="nimbus_core")],
        ),
        BUILTIN_STR,
    ],
)


def _properties_dict(
    module: py.Variable,
    resource_logical_id_variable: py.Variable,
    parameter_logical_id_variable: py.Variable,
    properties: Dict[str, PropertyTypeReference],
) -> py.Block:
    output = py.Block(
        [
            py.DeclareAssignStmt(
                label="output", type_=TYPE_JSON, value=py.DictLiteral([])
            )
        ]
    )
    output_variable = py.Variable("output")
    for property_name, typeref in properties.items():
        if property_name in py.KEYWORDS:
            property_name += "_"
        refexpr = reference_expression(
            module=module,
            property_variable=py.Variable(
                py.Attr(parent=py.Variable("self"), label=property_name)
            ),
            resource_logical_id_variable=resource_logical_id_variable,
            parameter_logical_id_variable=parameter_logical_id_variable,
            property_type_reference=typeref,
        )
        if not typeref.Required:
            output.stmts.append(
                py.AssignStmt(left=py.Variable(property_name), right=refexpr)
            )
            output.stmts.append(
                py.IfStmt(
                    condition=py.IsNotExpr(
                        left=py.Variable(property_name), right=py.NoneLiteral()
                    ),
                    body=py.Block(
                        [
                            py.AssignStmt(
                                left=py.DictKeyAccess(
                                    dict_=output_variable,
                                    key=py.StringLiteral(property_name),
                                ),
                                right=py.Variable(property_name),
                            )
                        ]
                    ),
                )
            )
        else:
            output.stmts.append(
                py.AssignStmt(
                    left=py.DictKeyAccess(
                        dict_=output_variable, key=py.StringLiteral(property_name)
                    ),
                    right=refexpr,
                )
            )
    return output


def _resource_to_cloudformation_method(
    module: py.Variable, resource_id: str, spec: ResourceSpec
) -> py.Method:
    RESOURCE_LOGICAL_ID_VARIABLE = "resource_logical_id"
    PARAMETER_LOGICAL_ID_VARIABLE = "parameter_logical_id"
    output = _properties_dict(
        module,
        py.Variable(RESOURCE_LOGICAL_ID_VARIABLE),
        py.Variable(PARAMETER_LOGICAL_ID_VARIABLE),
        spec.Properties,
    )
    output.stmts.append(
        py.ReturnStmt(
            py.DictLiteral(
                [
                    (py.StringLiteral("Type"), py.StringLiteral(resource_id)),
                    (py.StringLiteral("Properties"), py.Variable("output")),
                ]
            )
        )
    )
    return py.Method.new(
        name="resource_to_cloudformation",
        arguments=[
            (RESOURCE_LOGICAL_ID_VARIABLE, TYPE_RESOURCE_LOGICAL_ID),
            (PARAMETER_LOGICAL_ID_VARIABLE, TYPE_PARAMETER_LOGICAL_ID),
        ],
        return_type=TYPE_JSON,
        body=output,
    )


class _ToPythonType:
    @staticmethod
    def from_resource_spec(
        module: str, resource_id: str, spec: ResourceSpec
    ) -> py.ClassDef:
        idx = resource_id.rfind("::")
        required_props, optional_props = _property_type_refs(module, spec.Properties)
        return py.ClassDef(
            name=resource_id[0 if idx < 0 else idx + 2 :],
            module=module,
            required_properties=required_props,
            optional_properties=optional_props,
            methods=[
                py.Method.new(
                    # Sometimes there are '.'s in the attribute names. For
                    # example, AWS::RedShift::Cluster has attributes
                    # Endpoint.Address and Endpoint.Port. We could make
                    # Cluster.GetEndpoint() return an object with
                    # `GetAddress()` and `GetPort()` methods, but for now
                    # replacing it with an underscore is easier.
                    name=f"Get{attr_name.replace('.', '_')}",
                    return_type=py.Type.new(
                        name="AttributeString", module="nimbus_core"
                    ),
                    body=py.Block(
                        [
                            py.ReturnStmt(
                                py.CallExpr(
                                    fn=py.Attr(
                                        parent=py.Variable("nimbus_core"),
                                        label="AttributeString",
                                    ),
                                    args=[
                                        py.Variable("self"),
                                        py.StringLiteral(attr_name),
                                    ],
                                )
                            )
                        ]
                    ),
                )
                for attr_name, attr_spec in spec.Attributes.items()
                # TODO: Support other attribute types in addition to strings
                # if isinstance(attr_spec, PrimitiveScalarAttributeSpec)
                # and attr_spec.PrimitiveType == PrimitiveType.String
            ]
            + [
                _resource_to_cloudformation_method(
                    py.Variable(module), resource_id, spec
                )
            ],
        )

    @staticmethod
    def from_property_type(
        module: str, name: str, definition: PropertyTypeDefinition
    ) -> py.TypeDef:
        if isinstance(definition, CompoundPropertyTypeDefinition):
            required_props, optional_props = _property_type_refs(
                module, definition.Properties
            )
            RESOURCE_LOGICAL_ID_VARIABLE = "resource_logical_id"
            PARAMETER_LOGICAL_ID_VARIABLE = "parameter_logical_id"
            output = _properties_dict(
                py.Variable(module),
                py.Variable(RESOURCE_LOGICAL_ID_VARIABLE),
                py.Variable(PARAMETER_LOGICAL_ID_VARIABLE),
                definition.Properties,
            )
            output.stmts.append(py.ReturnStmt(py.Variable("output")))
            return py.ClassDef(
                name=name,
                module=module,
                required_properties=required_props,
                optional_properties=optional_props,
                methods=[
                    py.Method.new(
                        name="reference",
                        arguments=[
                            (RESOURCE_LOGICAL_ID_VARIABLE, TYPE_RESOURCE_LOGICAL_ID,),
                            (PARAMETER_LOGICAL_ID_VARIABLE, TYPE_PARAMETER_LOGICAL_ID,),
                        ],
                        return_type=TYPE_JSON,
                        body=output,
                    ),
                ],
            )
        elif isinstance(definition, PrimitiveScalarPropertyTypeReference):
            return py.NewTypeDef(
                name=name,
                module=module,
                parent_type=ToPythonType.from_primitive_type(definition.PrimitiveType),
            )
        elif isinstance(definition, NonPrimitiveListPropertyTypeReference):
            return py.NewTypeDef(
                name=name,
                module=module,
                parent_type=ToPythonType.from_non_primitive_list_property(
                    module, definition
                ),
            )
        raise TypeError(
            f"Invalid PropertyTypeDefinition: {definition}" " (type {type(definition)})"
        )


def resource_namespace(
    module: str, spec: Specification, resource_id: str
) -> List[py.TypeDef]:
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
