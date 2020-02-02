from datetime import datetime
from typing import Any, Dict, Union

from nimbus_core.attribute import (
    AttributeBoolean,
    AttributeDouble,
    AttributeInteger,
    AttributeLong,
    AttributeString,
    AttributeTimestamp,
)
from nimbus_core.parameter import ParameterNumber, ParameterString
from nimbus_core.resource import Resource
from nimbus_core.intrinsic import Sub

PROPERTY_STRING_TYPES = (str, AttributeString, ParameterString, Sub, Resource)
PropertyString = Union[str, AttributeString, ParameterString, "Sub", Resource]


PROPERTY_LONG_TYPES = (int, AttributeLong, ParameterNumber)
PropertyLong = Union[int, AttributeLong, ParameterNumber]


PROPERTY_INTEGER_TYPES = (int, AttributeInteger, ParameterNumber)
PropertyInteger = Union[int, AttributeInteger, ParameterNumber]


PROPERTY_DOUBLE_TYPES = (float, AttributeDouble, ParameterNumber)
PropertyDouble = Union[float, AttributeDouble, ParameterNumber]


PROPERTY_BOOLEAN_TYPES = (bool, AttributeBoolean, ParameterString)
PropertyBoolean = Union[bool, AttributeBoolean, ParameterString]


PROPERTY_TIMESTAMP_TYPES = (datetime, AttributeTimestamp, ParameterString)
PropertyTimestamp = Union[datetime, AttributeTimestamp, ParameterString]


PropertyJSON = Dict[str, Any]
