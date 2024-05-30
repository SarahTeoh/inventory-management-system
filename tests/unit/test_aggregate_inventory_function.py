import os
import json
import uuid
from decimal import Decimal
import pytest
from moto import mock_aws
from unittest.mock import patch
import boto3

from lambdas.aggregateInventoryFunction import get_valid_categories
from inventory_management_system.data_model.dynamodb_data_model import (
    CategoryEnum,
)
from lambdas.aggregateInventoryFunction import handler


@pytest.fixture
def environment_variable():
    os.environ["CATEGORIES"] = str(CategoryEnum.list())


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
                {"AttributeName": "price", "AttributeType": "N"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "CategoryPriceIndex",
                    "KeySchema": [
                        {"AttributeName": "category", "KeyType": "HASH"},
                        {"AttributeName": "price", "KeyType": "RANGE"},
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


@pytest.fixture
def target_items(dynamodb_mock):
    table = boto3.resource("dynamodb").Table(dynamodb_mock)
    # Pre-insert target item into the table(category = Music)
    table.put_item(
        Item={
            "name": "target_product_1",
            "category": "Music",
            "price": Decimal("90.00"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-02-02T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )
    table.put_item(
        Item={
            "name": "target_product_2",
            "category": "Music",
            "price": Decimal("10.00"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-03-03T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )


@pytest.fixture
def other_items(dynamodb_mock):
    table = boto3.resource("dynamodb").Table(dynamodb_mock)
    # Pre-insert others item into the table(category = Beauty, Electrics)
    table.put_item(
        Item={
            "name": "beauty_product",
            "category": "Beauty",
            "price": Decimal("20"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-02-01T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )
    table.put_item(
        Item={
            "name": "beauty_product_2",
            "category": "Beauty",
            "price": Decimal("40"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-02-01T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )

    table.put_item(
        Item={
            "name": "furniture product",
            "category": "Electrics",
            "price": Decimal("10.00"),
            "static_pk": "PRODUCT",
            "last_updated_dt": "2023-03-04T00:00:00.000055",
            "id": str(uuid.uuid4()),
        }
    )


def test_handler_aggregate_by_all_categories(
    environment_variable, target_items, other_items
):
    event = {
        "queryStringParameters": {
            "category": "all",
        }
    }

    response = handler(event, None)

    body = json.loads(response["body"])
    response_items = body["items"]
    response_items_categories = set([item["category"] for item in response_items])
    category_total_price = {
        "Beauty": 60.00,
        "Electrics": 10.00,
        "Music": 100.00,
    }

    # Verify item was correctly filtered
    assert response_items_categories == set(["Beauty", "Electrics", "Music"])
    assert (
        all(
            [
                category_total_price[item["category"]] == item["total_price"]
                for item in response_items
            ]
        )
        == True
    )


def test_handler_aggregate_by_one_category(
    environment_variable, target_items, other_items
):
    event = {
        "queryStringParameters": {
            "category": "Music",
        }
    }

    response = handler(event, None)

    body = json.loads(response["body"])
    response_items = body["items"]

    # Verify item was correctly filtered
    assert len(response_items) == 1
    assert response_items[0]["category"] == "Music"
    assert response_items[0]["total_price"] == 100.0


def test_handler_invalid_category_parameter():
    event = {"queryStringParameters": {"category": "invalid"}}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing or invalid category"


def test_handler_missing_category_parameter():
    event = {"queryStringParameters": {}}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing or invalid category"


@patch.dict(os.environ, {"CATEGORIES": '["Electronics", "Books"]'})
def test_valid_categories(target_items, other_items):
    """
    Test that the function returns the expected list when CATEGORIES env var is set.
    """
    expected_categories = (
        ["Electronics", "Books"]
        + ["electronics", "books"]
        + ["All", "ALL", "AlL", "ALl", "alL", "aLl", "all"]
    )
    actual_categories = get_valid_categories()
    assert actual_categories, expected_categories


def test_handler_empty_category(environment_variable, target_items, other_items):
    event = {
        "queryStringParameters": {
            "category": "Clothing",
        }
    }

    response = handler(event, None)

    body = json.loads(response["body"])
    response_items = body["items"]

    # Verify item was correctly filtered
    assert len(response_items) == 1
    assert response_items[0]["category"] == "Clothing"
    assert response_items[0]["total_price"] == 0


def test_handler_invalid_category_parameter():
    event = {"queryStringParameters": {"category": "invalid"}}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing or invalid category"


def test_handler_missing_category_parameter():
    event = {"queryStringParameters": {}}

    response = handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Missing or invalid category"
