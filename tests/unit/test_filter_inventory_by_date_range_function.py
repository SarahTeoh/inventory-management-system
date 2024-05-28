import os
import json
import uuid
from decimal import Decimal
import pytest
from moto import mock_aws
import boto3

from lambdas.filterInventoryByDateRangeFunction import handler


@pytest.fixture
def dynamodb_mock():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table_name = "TestTable"
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "name", "KeyType": "HASH"},
                {"AttributeName": "category", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "name", "AttributeType": "S"},
                {"AttributeName": "category", "AttributeType": "S"},
                {"AttributeName": "static_pk", "AttributeType": "S"},
                {"AttributeName": "last_updated_dt", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "ItemsLastUpdatedDtIndex",
                    "KeySchema": [
                        {"AttributeName": "static_pk", "KeyType": "HASH"},
                        {"AttributeName": "last_updated_dt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                }
            ],
        )
        os.environ["DB_TABLE_NAME"] = table_name
        yield table_name


def test_handler_filter_within_range(dynamodb_mock):
    # Pre-insert an item into the table(last_updated_dt = 1 feb, 2 feb, 3 march, 4 march)
    table = boto3.resource("dynamodb").Table(dynamodb_mock)
    table.put_item(
        Item={
            "name": "feb_one_product",
            "category": "feb_one_category",
            "price": Decimal("100.00"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-02-01T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )
    table.put_item(
        Item={
            "name": "target_product_1",
            "category": "target_category",
            "price": Decimal("90.00"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-02-02T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )
    table.put_item(
        Item={
            "name": "target_product_2",
            "category": "target_category",
            "price": Decimal("10.00"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-03-03T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )
    table.put_item(
        Item={
            "name": "march_four_product",
            "category": "march_four_category",
            "price": Decimal("10.00"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-03-04T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )

    event = {
        "queryStringParameters": {
            "dt_from": "2023-02-02 00:00:00",
            "dt_to": "2023-03-03 05:00:00",
        }
    }

    response = handler(event, None)

    body = response["body"]
    response_items = body["items"]
    filtered_items_names = [item["name"] for item in response_items]

    # Verify item was correctly filtered
    assert len(response_items) == 2
    assert filtered_items_names == ["target_product_1", "target_product_2"]
    assert body["total_price"] == 100.0


def test_handler_missing_parameters():
    event = {"queryStringParameters": {"dt_to": ""}}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing required query parameters 'dt_from' or 'dt_to'"
