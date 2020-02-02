from typing import Any, Dict, List, NamedTuple, Optional, Union

from typing_extensions import Literal

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
