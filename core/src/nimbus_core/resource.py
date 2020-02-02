from typing import Any, Callable, Dict

from nimbus_core.parameter import Parameter
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class Resource(Protocol):
    def resource_to_cloudformation(
        self,
        resource_logical_id: Callable[["Resource"], str],
        parameter_logical_id: Callable[[Parameter], str],
    ) -> Dict[str, Any]:
        ...
