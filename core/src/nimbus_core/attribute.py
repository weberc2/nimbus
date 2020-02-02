from typing import Any, Callable, Dict, NamedTuple

from nimbus_core.resource import Resource


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
