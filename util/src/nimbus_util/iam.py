from typing import List, Union, Optional, Dict

from typing_extensions import TypedDict, Literal

from nimbus_core import PropertyString

# TODO: implement this Grammar:
# https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_grammar.html

# From: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html#Conditions_Numeric
ConditionOperator = Literal[
    "StringEquals",
    "StringNotEquals",
    "StringEqualsIgnoreCase",
    "StringNotEqualsIgnoreCase",
    "StringLike",
    "StringNotLike",
    "NumericEquals",
    "NumericNotEquals",
    "NumericLessThan",
    "NumericLessThanEquals",
    "NumericGreaterThan",
    "NumericGreaterThanEquals",
    # TODO Date operators
    "Bool",
    # TODO Binary operators
    # TODO IP Address operators
    # TODO ARN operators
    # TODO IfExists operator
    # TODO null operator
]


class ConditionMap(
    Dict[
        ConditionOperator,
        Dict[PropertyString, Union[PropertyString, List[PropertyString]]],
    ]
):
    pass


class Statement(TypedDict):
    Sid: str
    Action: Union[str, List[str]]
    Effect: Literal["Allow", "Deny"]
    Resource: PropertyString
    Condition: Optional[ConditionMap]


class PolicyDocument(TypedDict):
    Version: Literal["2008-10-17", "2012-10-17"]
    Statement: List[Statement]
