import nimbus_codegen.ast as py
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

TYPE_STRING = py.Type.new("PropertyString", "nimbus_core")
TYPE_INTEGER = py.Type.new("PropertyInteger", "nimbus_core")
TYPE_LONG = py.Type.new("PropertyLong", "nimbus_core")
TYPE_BOOLEAN = py.Type.new("PropertyBoolean", "nimbus_core")
TYPE_DOUBLE = py.Type.new("PropertyDouble", "nimbus_core")
TYPE_TIMESTAMP = py.Type.new("PropertyTimestamp", "nimbus_core")
TYPE_JSON = py.Type.new("PropertyJSON", "nimbus_core")


class ToPythonType:
    @staticmethod
    def from_primitive_type(primitive_type: PrimitiveType) -> "py.Type":
        if primitive_type == PrimitiveType.String:
            return TYPE_STRING
        if primitive_type == PrimitiveType.Boolean:
            return TYPE_BOOLEAN
        if primitive_type == PrimitiveType.Integer:
            return TYPE_INTEGER
        if primitive_type == PrimitiveType.Long:
            return TYPE_LONG
        if primitive_type == PrimitiveType.Double:
            return TYPE_DOUBLE
        if primitive_type == PrimitiveType.Timestamp:
            return TYPE_TIMESTAMP
        if primitive_type == PrimitiveType.Json:
            return TYPE_JSON
        raise TypeError(
            f"Invalid PrimitiveType: {primitive_type} ({type(primitive_type)})"
        )

    @staticmethod
    def from_non_primitive_property(
        module: str, property_type: NonPrimitivePropertyType
    ) -> "py.Type":
        return py.Type.new(
            property_type, module if property_type != "Tag" else "nimbus_core"
        )

    @staticmethod
    def from_non_primitive_list_property(
        module, typeref: NonPrimitiveListPropertyTypeReference
    ) -> "py.Type":
        return py.Type.list_type_ref(
            ToPythonType.from_non_primitive_property(module, typeref.ItemType)
        )

    @staticmethod
    def from_property(
        name: str, module: str, typeref: PropertyTypeReference
    ) -> "py.Type":
        if isinstance(typeref, PrimitiveScalarPropertyTypeReference):
            return ToPythonType.from_primitive_type(typeref.PrimitiveType)
        if isinstance(typeref, NonPrimitiveScalarPropertyTypeReference):
            return ToPythonType.from_non_primitive_property(module, typeref.Type)
        if isinstance(typeref, PrimitiveListPropertyTypeReference):
            return py.Type.list_type_ref(
                ToPythonType.from_primitive_type(typeref.PrimitiveItemType)
            )
        if isinstance(typeref, NonPrimitiveListPropertyTypeReference):
            return ToPythonType.from_non_primitive_list_property(module, typeref)
        if isinstance(typeref, PrimitiveMapPropertyTypeReference):
            return py.Type.dict_type_ref(
                TYPE_STRING,
                ToPythonType.from_primitive_type(typeref.PrimitiveItemType),
            )
        if isinstance(typeref, NonPrimitiveMapPropertyTypeReference):
            return py.Type.dict_type_ref(
                TYPE_STRING,
                ToPythonType.from_non_primitive_property(module, typeref.ItemType),
            )
        raise TypeError(f"Invalid PropertyTypeReference: {typeref}")
