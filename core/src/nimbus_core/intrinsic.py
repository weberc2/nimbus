from typing import Any, Callable, Dict, Union

from nimbus_core.attribute import Attribute
from nimbus_core.parameter import Parameter
from nimbus_core.resource import Resource
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class IntrinsicFunction(Protocol):
    def intrinsic_to_cloudformation(
        self,
        resource_logical_id: Callable[[Resource], str],
        parameter_logical_id: Callable[[Parameter], str],
    ) -> Dict[str, Any]:
        ...


Substitutable = Union[Resource, "PropertyString", Attribute, Parameter]


class Sub:
    def __init__(self, format_string: str, **substitutes: Substitutable) -> None:
        self.format_string = format_string
        self.substitutes = dict(substitutes)
