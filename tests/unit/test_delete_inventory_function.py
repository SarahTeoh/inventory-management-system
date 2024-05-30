import os
import json
import pytest
from moto import mock_aws
import boto3
from unittest.mock import patch
from botocore.exceptions import ClientError

from lambdas.deleteInventoryFunction import handler


@pytest.fixture
def dynamodb_mock():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table_name = "TestTable"
        table = dynamodb.create_table(
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
        # Insert an object to be deleted
        table.put_item(Item={"name": "Laptop", "category": "Electrics"})
        os.environ["DB_TABLE_NAME"] = table_name
        yield table_name


def test_missing_name(dynamodb_mock):
    event = {"body": json.dumps({"category": "Electronics"})}
    response = handler(event, None)

    assert response["statusCode"] == 400
    # print(f"response body: {response["body"]}")
    assert "Missing required field(s): name" in response["body"]


def test_successful_deletion(dynamodb_mock):

    event = {"body": json.dumps({"name": "Laptop", "category": "Electrics"})}
    response = handler(event, None)

    assert response["statusCode"] == 200
    assert "Laptop of Electrics category was deleted successfully" in response["body"]


@patch("lambdas.deleteInventoryFunction.dynamodb.Table")
def test_client_error(mock_table):
    mock_table().delete_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "The conditional request failed",
            }
        },
        "DeleteItem",
    )
    event = {"body": json.dumps({"name": "Laptop", "category": "Electronics"})}
    response = handler(event, None)

    assert response["statusCode"] == 500
    assert "The conditional request failed" in response["body"]


@patch("lambdas.deleteInventoryFunction.dynamodb.Table")
def test_client_error(mock_table):
    mock_table().delete_item.side_effect = Exception("Something went wrong")
    event = {"body": json.dumps({"name": "Laptop", "category": "Electronics"})}
    response = handler(event, None)

    assert response["statusCode"] == 500
    assert "Something went wrong" in response["body"]
