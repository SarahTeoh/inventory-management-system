import os
import boto3
from boto3.dynamodb.conditions import Key
import logging
import json
import time
from botocore.exceptions import ClientError
import dateutil.parser as parser

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


def filter_unnecessary_attributes(items: list[dict]) -> list[dict]:
    """Filter out unnecessary attributes(static_pk and last_updated_dt)

    Args:
        items (list[dict]): items to filter

    Returns:
        list[dict]: items without static_pk and last_updated_dt attribute
    """
    # Attributes to filter away
    attributes_to_filter = ["static_pk", "last_updated_dt"]

    # Filtered list of items without the above attributes
    return [
        {key: value for key, value in item.items() if key not in attributes_to_filter}
        for item in items
    ]


def handler(event, _):
    """Filter items by date range

    This function filters items in a DynamoDB table based on a date time range(dt_from, dt_to) specified in the query parameters.
    It will return items that fall within the specified date time range and calculate the total price of those items.

    Args:
        event (dict): The API event object that should include a 'queryStringParameters' field with 'dt_from' & 'dt_to' keys,
            representing the start and end of the date time range to filter.
        _ (Any): The second parameter is not used

    Returns:
        dict: filtered items within the specified date range and the total price
            - 'items' (list[dict]): A list of filtered items
            - 'total_price' (float): The total price of all filtered items

    Raises:
        ClientError: If there is an error while querying the DynamoDB table
        Exception: If an unexpected error occurs during execution
    """
    table = dynamodb.Table(os.environ.get("DB_TABLE_NAME"))
    logging.info(f"## Loaded table: {table.name}")
    try:
        # Check if parameters exists and extract from event
        query_params = event["queryStringParameters"]
        dt_from = query_params.get("dt_from", "")
        dt_to = query_params.get("dt_to", "")
        logging.info(f"## Received payload: {query_params}")

        # Check if parameters exists
        if not dt_from or not dt_to:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Missing required query parameters 'dt_from' or 'dt_to'"}
                ),
            }

        # Parse dt_from and dt_to iso format so that can compare with the values in db
        dt_from = parser.parse(dt_from).isoformat()
        dt_to = parser.parse(dt_to).isoformat()

        # Wait for the global secondary index to become ACTIVE
        target_index_name = "ItemsLastUpdatedDtIndex"
        wait_for_index_active(table=table, index_name=target_index_name)

        # Query ItemsLastUpdatedDtIndex Index with partition and sort key
        response = table.query(
            IndexName=target_index_name,
            KeyConditionExpression=Key("static_pk").eq("PRODUCT")
            & Key("last_updated_dt").between(
                dt_from,
                dt_to,
            ),
        )
        # Calculate total price of filtered item
        total_price = sum(item["price"] for item in response["Items"])

        return {
            "body": {
                "items": filter_unnecessary_attributes(response["Items"]),
                "total_price": total_price,
            }
        }
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
        logger.info("## FilterByDateRangeFunction execution completed")
