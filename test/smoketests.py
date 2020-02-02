import unittest

from nimbus_core import ParameterString, Template
from nimbus_resources.s3.bucket import Bucket


class SmokeTests(unittest.TestCase):
    def test_bucket(self):
        param_bucket_name = ParameterString(
            Description="Bucket name parameter", Default="my-bucket"
        )
        template = Template(
            description="Bucket test template",
            parameters={"BucketName": param_bucket_name},
            resources={"Bucket": Bucket(BucketName=param_bucket_name)},
        )

        self.assertEqual(
            {
                "AWSTemplateFormatVersion": "2010-09-09",
                "Description": "Bucket test template",
                "Parameters": {
                    "BucketName": {
                        "Type": "String",
                        "Description": "Bucket name parameter",
                        "Default": "my-bucket",
                    }
                },
                "Resources": {
                    "Bucket": {
                        "Type": "AWS::S3::Bucket",
                        "Properties": {"BucketName": {"Ref": "BucketName"}},
                    }
                },
            },
            template.template_to_cloudformation(),
        )


if __name__ == "__main__":
    unittest.main()
