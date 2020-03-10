import json

from nimbus_resources.iam.managedpolicy import ManagedPolicy
from nimbus_resources.s3.bucket import Bucket
from nimbus_core import ParameterString, Template, Sub


def main():
    bucket_name_parameter = ParameterString(Description="The name of the bucket")
    key_arn_parameter = ParameterString(
        Description="The ARN of the KMS key used to encrypt the bucket",
    )
    bucket = Bucket(BucketName=bucket_name_parameter)
    t = Template(
        description="S3 Bucket Template",
        parameters={
            "BucketName": bucket_name_parameter,
            "KMSKeyARN": key_arn_parameter,
        },
        resources={
            "Bucket": bucket,
            "BucketPolicy": ManagedPolicy(
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowFullAccessToBucket",
                            "Action": "s3:*",
                            "Effect": "Allow",
                            "Resource": Sub(
                                f"${{BucketARN}}/*", BucketARN=bucket.GetArn()
                            ),
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
                            "Resource": key_arn_parameter,
                        },
                        {
                            "Sid": "AllowAttachmentOfPersistentResources",
                            "Effect": "Allow",
                            "Action": [
                                "kms:CreateGrant",
                                "kms:ListGrants",
                                "kms:RevokeGrant",
                            ],
                            "Resource": key_arn_parameter,
                            "Condition": {"Bool": {"kms:GrantIsForAWSResource": True}},
                        },
                    ],
                },
            ),
        },
    )
    print(json.dumps(t.template_to_cloudformation(), indent=4))


if __name__ == "__main__":
    main()
