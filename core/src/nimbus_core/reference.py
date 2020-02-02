from datetime import datetime
from typing import Any, Callable, Dict, List, Union

from nimbus_core.attribute import Attribute, AttributeString
from nimbus_core.intrinsic import IntrinsicFunction, Sub, Substitutable
from nimbus_core.parameter import (
    PARAMETER_TYPES,
    Parameter,
    ParameterNumber,
    ParameterString,
)
from nimbus_core.property import (
    PROPERTY_BOOLEAN_TYPES,
    PROPERTY_DOUBLE_TYPES,
    PROPERTY_INTEGER_TYPES,
    PROPERTY_LONG_TYPES,
    PROPERTY_STRING_TYPES,
    PROPERTY_TIMESTAMP_TYPES,
    PropertyBoolean,
    PropertyDouble,
    PropertyInteger,
    PropertyJSON,
    PropertyLong,
    PropertyString,
    PropertyTimestamp,
)
from nimbus_core.resource import Resource


def _ref(logical_id: str) -> Dict[str, Any]:
    return {"Ref": logical_id}


def property_string_reference(
    property_string: PropertyString,
    resource_logical_id: Callable[[Resource], str],
    parameter_logical_id: Callable[[Parameter], str],
) -> Union[str, Dict[str, Any]]:
    if isinstance(property_string, str):
        return property_string
    if isinstance(property_string, ParameterString):
        return _ref(parameter_logical_id(property_string))
    if isinstance(property_string, Sub):
        return sub_to_cloudformation(
            property_string, resource_logical_id, parameter_logical_id
        )
    if isinstance(property_string, Resource):
        return _ref(resource_logical_id(property_string))
    if isinstance(property_string, AttributeString):
        return property_string.attribute_to_cloudformation(resource_logical_id)
    raise TypeError(
        f"Invalid PropertyString: {property_string} ({type(property_string)})"
    )


def property_long_reference(
    property_long: PropertyLong, parameter_logical_id: Callable[[Parameter], str]
) -> Union[int, Dict[str, Any]]:
    if isinstance(property_long, int):
        return property_long
    if isinstance(property_long, ParameterNumber):
        return _ref(parameter_logical_id(property_long))
    # TODO: handle AttributeLong
    raise TypeError(f"Invalid PropertyLong: {property_long} ({type(property_long)})")


def property_integer_reference(
    property_integer: PropertyInteger, parameter_logical_id: Callable[[Parameter], str],
) -> Union[int, Dict[str, Any]]:
    if isinstance(property_integer, int):
        return property_integer
    if isinstance(property_integer, ParameterNumber):
        return _ref(parameter_logical_id(property_integer))
    # TODO: handle AttributeInteger
    raise TypeError(
        f"Invalid PropertyInteger: {property_integer} ({type(property_integer)})"
    )


def property_double_reference(
    property_double: PropertyDouble, parameter_logical_id: Callable[[Parameter], str]
) -> Union[float, Dict[str, Any]]:
    if isinstance(property_double, float):
        return property_double
    if isinstance(property_double, ParameterNumber):
        return _ref(parameter_logical_id(property_double))
    # TODO: handle AttributeDouble
    raise TypeError(
        f"Invalid PropertyDouble: {property_double} ({type(property_double)})"
    )


def property_boolean_reference(
    property_boolean: PropertyBoolean, parameter_logical_id: Callable[[Parameter], str]
) -> Union[bool, Dict[str, Any]]:
    if isinstance(property_boolean, bool):
        return property_boolean
    if isinstance(property_boolean, ParameterString):
        return _ref(parameter_logical_id(property_boolean))
    # TODO: handle AttributeBoolean
    raise TypeError(
        f"Invalid PropertyBoolean: {property_boolean} ({type(property_boolean)})"
    )


