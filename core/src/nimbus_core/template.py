from typing import Any, Dict, NamedTuple

from nimbus_core.parameter import Parameter, parameter_to_cloudformation
from nimbus_core.resource import Resource


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
