from typing import Any, Dict, NamedTuple

from nimbus_core.parameter import Parameter, parameter_to_cloudformation
from nimbus_core.resource import Resource


class UnknownResource(Exception):
    pass


class UnknownParameter(Exception):
    pass


class Template(NamedTuple):
    description: str
    parameters: Dict[str, Parameter]
    resources: Dict[str, Resource]

    def resource_logical_id(self, r: Resource) -> str:
        for lid, resource in self.resources:
            if resource == r:
                return lid
        raise UnknownResource(r)

    def parameter_logical_id(self, p: Parameter) -> str:
        for lid, parameter in self.parameters:
            if parameter == p:
                return lid
        raise UnknownParameter(p)

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
                    resource_logical_id=lambda resource: self.parameter_logical_id,
                    parameter_logical_id=self.parameter_logical_id,
                )
                for logical_id, resource in self.resources.items()
            },
        }
