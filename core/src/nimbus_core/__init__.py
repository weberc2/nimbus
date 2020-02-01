from datetime import datetime
import typing
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union

from typing_extensions import Literal, Protocol, runtime_checkable


@runtime_checkable
class Resource(Protocol):
    def resource_to_cloudformation(
        self,
        resource_logical_id: Callable[["Resource"], str],
        parameter_logical_id: Callable[["Parameter"], str],
    ) -> Dict[str, Any]:
        ...


# Parameters
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
# NOTE: Distinct types of parameters for better type-checking support (can't
# pass a number param into a PropertyString)). All parameters must have the same
# fields.
# TODO: Override __hash__ for the same reason as __eq__?


class ParameterString(NamedTuple):
    Type: Literal["String"] = "String"
    Description: Optional[str] = None
    Default: Optional[str] = None
    NoEcho: bool = False

    def __eq__(self, other: object) -> bool:
        """Compare a Parameter with another object.

        NOTE: Parameters must use identity to compare, so two
        Parameters don't compare to be the same parameter. This is important
        because when the template rendering step encounters a parameter
        value, it looks up the parameter name in the template's `parameters`
        dict, returning the first parameter name that matches the parameter
        value. If we use value comparison instead of identity comparison,
        then we are very likely to accidentally substitute the wrong
        parameter name, especially in cases where two or more parameters are
        instantiated with default values.
        """
        return id(self) == id(other)


class ParameterNumber(NamedTuple):
    Type: Literal["Number"] = "Number"
    Description: Optional[str] = None
    Default: Optional[Union[int, float]] = None
    NoEcho: bool = False

    def __eq__(self, other: object) -> bool:
        """Compare a Parameter with another object.

        NOTE: Parameters must use identity to compare, so two
        Parameters don't compare to be the same parameter. This is important
        because when the template rendering step encounters a parameter
        value, it looks up the parameter name in the template's `parameters`
        dict, returning the first parameter name that matches the parameter
        value. If we use value comparison instead of identity comparison,
        then we are very likely to accidentally substitute the wrong
        parameter name, especially in cases where two or more parameters are
        instantiated with default values.
        """
        return id(self) == id(other)


class ParameterNumberList(NamedTuple):
    Type: Literal["List<Number>"] = "List<Number>"
    Description: Optional[str] = None
    Default: Optional[List[Union[int, float]]] = None
    NoEcho: bool = False

    def __eq__(self, other: object) -> bool:
        """Compare a Parameter with another object.

        NOTE: Parameters must use identity to compare, so two
        Parameters don't compare to be the same parameter. This is important
        because when the template rendering step encounters a parameter
        value, it looks up the parameter name in the template's `parameters`
        dict, returning the first parameter name that matches the parameter
        value. If we use value comparison instead of identity comparison,
        then we are very likely to accidentally substitute the wrong
        parameter name, especially in cases where two or more parameters are
        instantiated with default values.
        """
        return id(self) == id(other)


class ParameterCommaDelineatedList(NamedTuple):
    Type: Literal["CommaDelineatedList"] = "CommaDelineatedList"
    Description: Optional[str] = None
    Default: Optional[List[str]] = None
    NoEcho: bool = False

    def __eq__(self, other: object) -> bool:
        """Compare a Parameter with another object.

        NOTE: Parameters must use identity to compare, so two
        Parameters don't compare to be the same parameter. This is important
        because when the template rendering step encounters a parameter
        value, it looks up the parameter name in the template's `parameters`
        dict, returning the first parameter name that matches the parameter
        value. If we use value comparison instead of identity comparison,
        then we are very likely to accidentally substitute the wrong
        parameter name, especially in cases where two or more parameters are
        instantiated with default values.
        """
        return id(self) == id(other)


PARAMETER_TYPES = (
    ParameterString,
    ParameterNumber,
    ParameterNumberList,
    ParameterCommaDelineatedList,
)
Parameter = Union[
    ParameterString, ParameterNumber, ParameterNumberList, ParameterCommaDelineatedList
]


def parameter_to_cloudformation(parameter: Parameter) -> Dict[str, Any]:
    output: Dict[str, Any] = {"Type": parameter.Type}
    if parameter.Description is not None:
        output["Description"] = parameter.Description
    if parameter.Default is not None:
        output["Default"] = parameter.Default
    if parameter.NoEcho:
        output["NoEcho"] = parameter.NoEcho
    return output


class Attribute(NamedTuple):
    resource: Resource
    attribute_name: str

    def attribute_to_cloudformation(
        self, resource_logical_id=Callable[[Resource], str]
    ) -> Dict[str, Any]:
        return {
            "Fn::GetAtt": f"{resource_logical_id(self.resource)}.{self.attribute_name}"
        }


class AttributeString(Attribute):
    pass


