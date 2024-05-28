import os
import boto3
from boto3.dynamodb.conditions import Key
import logging
import json
import time
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")


def wait_for_index_active(table, index_name: str):
    """Wait for the specified global secondary index to become ACTIVE."""

    def is_index_active(indexes, index_name):
        for index in indexes:
            if index["IndexName"] == index_name:
                return index["IndexStatus"] == "ACTIVE"
        return False

    while True:
        if not table.global_secondary_indexes or not is_index_active(
            indexes=table.global_secondary_indexes, index_name=index_name
        ):
            print("Waiting for index to backfill...")
            time.sleep(5)
            table.reload()
        else:
            break


def get_valid_categories() -> list[str]:
    categories_str = os.environ.get("CATEGORIES")
    first_letter_uppercase_categories = eval(categories_str)
    first_letter_lowercase_categories = [
        category.lower() for category in first_letter_uppercase_categories
    ]
    return (
        first_letter_uppercase_categories
        + first_letter_lowercase_categories
        + ["All", "ALL", "AlL", "ALl", "alL", "aLl", "all"]
    )


def get_inventory_of_category(table, category: str, target_index_name: str):
    response = table.query(
        IndexName=target_index_name,
        KeyConditionExpression=Key("category").eq(category),
    )
    total_price = sum(item["price"] for item in response["Items"])
    return {
        "category": category,
        "total_price": float(total_price),
        "count": len(response["Items"]),
    }


def get_inventory_of_all_categories(table, target_index_name: str):
    valid_categories = get_valid_categories()
    category_data = [
        get_inventory_of_category(table, category, target_index_name)
        for category in valid_categories
    ]

    return [data for data in category_data if data["count"] > 0]


def handler(event, _):
    table = dynamodb.Table(os.environ.get("DB_TABLE_NAME"))
    logging.info(f"## Loaded table: {table.name}")
    try:
        # Extract parameter from event
        query_params = event["queryStringParameters"]
        target_category = query_params.get("category", "")

        logging.info(f"## Received payload: {query_params}")

        # Check if category valid
        valid_categories = get_valid_categories()
        if not target_category or target_category not in valid_categories:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing or invalid category"}),
            }

        # Wait for the global secondary index to become ACTIVE
        target_index_name = "CategoryPriceIndex"
        wait_for_index_active(table=table, index_name=target_index_name)

        # Query Global Secondary Index (CategoryPriceIndex)
        if target_category == "all":
            body = get_inventory_of_all_categories(
                table=table, target_index_name=target_index_name
            )
        else:
            body = [
                get_inventory_of_category(
                    table=table,
                    category=target_category,
                    target_index_name=target_index_name,
                )
            ]

        return {"body": json.dumps({"items": body})}
    except ClientError as err:
        logger.error(
            f"Error {err.response['Error']['Code']}: {err.response['Error']['Message']}"
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"error": err.response["Error"]["Message"]}),
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
    finally:
        logger.info("## AggregateInventoryFunction execution completed")
