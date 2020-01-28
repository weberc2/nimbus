from .spec import (
    NonPrimitiveListPropertyTypeReference,
    NonPrimitiveMapPropertyTypeReference,
    NonPrimitivePropertyType,
    NonPrimitiveScalarPropertyTypeReference,
    PrimitiveListPropertyTypeReference,
    PrimitiveMapPropertyTypeReference,
    PrimitiveScalarPropertyTypeReference,
    PrimitiveType,
    PropertyTypeReference,
)


def _primitive_type_reference_expression(
    property_variable: str, primitive_type: PrimitiveType
) -> str:
    if primitive_type == PrimitiveType.Boolean:
        return f"nimbus_core.property_boolean_reference({property_variable})"
    if primitive_type == PrimitiveType.Double:
        return f"nimbus_core.property_double_reference({property_variable})"
    if primitive_type == PrimitiveType.Integer:
        return f"nimbus_core.property_integer_reference({property_variable})"
    if primitive_type == PrimitiveType.Json:
        return f"nimbus_core.property_json_reference({property_variable})"
    if primitive_type == PrimitiveType.Long:
        return f"nimbus_core.property_long_reference({property_variable})"
    if primitive_type == PrimitiveType.String:
        return f"nimbus_core.property_string_reference({property_variable})"
    if primitive_type == PrimitiveType.Timestamp:
        return f"property_timestamp_reference({property_variable})"
    raise TypeError(f"Invalid PrimitiveType: {primitive_type} ({type(primitive_type)})")


def _non_primitive_property_type_reference_expression(
    module: str, property_variable: str, property_type: NonPrimitivePropertyType
) -> str:
    if str(property_type) == "Tag":
        module = "nimbus_core"
    return f"{module}.{property_type}.reference({property_variable})"


def reference_expression(
    module, property_variable: str, property_type_reference: PropertyTypeReference
) -> str:
    base_expr: str = ""
    if isinstance(property_type_reference, PrimitiveScalarPropertyTypeReference):
        base_expr = _primitive_type_reference_expression(
            property_variable, property_type_reference.PrimitiveType
        )
    elif isinstance(property_type_reference, NonPrimitiveScalarPropertyTypeReference):
        base_expr = _non_primitive_property_type_reference_expression(
            module, property_variable, property_type_reference.Type
        )
    elif isinstance(property_type_reference, PrimitiveListPropertyTypeReference):
        reference_expression = _primitive_type_reference_expression(
            "x", property_type_reference.PrimitiveItemType
        )
        base_expr = f"[{reference_expression} for x in {property_variable}]"
    elif isinstance(property_type_reference, NonPrimitiveListPropertyTypeReference):
        reference_expression = _non_primitive_property_type_reference_expression(
            module, "x", property_type_reference.ItemType
        )
        base_expr = f"[{reference_expression} for x in {property_variable}]"
    elif isinstance(property_type_reference, PrimitiveMapPropertyTypeReference):
        reference_expression = _primitive_type_reference_expression(
            "value", property_type_reference.PrimitiveItemType
        )
        base_expr = f"{{key: {reference_expression} for key, value in {property_variable}.items()}}"
    elif isinstance(property_type_reference, NonPrimitiveMapPropertyTypeReference):
        reference_expression = _non_primitive_property_type_reference_expression(
            module, "value", property_type_reference.ItemType
        )
        base_expr = f"{{key: {reference_expression} for key, value in {property_variable}.items()}}"
    else:
        raise NotImplementedError(
            "_reference_expression() is not implemented for "
            f"{property_type_reference} ({type(property_type_reference)})"
        )

    if property_type_reference.Required:
        return base_expr
    return f"{base_expr} if {property_variable} is not None else None"