class AttributeLong(Attribute):
    pass


class AttributeInteger(Attribute):
    pass


class AttributeDouble(Attribute):
    pass


class AttributeBoolean(Attribute):
    pass


class AttributeTimestamp(Attribute):
    pass


class AttributeJSON(Attribute):
    pass


def _ref(logical_id: str) -> Dict[str, Any]:
    return {"Ref": logical_id}


@runtime_checkable
class IntrinsicFunction(Protocol):
    def intrinsic_to_cloudformation(
        self,
        resource_logical_id: Callable[[Resource], str],
        parameter_logical_id: Callable[["Parameter"], str],
    ) -> Dict[str, Any]:
        ...


Substitutable = Union[Resource, "PropertyString", Attribute, Parameter]


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


class Sub:
    def __init__(self, format_string: str, **substitutes: Substitutable) -> None:
        self.format_string = format_string
        self.substitutes = dict(substitutes)

    def intrinsic_to_cloudformation(
        self,
        resource_logical_id: Callable[[Resource], str],
        parameter_logical_id: Callable[[Parameter], str],
    ) -> Dict[str, Any]:
        return {
            "Fn::Sub": [
                self.format_string,
                {
                    key: substitutable_to_cloudformation(
                        value, resource_logical_id, parameter_logical_id
                    )
                    for key, value in self.substitutes.items()
                },
            ]
            if len(self.substitutes) > 0
            else self.format_string
        }


PROPERTY_STRING_TYPES = (str, AttributeString, ParameterString, Sub, Resource)
PropertyString = Union[str, AttributeString, ParameterString, "Sub", Resource]


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
        return property_string.intrinsic_to_cloudformation(
            resource_logical_id, parameter_logical_id
        )
    if isinstance(property_string, Resource):
        return _ref(resource_logical_id(property_string))
    if isinstance(property_string, AttributeString):
        return property_string.attribute_to_cloudformation(resource_logical_id)
    raise TypeError(
        f"Invalid PropertyString: {property_string} ({type(property_string)})"
    )


PROPERTY_LONG_TYPES = (int, AttributeLong, ParameterNumber)
PropertyLong = Union[int, AttributeLong, ParameterNumber]


def property_long_reference(
    property_long: PropertyLong, parameter_logical_id: Callable[[Parameter], str]
) -> Union[int, Dict[str, Any]]:
    if isinstance(property_long, int):
        return property_long
    if isinstance(property_long, ParameterNumber):
        return _ref(parameter_logical_id(property_long))
    # TODO: handle AttributeLong
    raise TypeError(f"Invalid PropertyLong: {property_long} ({type(property_long)})")


PROPERTY_INTEGER_TYPES = (int, AttributeInteger, ParameterNumber)
PropertyInteger = Union[int, AttributeInteger, ParameterNumber]


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


PROPERTY_DOUBLE_TYPES = (float, AttributeDouble, ParameterNumber)
PropertyDouble = Union[float, AttributeDouble, ParameterNumber]


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


PROPERTY_BOOLEAN_TYPES = (bool, AttributeBoolean, ParameterString)
PropertyBoolean = Union[bool, AttributeBoolean, ParameterString]


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


PROPERTY_TIMESTAMP_TYPES = (datetime, AttributeTimestamp, ParameterString)
PropertyTimestamp = Union[datetime, AttributeTimestamp, ParameterString]


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


PropertyJSON = Dict[str, Any]


class JSONSerializationErr(Exception):
    pass


def property_json_reference(
    property_json: PropertyJSON,
    resource_logical_id: typing.Callable[[Resource], str],
    parameter_logical_id: typing.Callable[[Parameter], str],
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


class Tag(typing.NamedTuple):
    Key: PropertyString
    Value: PropertyString

    def reference(
        self,
        resource_logical_id: Callable[[Resource], str],
        parameter_logical_id: Callable[[Parameter], str],
    ) -> Dict[str, Any]:
        return {
            "Key": self.Key,
            "Value": property_string_reference(
                self.Value, resource_logical_id, parameter_logical_id
            ),
        }


class Template(NamedTuple):
    description: str
    parameters: Dict[str, Parameter]
    resources: Dict[str, Resource]

    def template_to_cloudformation(self) -> Dict[str, Any]:
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": self.description,
            "Parameters": {
                logical_id: parameter_to_cloudformation(parameter)
                for logical_id, parameter in self.parameters.items()
            },
            "Resources": {
                logical_id: resource.resource_to_cloudformation(
                    resource_logical_id=lambda resource: next(
                        lid for lid, r in self.resources.items() if r == resource
                    ),
                    parameter_logical_id=lambda parameter: next(
                        lid for lid, p in self.parameters.items() if p == parameter
                    ),
                )
                for logical_id, resource in self.resources.items()
            },
        }
