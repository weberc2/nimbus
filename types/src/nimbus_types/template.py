from typing import Any, Dict, NamedTuple, List

from libcfn.types import Resource, Parameter, ParameterString

from awscfn.s3.bucket import Bucket
from awscfn.iam.managedpolicy import ManagedPolicy


def parameter_to_cloudformation(parameter: Parameter) -> Dict[str, Any]:
    output = {"Type": parameter.Type}
    if parameter.Description is not None:
        output["Description"] = parameter.Description
    if parameter.Default is not None:
        output["Default"] = parameter.Default
    if parameter.NoEcho is not None:
        output["NoEcho"] = parameter.NoEcho
    return output


class Template(NamedTuple):
    description: str
    parameters: List[Parameter]
    resources: List[Resource]

    def template_to_cloudformation(self) -> Dict[str, Any]:
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": self.description,
            "Parameters": {
                parameter.logical_id: parameter_to_cloudformation(parameter)
                for parameter in self.parameters
            },
            "Resources": {
                resource.logical_id: resource.resource_to_cloudformation()
                for resource in self.resources
            },
        }
