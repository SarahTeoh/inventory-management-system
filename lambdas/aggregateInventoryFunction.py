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
    """Waits until the specified global secondary index(GSI) to become ACTIVE.

    This function continuously checks the status of the specific GSI
    of a DynamoDB table until it becomes active. It logs a message every 5 seconds
    indicating that it's waiting for the index to backfill.

    Args:
        table: The DynamoDB table object.
        index_name: The name of the GSI to wait for.

    Raises:
        RuntimeError: If the index does not become active within a reasonable time.
    """

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
    """Retrieves and validates the list of valid categories.

    This function returns all accepted categories. It retrieves `CATEGORIES` environment variable containing a list of
    pre-defined categories. It also handle case-insensitive matching (eg: Clothing and clothing will be accepted).

    Returns:
        A list of valid categories.

    Raises:
        ValueError: If the `CATEGORIES` environment variable is not set or cannot be evaluated.
    """
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
    """Queries inventory data for a specific category using a global secondary index.

    This function queries the DynamoDB table's specified global secondary index
    to retrieve inventory data belonging to the provided category. It calculates the
    total price and item count for the category.

    Args:
        table (dynamoDB.table): The DynamoDB table object.
        category (str): The category to query for.
        target_index_name (str): The name of the GSI to use.

    Returns:
        A dictionary containing inventory data for the category:
    """
    response = table.query(
        IndexName=target_index_name,
        KeyConditionExpression=Key("category").eq(category),
    )
    total_price = sum(item["price"] for item in response["Items"])
    return {
        "category": category.capitalize(),
        "total_price": float(total_price),
        "count": len(response["Items"]),
    }


def get_inventory_of_all_categories(table, target_index_name: str):
    """Retrieves inventory data for all valid categories using a global secondary index.

    This function calls `get_inventory_of_category` for each category.
    It also filters the results to include only categories with items (count > 0).

    Args:
        table (dynamoDB.table): The DynamoDB table object.
        target_index_name (str): The name of the global secondary index to use.

    Returns:
        A list of dictionaries containing inventory data for each category with items.
    """
    categories = eval(os.environ.get("CATEGORIES"))
    category_data = [
        get_inventory_of_category(table, category, target_index_name)
        for category in categories
    ]

    return [data for data in category_data if data["count"] > 0]


def handler(event, _):
    """Handles HTTP GET requests to get inventory data by category.

    This Lambda function processes incoming HTTP GET requests with `category` query
    parameters. It retrieves inventory data using the
    specified category or all categories if "all" is provided.

    Args:
        event: The HTTP event dictionary containing the request details:
            - queryStringParameters: A dictionary containing the query parameter:
                - category (str): The category to filter by.

        _: The Lambda context object (not used in this function).

    Returns:
        A dictionary containing the response data:
            - On success:
                - body: A JSON string containing an inventory object with items:
                    - items (list): A list of dictionaries containing inventory data, total_price and count for each category with items.
            - On error:
                - statusCode (int): The HTTP status code (e.g., 400 or 500).
                - body: A JSON string containing the error message.
    """
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
