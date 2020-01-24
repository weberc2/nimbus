import typing

from typing import (
    Any,
    Dict,
    List,
    NamedTuple,
    Optional,
    Type,
    TYPE_CHECKING,
    Union,
    Tuple,
)
import unittest

from typing_extensions import Literal, Protocol

from spec import (
    NonPrimitiveListPropertySpec,
    NonPrimitivePropertyType,
    NonPrimitiveScalarPropertySpec,
    PrimitiveScalarPropertySpec,
    PrimitiveType,
    PropertySpec,
    ResourceSpec,
    Specification,
    UpdateType,
)
from cfntypes import Resource, PropertyString, PropertyBoolean, PropertyDouble, PropertyInteger, PropertyJSON, PropertyLong, PropertyTimestamp


def _primitive_type(primitive_type: PrimitiveType) -> Type:
    if primitive_type == PrimitiveType.String:
        return PropertyString
    elif primitive_type == PrimitiveType.Long:
        return PropertyLong
    elif primitive_type == PrimitiveType.Integer:
        return PropertyInteger
    elif primitive_type == PrimitiveType.Double:
        return PropertyDouble
    elif primitive_type == PrimitiveType.Boolean:
        return PropertyBoolean
    elif primitive_type == PrimitiveType.Timestamp:
        return PropertyTimestamp
    elif primitive_type == PrimitiveType.Json:
        return PropertyJSON
    else:
        raise TypeError(f"Invalid PrimitiveType: {primitive_type}")


def _non_primitive_type(non_primitive_type: NonPrimitivePropertyType) -> Type:
    return type(str(non_primitive_type), (), {})


def _make_property_type(spec: PropertySpec) -> Type:
    if isinstance(spec, PrimitiveScalarPropertySpec):
        return _primitive_type(spec.PrimitiveType)
    if isinstance(spec, NonPrimitiveScalarPropertySpec):
        return _non_primitive_type(spec.Type)
    if isinstance(spec, NonPrimitiveListPropertySpec):
        return List[_non_primitive_type(spec.ItemType)]
    raise TypeError(f"Invalid PropertySpec type: {spec}")


def make_resource(name: str, resource: ResourceSpec) -> Resource:
    # Separate the required properties from the optional properties. The
    # first required property is the resource's logical ID.
    required_properties = [("logical_id", str)]
    optional_properties = []
    for property_name, property_spec in resource.Properties.items():
        if property_spec.Required:
            required_properties.append(
                (property_name, _make_property_type(property_spec))
            )
        else:
            optional_properties.append(
                (property_name, Optional[_make_property_type(property_spec)])
            )

    type_ = NamedTuple(
        name,
        # Since optional params will have default values, they must come after
        # the required params in Python.
        required_properties + optional_properties,
    )
    # Create a tuple with a `None` for each optional property.
    type_.__new__.__defaults__ = (None,) * len(optional_properties)
    return type_


class TestMakeResource(unittest.TestCase):
    def test_make_resource__string_property_optional(self):
        # Given a resource with an optional string property
        Bucket = make_resource(
            "Bucket",
            ResourceSpec(
                Documentation="",
                Attributes={},
                Properties={
                    "BucketName": PrimitiveScalarPropertySpec(
                        Documentation="",
                        Required=False,
                        UpdateType=UpdateType.Immutable,
                        PrimitiveType=PrimitiveType.String,
                    )
                },
            ),
        )

        # Make sure the property is correctly annotated as an optional string
        self.assertEqual(Bucket.__annotations__["BucketName"], Optional[PropertyString])

        # Make sure a specified property name is set correctly
        self.assertEqual("foo", Bucket(BucketName="foo").BucketName)

        # Make sure the value is `None` if unspecified
        self.assertIsNone(Bucket().BucketName)


if __name__ == "__main__":
    # unittest.main()

    import json

    contents = ""
    with open("/Users/cweber/Downloads/CloudFormationResourceSpecification.json") as f:
        contents = f.read()
    specification = Specification.from_dict(json.loads(contents))
    Bucket = make_resource("Bucket", specification.ResourceTypes["AWS::S3::Bucket"])
    BucketPolicy = make_resource(
        "BucketPolicy", specification.ResourceTypes["AWS::S3::BucketPolicy"]
    )
    bucket = Bucket(logical_id="MyBucket", BucketName="foo")
    bucket_policy = BucketPolicy(
        logical_id="BucketPolicy", Bucket=bucket, PolicyDocument={}
    )
    print(bucket_policy.Bucket.BucketName)

    # import pdb

    # pdb.set_trace()
