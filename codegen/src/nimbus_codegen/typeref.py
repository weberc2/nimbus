from .ast import PythonTypeReference
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

TYPE_REF_STRING = PythonTypeReference.new("PropertyString", "nimbus_core")
TYPE_REF_INTEGER = PythonTypeReference.new("PropertyInteger", "nimbus_core")
TYPE_REF_LONG = PythonTypeReference.new("PropertyLong", "nimbus_core")
TYPE_REF_BOOLEAN = PythonTypeReference.new("PropertyBoolean", "nimbus_core")
TYPE_REF_DOUBLE = PythonTypeReference.new("PropertyDouble", "nimbus_core")
TYPE_REF_TIMESTAMP = PythonTypeReference.new("PropertyTimestamp", "nimbus_core")
TYPE_REF_JSON = PythonTypeReference.new("PropertyJSON", "nimbus_core")


class ToPythonTypeRef:
    @staticmethod
    def from_primitive_type(primitive_type: PrimitiveType) -> "PythonTypeReference":
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

    @staticmethod
    def from_non_primitive_property(
        module: str, property_type: NonPrimitivePropertyType
    ) -> "PythonTypeReference":
        return PythonTypeReference.new(
            property_type, module if property_type != "Tag" else "nimbus_core"
        )

    @staticmethod
    def from_non_primitive_list_property(
        module, typeref: NonPrimitiveListPropertyTypeReference
    ) -> "PythonTypeReference":
        return PythonTypeReference.list_type_ref(
            ToPythonTypeRef.from_non_primitive_property(module, typeref.ItemType)
        )

    @staticmethod
    def from_property(
        name: str, module: str, typeref: PropertyTypeReference
    ) -> "PythonTypeReference":
        if isinstance(typeref, PrimitiveScalarPropertyTypeReference):
            return ToPythonTypeRef.from_primitive_type(typeref.PrimitiveType)
        if isinstance(typeref, NonPrimitiveScalarPropertyTypeReference):
            return ToPythonTypeRef.from_non_primitive_property(module, typeref.Type)
        if isinstance(typeref, PrimitiveListPropertyTypeReference):
            return PythonTypeReference.list_type_ref(
                ToPythonTypeRef.from_primitive_type(typeref.PrimitiveItemType)
            )
        if isinstance(typeref, NonPrimitiveListPropertyTypeReference):
            return ToPythonTypeRef.from_non_primitive_list_property(module, typeref)
        if isinstance(typeref, PrimitiveMapPropertyTypeReference):
            return PythonTypeReference.dict_type_ref(
                TYPE_REF_STRING,
                ToPythonTypeRef.from_primitive_type(typeref.PrimitiveItemType),
            )
        if isinstance(typeref, NonPrimitiveMapPropertyTypeReference):
            return PythonTypeReference.dict_type_ref(
                TYPE_REF_STRING,
                ToPythonTypeRef.from_non_primitive_property(module, typeref.ItemType),
            )
        raise TypeError(f"Invalid PropertyTypeReference: {typeref}")
