import random
import uuid
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    custom_resources,
    aws_iam as iam,
)
from constructs import Construct
from faker import Faker
import faker_commerce
from .data_model.dynamodb_data_model import CategoryEnum, DynamoDbTableModel


class DynamoDbStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        dynamodb_data_model: DynamoDbTableModel,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.table_model = dynamodb_data_model

        self.inventory_table = self.create_table()
        self.populate_table(table=self.inventory_table)

    def create_table(self) -> dynamodb.TableV2:
        """Create a DynamoDB table and its secondary indexes

        This table has read and write capacity of 1 to 3,
        autoscale on 90% utilization percentage

        Returns:
            dynamodb.TableV2: created DynamoDB table
        """
        inventory_table = dynamodb.TableV2(
            self,
            self.table_model.table_name,
            partition_key=self.table_model.partition_key,
            sort_key=self.table_model.sort_key,
            removal_policy=RemovalPolicy.DESTROY,
            billing=dynamodb.Billing.provisioned(
                read_capacity=dynamodb.Capacity.autoscaled(
                    max_capacity=2, target_utilization_percent=90
                ),
                write_capacity=dynamodb.Capacity.autoscaled(
                    max_capacity=2, target_utilization_percent=90
                ),
            ),
        )

        # add secondary index
        self.add_secondary_indexes(inventory_table)
        return inventory_table

    def add_secondary_indexes(self, table: dynamodb.TableV2):
        """Add global secondary indexes.

        Args:
            table (dynamodb.TableV2): dynamodb table to add secondary indexes
        """
        for index in self.table_model.global_secondary_indexes:
            table.add_global_secondary_index(
                index_name=index.index_name,
                partition_key=index.partition_key,
                sort_key=index.sort_key,
                projection_type=index.projection_type,
                non_key_attributes=index.non_key_attributes,
            )

    def generate_fake_data(self) -> dict:
        """Generate a single fake data item

        Returns:
            dict: A dictionary representing a fake data item
        """
        faker = Faker()
        faker.add_provider(faker_commerce.Provider)
        return {
            "id": {"S": str(uuid.uuid4())},
            "name": {"S": faker.ecommerce_name()},
            "category": {"S": random.choice(CategoryEnum.list())},
            "price": {"N": str(round(random.uniform(1, 100), 1))},
            "last_updated_dt": {"S": faker.date_time().isoformat()},
            "static_pk": {"S": "PRODUCT"},
        }

    def generate_batch_fake_data(self, batch_size: int = 20) -> list:
        """Generate a batch of fake data items.

        Args:
            batch_size (int, optional): The number of fake items to generate. Defaults to 20.

        Returns:
            list: A list of dictionaries that represent the fake items
        """
        return [
            {"PutRequest": {"Item": self.generate_fake_data()}}
            for _ in range(batch_size)
        ]

    def populate_table(self, table: dynamodb.TableV2):
        """Initialize table data.

        Args:
            table (dynamodb.TableV2): dynamodb table to populate
        """
        custom_resources.AwsCustomResource(
            self,
            "initializeTableResource",
            on_create=custom_resources.AwsSdkCall(
                action="batchWriteItem",
                service="DynamoDB",
                physical_resource_id=custom_resources.PhysicalResourceId.of(
                    table.table_name + "_initializeTableData"
                ),
                parameters={
                    "RequestItems": {
                        table.table_name: self.generate_batch_fake_data(),
                    }
                },
            ),
            policy=custom_resources.AwsCustomResourcePolicy.from_statements(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["dynamodb:batchWriteItem"],
                        resources=[table.table_arn],
                    )
                ]
            ),
        )
