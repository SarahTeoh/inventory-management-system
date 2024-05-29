import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template
from inventory_management_system.dynamodb_stack import (
    DynamoDbStack,
)
from inventory_management_system.data_model.dynamodb_data_model import (
    DynamoDbTableModel,
    global_secondary_indexes,
    create_db_attribute,
)


@pytest.fixture
def dynamodb_stack():
    app = cdk.App()

    # Create the dynamodb table model that the DynamoDbStack will reference
    table_model = DynamoDbTableModel(
        table_name="InventoryTestTable",
        partition_key=create_db_attribute(name="name"),
        sort_key=create_db_attribute(name="category"),
        global_secondary_indexes=global_secondary_indexes,
    )

    # Create the DynamoDbStack
    dynamodb_stack = DynamoDbStack(
        app, "DynamoDbStack", dynamodb_data_model=table_model
    )

    return dynamodb_stack


@pytest.fixture
def template(dynamodb_stack):
    # synthesized template
    return Template.from_stack(dynamodb_stack)


def test_dynamodb_table_created(template):
    # Assert that DynamoDb Global Table created
    template.has_resource_properties(
        "AWS::DynamoDB::GlobalTable",
        {
            "BillingMode": "PROVISIONED",
            "AttributeDefinitions": [
                {"AttributeName": "name", "AttributeType": "S"},
                {"AttributeName": "category", "AttributeType": "S"},
                {"AttributeName": "static_pk", "AttributeType": "S"},
                {"AttributeName": "price", "AttributeType": "N"},
                {"AttributeName": "last_updated_dt", "AttributeType": "S"},
            ],
            "KeySchema": [
                {"AttributeName": "name", "KeyType": "HASH"},
                {"AttributeName": "category", "KeyType": "RANGE"},
            ],
            "WriteProvisionedThroughputSettings": {
                "WriteCapacityAutoScalingSettings": {
                    "MaxCapacity": 2,
                    "MinCapacity": 1,
                    "TargetTrackingScalingPolicyConfiguration": {"TargetValue": 90},
                },
            },
        },
    )


def test_dynamodb_global_secondary_indexes(template):
    # Assert that DynamoDb Global Table GSI
    template.has_resource_properties(
        "AWS::DynamoDB::GlobalTable",
        {
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "ItemsPriceIndex",
                    "KeySchema": [
                        {"AttributeName": "static_pk", "KeyType": "HASH"},
                        {"AttributeName": "price", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "CategoryPriceIndex",
                    "KeySchema": [
                        {"AttributeName": "category", "KeyType": "HASH"},
                        {"AttributeName": "price", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": ["id", "last_updated_dt", "name"],
                    },
                },
                {
                    "IndexName": "ItemsLastUpdatedDtIndex",
                    "KeySchema": [
                        {"AttributeName": "static_pk", "KeyType": "HASH"},
                        {"AttributeName": "last_updated_dt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ]
        },
    )
