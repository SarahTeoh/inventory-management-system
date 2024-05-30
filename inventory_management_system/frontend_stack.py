from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as bucket_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    RemovalPolicy,
)
from constructs import Construct
from inventory_management_system.data_model.dynamodb_data_model import CategoryEnum


class FrontendStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "InventoryManagementSystemFrontendBucket",
            bucket_name="inventory-management-system-frontend-bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        distribution = self.create_cloudfront_distribution(bucket)

        #  Deploy with cache invalidation
        bucket_deployment.BucketDeployment(
            self,
            "InventoryManagementSystemFrontendBucketDeployment",
            destination_bucket=bucket,
            sources=[bucket_deployment.Source.asset("./frontend-react/dist")],
            distribution=distribution,
            distribution_paths=["/*"],
        )

    def create_cloudfront_distribution(self, s3_bucket: s3.Bucket) -> None:
        frontend_cloudfront_oac = cloudfront.OriginAccessIdentity(
            self, "FrontendCloudfrontOriginAccessIdentity"
        )
        s3_bucket.grant_read(frontend_cloudfront_oac)

        return cloudfront.Distribution(
            self,
            "InventoryManagementSystemFrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(s3_bucket),
            ),
            default_root_object="index.html",
        )
