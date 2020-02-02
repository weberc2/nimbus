from typing import Any, Callable, Dict, NamedTuple

from nimbus_core.parameter import Parameter
from nimbus_core.property import PropertyString
from nimbus_core.reference import property_string_reference
from nimbus_core.resource import Resource


class Tag(NamedTuple):
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
