import typing
from datetime import datetime
from typing import NamedTuple, Optional, Union, Tuple, List, Dict, Any

from typing_extensions import Literal, Protocol, runtime_checkable


@runtime_checkable
class Resource(Protocol):
    logical_id: str

    def resource_to_cloudformation(self) -> Dict[str, Any]:
        ...


# Parameters
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
# NOTE: Distinct types of parameters for better type-checking support (can't
# pass a number param into a PropertyString)). All parameters must have the same
# fields.


class ParameterString(NamedTuple):
    logical_id: str
    Type: Literal["String"] = "String"
    Description: Optional[str] = None
    Default: Optional[str] = None
    NoEcho: bool = False

    # NOTE: This method is only used for the metaprogramming implementation;
    # should be moved alongside the metaprogramming implementation.
    # NOTE: need to refer to `typing.Type` and not just `Type` because the
    # latter is shadowed by `ParameterString.Type` in this scope. Without
    # this, `Type` would resolve to `"String"`, the default value for
    # `ParameterString.Type`.
    def to_field(self) -> Tuple[str, typing.Type, Optional[str]]:
        return self.logical_id, str, self.Default


class ParameterNumber(NamedTuple):
    logical_id: str
    Type: Literal["Number"] = "Number"
    Description: Optional[str] = None
    Default: Optional[Union[int, float]] = None
    NoEcho: bool = False

    # NOTE: This method is only used for the metaprogramming implementation;
    # should be moved alongside the metaprogramming implementation.
    # NOTE: need to refer to `typing.Type` and not just `Type` because the
    # latter is shadowed by `ParameterNumber.Type` in this scope. Without
    # this, `Type` would resolve to `"Number"`, the default value for
    # `ParameterNumber.Type`.
    def to_field(self) -> Tuple[str, typing.Type, Optional[Union[int, float]]]:
        return self.logical_id, Union[int, float], self.Default


class ParameterNumberList(NamedTuple):
    logical_id: str
    Type: Literal["List<Number>"] = "List<Number>"
    Description: Optional[str] = None
    Default: Optional[List[Union[int, float]]] = None
    NoEcho: bool = False

    # NOTE: This method is only used for the metaprogramming implementation;
    # should be moved alongside the metaprogramming implementation.
    # NOTE: need to refer to `typing.Type` and not just `Type` because the
    # latter is shadowed by `ParameterNumberList.Type` in this scope.
    # Without this, `Type` would resolve to `"List<Number>"`, the default value
    # for `ParameterNumberList.Type`.
    def to_field(self) -> Tuple[str, typing.Type, Optional[List[Union[int, float]]]]:
        return self.logical_id, List[Union[int, float]], self.Default


class ParameterCommaDelineatedList(NamedTuple):
    logical_id: str
    Type: Literal["CommaDelineatedList"] = "CommaDelineatedList"
    Description: Optional[str] = None
    Default: Optional[List[str]] = None
    NoEcho: bool = False

    # NOTE: This method is only used for the metaprogramming implementation;
    # should be moved alongside the metaprogramming implementation.
    # NOTE: need to refer to `typing.Type` and not just `Type` because the
    # latter is shadowed by `ParameterCommaDelineatedList.Type` in this
    # scope. Without this, `Type` would resolve to `"CommaDelineatedList"`, the
    # default value for `ParameterCommaDelineatedList.Type`.
    def to_field(self) -> Tuple[str, typing.Type, Optional[List[str]]]:
        return self.logical_id, List[str], self.Default


PARAMETER_TYPES = (
    ParameterString,
    ParameterNumber,
    ParameterNumberList,
    ParameterCommaDelineatedList,
)
Parameter = Union[
    ParameterString, ParameterNumber, ParameterNumberList, ParameterCommaDelineatedList
]


class Attribute(NamedTuple):
    resource: Resource
    attribute_name: str

    def attribute_to_cloudformation(self) -> Dict[str, Any]:
        return {"Fn::GetAtt": f"{self.resource.logical_id}.{self.attribute_name}"}


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


PropertyString = Union[str, AttributeString, ParameterString, Resource]


