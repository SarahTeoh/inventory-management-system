import os, json
from decimal import Decimal
import pytest
from moto import mock_aws
import boto3
from datetime import datetime, timedelta

from lambdas.queryInventoryFunction import handler
from inventory_management_system.data_model.dynamodb_data_model import CategoryEnum


@pytest.fixture
def dynamodb_mock():
    with mock_aws():
        table_name = "test-table"
        os.environ["DB_TABLE_NAME"] = table_name
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "name", "KeyType": "HASH"},
                {"AttributeName": "category", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "name", "AttributeType": "S"},
                {"AttributeName": "category", "AttributeType": "S"},
                {"AttributeName": "static_pk", "AttributeType": "S"},
                {"AttributeName": "price", "AttributeType": "N"},
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
                },
                {
                    "IndexName": "CategoryPriceIndex",
                    "KeySchema": [
                        {"AttributeName": "category", "KeyType": "HASH"},
                        {"AttributeName": "price", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "NonKeyAttributes": ["id", "last_updated_dt", "price"],
                        "ProjectionType": "INCLUDE",
                    },
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                },
                {
                    "IndexName": "ItemsPriceIndex",
                    "KeySchema": [
                        {"AttributeName": "static_pk", "KeyType": "HASH"},
                        {"AttributeName": "price", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                },
            ],
        )
        yield table


@pytest.fixture
def mocked_items(dynamodb_mock):
    """Mock test data

    Generates mock data for items in all categories.
    For each category, creates 3 items named 'item 1', 'item 2' and 'item 3'.

    The price of items within a category is set in descending order based on their item ID.
    This means items with a smaller ID (like "item-1") have a higher price than items with a larger ID (like "item-3").
    Price of 'item 1' will be 25, 'item 2' will be 20, 'item 3' will be 15.


    The last_udpated_dt of items within a category is set such that 'item 2' is the latest one,
    and 'item 3' will be the oldest.

    Args:
        dynamodb_mock (moto.MockDynamoDB): A mocked DynamoDB table
    """
    items = []
    categories = CategoryEnum.list()
    for category in categories:
        for i in range(1, 4):
            now = datetime.now()
            last_udpated_dt = now - timedelta(days=i)
            last_udpated_dt_iso = last_udpated_dt.isoformat()

            items.append(
                {
                    "name": f"item {i}",
                    "category": category,
                    "id": f"{category}-item-id-{i}",
                    "price": Decimal(
                        str(30 - i * 5)
                    ),  # item with smaller id has higher price
                    "static_pk": "PRODUCT",
                    "last_updated_dt": (
                        now.isoformat() if i == 2 else last_udpated_dt_iso
                    ),  # items with i=2 is the latest, the one with i=3 will be the oldest
                }
            )

    with mock_aws():
        for item in items:
            dynamodb_mock.put_item(Item=item)
        yield dynamodb_mock


# ----- Test: filter by one parameter only  ----- #
def test_handler_by_category_only(mocked_items):
    """
    Note: As we created 3 items for every category during mocking,
    returned item count should be 3
    """
    target_category = "Music"
    query_params = {"filters": {"category": target_category}, "pagination": {"page": 1}}
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_items = response["items"]
    returned_items_categories = set([item["category"] for item in returned_items])
    assert len(returned_items) == 3
    assert returned_items_categories == {target_category}


def test_query_by_name_only(mocked_items):
    """
    Note: As we created an item named 'item 1' for every category during mocking,
    returned item count should be the same with the num of category
    """
    target_name = "item 1"
    query_params = {"filters": {"name": target_name}, "pagination": {"page": 1}}
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_items = response["items"]

    num_of_item_named_item1 = len(CategoryEnum.list())
    returned_items_names = set([item["name"] for item in returned_items])
    assert len(returned_items) == num_of_item_named_item1
    assert returned_items_names == {target_name}


def test_query_by_price_range_only(mocked_items):
    """
    Note: As we created items within a category such that price of 'item 1' is 25,
    'item 2' is 20 and 'item 3' is 15(see documentation of 'mocked_items' fixtures for more details),
    returned item of price_range: [1, 19] should be 'item 3' from each category
    """
    lower_bound = 1
    upper_bound = 19
    query_params = {
        "filters": {"price_range": [lower_bound, upper_bound]},
        "pagination": {"page": 1},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_items = response["items"]

    num_of_item_within_price_range = len(CategoryEnum.list())
    assert len(returned_items) == num_of_item_within_price_range
    assert (
        all(
            lower_bound <= element["price"] <= upper_bound for element in returned_items
        )
        == True
    )


# ----- Test: filter by combination of 2 filter parameters  ----- #
def test_query_by_name_category(mocked_items):
    query_params = {
        "filters": {
            "name": "item 1",
            "category": "Music",
        },
        "pagination": {"page": 1},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_item = response["items"]

    assert len(returned_item) == 1
    assert returned_item[0]["category"] == "Music"


def test_query_by_name_in_price_range(mocked_items):
    """
    Note: As we created items within a category such that price of 'item 1' is 25,
    'item 2' is 20 and 'item 3' is 15(see documentation of 'mocked_items' fixtures for more details),
    returned item of price_range: [1, 30] should be all items from every category,
    but since we filter by name='item 1', we should get only 'item 1' from each category
    """
    lower_bound = 1
    upper_bound = 30
    query_params = {
        "filters": {"name": "item 1", "price_range": [1, 30]},
        "pagination": {"page": 1},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_items = response["items"]

    num_of_item1_within_price_range = len(CategoryEnum.list())
    assert len(returned_items) == num_of_item1_within_price_range
    assert (
        all(
            lower_bound <= element["price"] <= upper_bound for element in returned_items
        )
        == True
    )


def test_query_by_category_in_price_range(mocked_items):
    """
    Note: As we created items within a category such that price of 'item 1' is 25,
    'item 2' is 20 and 'item 3' is 15(see documentation of 'mocked_items' fixtures for more details),
    returned item of price_range: [1, 19] should be all items from every category,
    but since we filter by category='Clothing', we should get only 'item 1' from 'Clothing' category
    """
    lower_bound = 1
    upper_bound = 19
    target_category = "Clothing"
    query_params = {
        "filters": {
            "category": target_category,
            "price_range": [lower_bound, upper_bound],
        },
        "pagination": {"page": 1},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_items = response["items"]

    num_of_clothing_item_within_price_range = 1
    returned_items_categories = set([item["category"] for item in returned_items])
    assert len(returned_items) == num_of_clothing_item_within_price_range
    assert returned_items_categories == {target_category}
    assert (
        all(
            lower_bound <= element["price"] <= upper_bound for element in returned_items
        )
        == True
    )


# ----- Test: filter by combination of 3 filter parameters  ----- #
def test_query_by_name_category_in_price_range(mocked_items):
    """
    Note: since combination of name and category(primary key of our dynamodb table) is unique,
    we should only get 1 item returned.
    """
    lower_bound = 1
    upper_bound = 30
    target_category = "Clothing"
    query_params = {
        "filters": {
            "name": "item 1",
            "category": target_category,
            "price_range": [lower_bound, upper_bound],
        },
        "pagination": {"page": 1},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_items = response["items"]
    assert len(returned_items) == 1
    assert (
        all(
            lower_bound <= element["price"] <= upper_bound for element in returned_items
        )
        == True
    )


# ----- Test: filter by combination of 3 filter parameters pagination  ----- #
def test_query_by_pagination_limit(mocked_items):
    """
    Note: since combination of name and category(primary key of our dynamodb table) is unique,
    we should only get 1 item returned.
    """
    lower_bound = 1
    upper_bound = 30
    target_category = "Clothing"
    query_params = {
        "filters": {
            "category": target_category,
            "price_range": [lower_bound, upper_bound],
        },
        "pagination": {"page": 2, "limit": 1},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    returned_items = response["items"]
    assert len(returned_items) == 1
    assert response["page"] == 2


# ----- Test: sorting  ----- #
def test_sort_query(mocked_items):
    """
    Note: During mocking, we created items within a category such that 'item 1' has the highest price,
    and 'item 3' has the lowest. (see documentation of 'mocked_items' fixtures for more details),
    So the returned items should be in order of 'item 1', 'item 2', 'item 3'
    """
    query_params = {
        "filters": {"category": "Clothing"},
        "sort": {"field": "price", "order": "desc"},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    item_name_sorted_by_last_updated_dt = ["item 1", "item 2", "item 3"]
    returned_item_name_list = [item["name"] for item in response]
    assert item_name_sorted_by_last_updated_dt == returned_item_name_list


def test_sort_by_last_updated_dt_asc_by_default(mocked_items):
    """
    Note: During mocking, we created items within a category such that 'item 2' has the latest last_updated_dt,
    and 'item 3' is the oldest. (see documentation of 'mocked_items' fixtures for more details),
    So the returned items should be in order of 'item 3', 'item 2', 'item 1'
    """
    query_params = {
        "filters": {"category": "Clothing"},
    }
    event = {"body": json.dumps(query_params)}
    response = handler(event, None)

    item_name_sorted_by_last_updated_dt = ["item 3", "item 2", "item 1"]
    returned_item_name_list = [item["name"] for item in response]
    assert item_name_sorted_by_last_updated_dt == returned_item_name_list


# ----- Test: other tests  ----- #
def test_query_with_no_filters(mocked_items):
    event = {
        "body": json.dumps(
            {
                "pagination": {"page": 1, "limit": 40},
                "sort": {"field": "price", "order": "asc"},
            }
        )
    }
    response = handler(event, None)
    assert len(response["items"]) == len(CategoryEnum.list()) * 3


def test_return_in_list_if_no_pagination(mocked_items):
    """
    Note: should return list of items with no pagination
    """
    event = {
        "body": json.dumps(
            {
                "sort": {"field": "price", "order": "asc"},
            }
        )
    }
    response = handler(event, None)
    assert len(response) == len(CategoryEnum.list()) * 3
