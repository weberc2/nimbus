from typing import Any, Dict

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class IntrinsicFunction(Protocol):
    def intrinsic_to_cloudformation(self) -> Dict[str, Any]:
        ...


class Sub:
    def __init__(self, format_string: str, **substitutes: Any) -> None:
        self.format_string = format_string
        self.substitutes = dict(substitutes)

    def intrinsic_to_cloudformation(self) -> Dict[str, Any]:
        return {
            "Fn::Sub": [self.format_string, self.substitutes]
            if len(self.substitutes) > 0
            else self.format_string
        }
