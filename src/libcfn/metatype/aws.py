import sys
from typing import Any, Dict
from types import ModuleType
import json

from spec import ResourceSpec
from meta import make_resource


def _spec_dict() -> Dict[str, Any]:
    contents = ""
    with open("/Users/cweber/Downloads/CloudFormationResourceSpecification.json") as f:
        contents = f.read()
    return json.loads(contents)


def _make_module(
    resource_types: Dict[str, Any], modname: str, keypath: str
) -> ModuleType:
    _keypath_prefix = f"{keypath}::"
    m = ModuleType(modname)

    def _getattr(attr):
        keypath_ = f"{keypath}::{attr}"
        resource_spec_dict = resource_types.get(keypath_)
        if resource_spec_dict is not None:
            return make_resource(
                name=attr, resource=ResourceSpec.from_dict(resource_spec_dict)
            )
        for key in resource_types.keys():
            if key.startswith(_keypath_prefix):
                return _make_module(
                    resource_types, modname=attr, keypath=f"{keypath_}::{attr}"
                )
        raise AttributeError(f"module '{modname}' has no attribute '{attr}'")

    # we need to get this outside of the lambda below else infinite recursion.
    dir_ = m.__dir__()
    m.__dir__ = lambda: dir_ + [
        key[len(_keypath_prefix) :]
        for key in resource_types
        if key.startswith(_keypath_prefix)
    ]
    m.__getattr__ = _getattr
    return m


def __getattr__(attr: str):
    return _make_module(
        resource_types=_spec_dict()["ResourceTypes"],
        modname=attr,
        keypath=f"AWS::{attr}",
    )


if __name__ == "__main__":
    s3 = __getattr__("S3")
    bucket = s3.Bucket("Bucket", BucketName="my-bucket")
    bucket_policy = s3.BucketPolicy("BucketPolicy", Bucket=bucket, PolicyDocument={})
    print(bucket_policy.Bucket.BucketName)
