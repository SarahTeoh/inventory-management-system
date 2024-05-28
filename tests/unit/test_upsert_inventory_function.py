import os
import json
import uuid
from decimal import Decimal
from unittest.mock import patch
import pytest
from moto import mock_aws
import boto3
from datetime import datetime

from lambdas.upsertInventoryFunction import handler


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
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        os.environ["DB_TABLE_NAME"] = table_name
        yield table_name


def test_handler_create_item(dynamodb_mock):
    test_uuid = str(uuid.uuid4())
    test_datetime = "2024-01-01T00:00:00.000055"

    with patch("uuid.uuid4", return_value=test_uuid), patch(
        "lambdas.upsertInventoryFunction.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime.fromisoformat(test_datetime)

        event = {
            "body": json.dumps(
                {"name": "new_item", "category": "test_category", "price": 123.5}
            )
        }

        response = handler(event, None)

    body = json.loads(response["body"])
    assert body["id"] == test_uuid

    # # Verify item was correctly created in DynamoDB
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(dynamodb_mock)
    result = table.get_item(Key={"name": "new_item", "category": "test_category"})
    item = result.get("Item")
    assert item is not None
    assert item["price"] == Decimal("123.5")
    assert item["static_pk"] == "PRODUCT"
    assert item["last_updated_dt"] == test_datetime
    assert item["id"] == test_uuid


def test_handler_update_item(dynamodb_mock):
    test_uuid = str(uuid.uuid4())
    test_datetime = "2024-01-01T00:00:00.000055"

    with patch("uuid.uuid4", return_value=test_uuid), patch(
        "lambdas.upsertInventoryFunction.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime.fromisoformat(test_datetime)

        # Pre-insert an item into the table(price=100.00)
        table = boto3.resource("dynamodb").Table(dynamodb_mock)
        table.put_item(
            Item={
                "name": "test_product",
                "category": "test_category",
                "price": Decimal("100.00"),
                "static_pk": "PRODUCT",
                "last_updated_dt": "2023-01-01T00:00:00.000055",
                "id": test_uuid,
            }
        )

        event = {
            "body": json.dumps(
                {"name": "test_product", "category": "test_category", "price": 123.7}
            )
        }

        response = handler(event, None)

        body = json.loads(response["body"])
        assert body["id"] == test_uuid

        # Verify item was correctly updated in DynamoDB
        result = table.get_item(
            Key={"name": "test_product", "category": "test_category"}
        )
        item = result.get("Item")
        assert item is not None
        assert item["price"] == Decimal("123.7")
        assert item["static_pk"] == "PRODUCT"
        assert item["last_updated_dt"] == test_datetime
        assert item["id"] == test_uuid


def test_handler_missing_name_parameter():
    event = {"body": json.dumps({"category": "test_category", "price": 123.45})}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing required field(s): name"


def test_handler_missing_category_parameter():
    event = {"body": json.dumps({"name": "test_product", "price": 123.45})}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing required field(s): category"


def test_handler_missing_price_parameter():
    event = {"body": json.dumps({"name": "test_product", "category": "test_category"})}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing required field(s): price"
