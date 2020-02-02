from typing import List, Tuple, Dict, Optional

import nimbus_codegen.ast as py

from .spec import (
    CompoundPropertyTypeDefinition,
    NonPrimitiveListPropertyTypeReference,
    NonPrimitiveMapPropertyTypeReference,
    NonPrimitivePropertyType,
    NonPrimitiveScalarPropertyTypeReference,
    PrimitiveListPropertyTypeReference,
    PrimitiveMapPropertyTypeReference,
    PrimitiveScalarPropertyTypeReference,
    PrimitiveType,
    PropertyTypeReference,
    PropertyTypeDefinition,
)


def _primitive_type_reference_expression(
    property_variable: py.Variable,
    resource_logical_id_variable: py.Variable,
    parameter_logical_id_variable: py.Variable,
    primitive_type: PrimitiveType,
) -> py.CallExpr:
    typestr: str
    args: List[py.Expr] = [property_variable, parameter_logical_id_variable]
    if primitive_type == PrimitiveType.Boolean:
        typestr = "boolean"
    elif primitive_type == PrimitiveType.Double:
        typestr = "double"
    elif primitive_type == PrimitiveType.Integer:
        typestr = "integer"
    elif primitive_type == PrimitiveType.Json:
        typestr = "json"
        args = [
            property_variable,
            resource_logical_id_variable,
            parameter_logical_id_variable,
        ]
    elif primitive_type == PrimitiveType.Long:
        typestr = "long"
    elif primitive_type == PrimitiveType.String:
        typestr = "string"
        args = [
            property_variable,
            resource_logical_id_variable,
            parameter_logical_id_variable,
        ]
    elif primitive_type == PrimitiveType.Timestamp:
        typestr = "timestamp"
    else:
        raise TypeError(
            f"Invalid PrimitiveType: {primitive_type} ({type(primitive_type)})"
        )
    return py.CallExpr(
        fn=py.Attr(
            parent=py.Variable("nimbus_core"), label=f"property_{typestr}_reference"
        ),
        args=args,
    )


def _non_primitive_property_type_reference_expression(
    module: py.Variable,
    property_variable: py.Variable,
    resource_logical_id_variable: py.Variable,
    parameter_logical_id_variable: py.Variable,
    property_types: Dict[
        NonPrimitivePropertyType, Tuple[Optional[py.Variable], PropertyTypeDefinition]
    ],
    property_type: NonPrimitivePropertyType,
    required: bool,
) -> py.Expr:
    def type_expr(
        module: py.Variable, property_type: NonPrimitivePropertyType, required: bool
    ) -> py.Expr:
        property_type_module, property_type_definition = property_types[property_type]
        if property_type_module is not None:
            module = property_type_module
        if isinstance(property_type_definition, CompoundPropertyTypeDefinition):
            return py.Attr(
                parent=py.Attr(parent=module, label=str(property_type)),
                label="reference",
            )
        elif isinstance(
            property_type_definition, NonPrimitiveListPropertyTypeReference
        ):
            base_expr = type_expr(
                module,
                property_type_definition.ItemType,
                property_type_definition.Required,
            )
        elif isinstance(property_type_definition, PrimitiveScalarPropertyTypeReference):
            base_expr = _primitive_type_reference_expression(
                property_variable,
                resource_logical_id_variable,
                parameter_logical_id_variable,
                property_type_definition.PrimitiveType,
            )
        else:
            raise TypeError(
                f"Invalid PropertyTypeDefinition: {module.label}.{property_type} ({property_type_definition})"
            )
        if not required:
            base_expr = py.IfExpr(
                true_value=base_expr,
                condition=py.IsNotExpr(left=base_expr, right=py.NoneLiteral),
                false_value=py.NoneLiteral,
            )
        return base_expr

    return py.CallExpr(
        fn=type_expr(module, property_type, required),
        args=[
            property_variable,
            resource_logical_id_variable,
            parameter_logical_id_variable,
        ],
    )


def reference_expression(
    module: py.Variable,
    property_variable: py.Variable,
    resource_logical_id_variable: py.Variable,
    parameter_logical_id_variable: py.Variable,
    property_types: Dict[
        NonPrimitivePropertyType, Tuple[Optional[py.Variable], PropertyTypeDefinition]
    ],
    property_type_reference: PropertyTypeReference,
) -> py.Expr:
    base_expr: py.Expr
    if isinstance(property_type_reference, PrimitiveScalarPropertyTypeReference):
        base_expr = _primitive_type_reference_expression(
            property_variable,
            resource_logical_id_variable,
            parameter_logical_id_variable,
            property_type_reference.PrimitiveType,
        )
    elif isinstance(property_type_reference, NonPrimitiveScalarPropertyTypeReference):
        base_expr = _non_primitive_property_type_reference_expression(
            module,
            property_variable,
            resource_logical_id_variable,
            parameter_logical_id_variable,
            property_types,
            property_type_reference.Type,
            property_type_reference.Required,
        )
    elif isinstance(property_type_reference, PrimitiveListPropertyTypeReference):
        forexpr = py.Variable("x")
        base_expr = py.ListComprehension(
            expr=_primitive_type_reference_expression(
                forexpr,
                resource_logical_id_variable,
                parameter_logical_id_variable,
                property_type_reference.PrimitiveItemType,
            ),
            forexpr=forexpr,
            inexpr=property_variable,
        )
    elif isinstance(property_type_reference, NonPrimitiveListPropertyTypeReference):
        forexpr = py.Variable("x")
        base_expr = py.ListComprehension(
            expr=_non_primitive_property_type_reference_expression(
                module,
                forexpr,
                resource_logical_id_variable,
                parameter_logical_id_variable,
                property_types,
                property_type_reference.ItemType,
                property_type_reference.Required,
            ),
            forexpr=forexpr,
            inexpr=property_variable,
        )
    elif isinstance(property_type_reference, PrimitiveMapPropertyTypeReference):
        keyexpr = py.Variable("key")
        valexpr = py.Variable("value")
        base_expr = py.DictComprehension(
            keyexpr=keyexpr,
            valexpr=_primitive_type_reference_expression(
                valexpr,
                resource_logical_id_variable,
                parameter_logical_id_variable,
                property_type_reference.PrimitiveItemType,
            ),
            forexpr=py.MultiExpr([keyexpr, valexpr]),
            inexpr=py.CallExpr(
                fn=py.Attr(parent=property_variable, label="items"), args=[]
            ),
        )
    elif isinstance(property_type_reference, NonPrimitiveMapPropertyTypeReference):
        keyexpr = py.Variable("key")
        valexpr = py.Variable("value")
        base_expr = py.DictComprehension(
            keyexpr=keyexpr,
            valexpr=_non_primitive_property_type_reference_expression(
                module,
                valexpr,
                resource_logical_id_variable,
                parameter_logical_id_variable,
                property_types,
                property_type_reference.ItemType,
                property_type_reference.Required,
            ),
            forexpr=py.MultiExpr([keyexpr, valexpr]),
            inexpr=py.CallExpr(
                fn=py.Attr(parent=property_variable, label="items"), args=[]
            ),
        )
    else:
        raise NotImplementedError(
            "reference_expression() is not implemented for "
            f"{property_type_reference} ({type(property_type_reference)})"
        )

    if property_type_reference.Required:
        return base_expr
    return py.IfExpr(
        true_value=base_expr,
        condition=py.IsNotExpr(left=property_variable, right=py.NoneLiteral),
        false_value=py.NoneLiteral,
    )
