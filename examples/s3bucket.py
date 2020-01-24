import json

from awscfn.iam.managedpolicy import ManagedPolicy
from awscfn.s3.bucket import Bucket
from libcfn.auxilary.template import Template
from libcfn.types import ParameterString

parameter = ParameterString(
    logical_id="BucketName", Description="The name of the bucket"
)
t = Template(
    description="S3 Bucket Template",
    parameters=[parameter],
    resources=[
        Bucket(logical_id="Bucket", BucketName=parameter),
        ManagedPolicy(
            logical_id="BucketPolicy",
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowFullAccessToBucket",
                        "Action": "s3:*",
                        "Effect": "Allow",
                        "Resource": {
                            "Fn::Sub": [
                                "${BucketARN}/*",
                                {"BucketARN": {"Fn::GetAtt": "Bucket.Arn"}},
                            ]
                        },
                    },
                    {
                        "Sid": "AllowUseOfTheKey",
                        "Effect": "Allow",
                        "Action": [
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey",
                        ],
                        "Resource": {
                            "Fn::Sub": "arn:aws:kms:us-east-1:231405699240:key/${KeyID}"
                        },
                    },
                    {
                        "Sid": "AllowAttachmentOfPersistentResources",
                        "Effect": "Allow",
                        "Action": [
                            "kms:CreateGrant",
                            "kms:ListGrants",
                            "kms:RevokeGrant",
                        ],
                        "Resource": {
                            "Fn::Sub": "arn:aws:kms:us-east-1:231405699240:key/${KeyID}"
                        },
                        "Condition": {"Bool": {"kms:GrantIsForAWSResource": True}},
                    },
                ],
            },
        ),
    ],
)
print(json.dumps(t.template_to_cloudformation(), indent=4))