def property_string_reference(
    property_string: PropertyString
) -> Union[str, Dict[str, Any]]:
    if isinstance(property_string, str):
        return property_string
    if isinstance(property_string, (ParameterString, Resource)):
        return {"Ref": property_string.logical_id}
    # TODO: handle AttributeString
    raise TypeError(
        f"Invalid PropertyString: {property_string} ({type(property_string)})"
    )


PropertyLong = Union[int, AttributeLong, ParameterNumber]


def property_long_reference(property_long: PropertyLong) -> Union[int, Dict[str, Any]]:
    if isinstance(property_long, int):
        return property_long
    if isinstance(property_long, ParameterNumber):
        return {"Ref": property_long.logical_id}
    # TODO: handle AttributeLong
    raise TypeError(f"Invalid PropertyLong: {property_long} ({type(property_long)})")


PropertyInteger = Union[int, AttributeInteger, ParameterNumber]


def property_integer_reference(
    property_integer: PropertyInteger
) -> Union[int, Dict[str, Any]]:
    if isinstance(property_integer, int):
        return property_integer
    if isinstance(property_integer, ParameterNumber):
        return {"Ref": property_integer.logical_id}
    # TODO: handle AttributeInteger
    raise TypeError(
        f"Invalid PropertyInteger: {property_integer} ({type(property_integer)})"
    )


PropertyDouble = Union[float, AttributeDouble, ParameterNumber]


def property_double_reference(
    property_double: PropertyDouble
) -> Union[float, Dict[str, Any]]:
    if isinstance(property_double, float):
        return property_double
    if isinstance(property_double, ParameterNumber):
        return {"Ref": property_double.logical_id}
    # TODO: handle AttributeDouble
    raise TypeError(
        f"Invalid PropertyDouble: {property_double} ({type(property_double)})"
    )


PropertyBoolean = Union[bool, AttributeBoolean, ParameterString]


def property_boolean_reference(
    property_boolean: PropertyBoolean
) -> Union[bool, Dict[str, Any]]:
    if isinstance(property_boolean, bool):
        return property_boolean
    if isinstance(property_boolean, ParameterString):
        return {"Ref": property_boolean.logical_id}
    # TODO: handle AttributeBoolean
    raise TypeError(
        f"Invalid PropertyBoolean: {property_boolean} ({type(property_boolean)})"
    )


PropertyTimestamp = Union[datetime, AttributeTimestamp, ParameterString]


def property_timestamp_reference(
    property_timestamp: PropertyTimestamp
) -> Union[datetime, Dict[str, Any]]:
    if isinstance(property_timestamp, datetime):
        return property_timestamp
    if isinstance(property_timestamp, ParameterString):
        return {"Ref": property_timestamp.logical_id}
    # TODO: handle AttributeTimestamp
    raise TypeError(
        f"Invalid PropertyTimestamp: {property_timestamp} ({type(property_timestamp)})"
    )


PropertyJSON = Dict[str, Any]


def property_json_reference(property_json: PropertyJSON) -> Dict[str, Any]:
    def _process_value(value: Any) -> Any:
        if isinstance(value, PARAMETER_TYPES):
            return {"Ref": value.logical_id}
        if isinstance(value, Resource):
            return {"Ref": value.logical_id}
        if isinstance(value, dict):
            output = {}
            for k, v in value.items():
                try:
                    output[k] = _process_value(v)
                except TypeError as e:
                    raise TypeError(f"In key {k}: {e}")
            return output
        if isinstance(value, list):
            output = []
            for i, x in enumerate(value):
                try:
                    output.append(_process_value(x))
                except TypeError as e:
                    raise TypeError(f"At index {i}: {e}")
            return output
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        raise TypeError(
            f"{value} (of type {type(value)}) is not a valid JSON node type"
        )

    try:
        return _process_value(property_json)
    except TypeError as e:
        raise TypeError(f"Invalid JSON object: {e}")


class Tag(typing.NamedTuple):
    Key: PropertyString
    Value: PropertyString

    def reference(self) -> Dict[str, Any]:
        return {"Key": self.Key, "Value": property_string_reference(self.Value)}