def property_timestamp_reference(
    property_timestamp: PropertyTimestamp,
    parameter_logical_id: Callable[[Parameter], str],
) -> Union[datetime, Dict[str, Any]]:
    if isinstance(property_timestamp, datetime):
        return property_timestamp
    if isinstance(property_timestamp, ParameterString):
        return _ref(parameter_logical_id(property_timestamp))
    # TODO: handle AttributeTimestamp
    raise TypeError(
        f"Invalid PropertyTimestamp: {property_timestamp} ({type(property_timestamp)})"
    )


class JSONSerializationErr(Exception):
    pass


def property_json_reference(
    property_json: PropertyJSON,
    resource_logical_id: Callable[[Resource], str],
    parameter_logical_id: Callable[[Parameter], str],
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    def _process_value(value: Any) -> Any:
        if isinstance(value, PARAMETER_TYPES):
            return _ref(parameter_logical_id(value))
        if isinstance(value, Resource):
            return _ref(resource_logical_id(value))
        if isinstance(value, Attribute):
            return value.attribute_to_cloudformation(resource_logical_id)
        if isinstance(value, IntrinsicFunction):
            return value.intrinsic_to_cloudformation(
                resource_logical_id, parameter_logical_id
            )
        if isinstance(value, PROPERTY_BOOLEAN_TYPES):
            return property_boolean_reference(value, parameter_logical_id)
        if isinstance(value, PROPERTY_DOUBLE_TYPES):
            return property_double_reference(value, parameter_logical_id)
        if isinstance(value, PROPERTY_INTEGER_TYPES):
            return property_integer_reference(value, parameter_logical_id)
        if isinstance(value, PROPERTY_LONG_TYPES):
            return property_long_reference(value, parameter_logical_id)
        if isinstance(value, PROPERTY_STRING_TYPES):
            return property_string_reference(
                value, resource_logical_id, parameter_logical_id
            )
        if isinstance(value, PROPERTY_TIMESTAMP_TYPES):
            return property_timestamp_reference(value, parameter_logical_id)
        if isinstance(value, dict):
            output_dict = {}
            for k, v in value.items():
                try:
                    output_dict[k] = _process_value(v)
                except JSONSerializationErr as e:
                    raise JSONSerializationErr(f"In key {k}: {e}")
            return output_dict
        if isinstance(value, list):
            output_list: List[Dict[str, Any]] = []
            for i, x in enumerate(value):
                try:
                    output_list.append(_process_value(x))
                except JSONSerializationErr as e:
                    raise JSONSerializationErr(f"At index {i}: {e}")
            return output_list
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        raise JSONSerializationErr(
            f"{value} (of type {type(value)}) is not a valid JSON node type"
        )

    try:
        return _process_value(property_json)
    except JSONSerializationErr as e:
        raise JSONSerializationErr(f"Invalid JSON object: {e}")


def substitutable_to_cloudformation(
    substitutable: Substitutable,
    resource_logical_id: Callable[[Resource], str],
    parameter_logical_id: Callable[[Parameter], str],
) -> Dict[str, Any]:
    if isinstance(substitutable, Resource):
        return _ref(resource_logical_id(substitutable))
    if isinstance(substitutable, PROPERTY_STRING_TYPES):
        return property_string_reference(
            substitutable, resource_logical_id, parameter_logical_id
        )
    if isinstance(substitutable, Attribute):
        return substitutable.attribute_to_cloudformation(resource_logical_id)
    if isinstance(substitutable, PARAMETER_TYPES):
        return _ref(parameter_logical_id(substitutable))
    raise TypeError(
        f"Invalid Substitutable: {substitutable} (type={type(substitutable)})"
    )


def sub_to_cloudformation(
    sub: Sub,
    resource_logical_id: Callable[[Resource], str],
    parameter_logical_id: Callable[[Parameter], str],
) -> Dict[str, Any]:
    return {
        "Fn::Sub": [
            sub.format_string,
            {
                key: substitutable_to_cloudformation(
                    value, resource_logical_id, parameter_logical_id
                )
                for key, value in sub.substitutes.items()
            },
        ]
        if len(sub.substitutes) > 0
        else sub.format_string
    }
