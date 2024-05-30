from decimal import Decimal
import os
import uuid
import boto3
import logging
import json
from botocore.exceptions import ClientError
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")


def handler(event, _):
    """Handles HTTP POST requests to delete an inventory item.

    This Lambda function processes incoming HTTP POST requests containing a JSON payload
    with name and category of the inventory to delete.

    Args:
        event (dict): The HTTP event containing the request data.
            - body (str): The JSON payload containing the inventory item details:
                - name (str): The name of the item (required).
                - category (str): The category of the item (required).

        _: The Lambda context object (not used in this function).

    Returns:
        A dictionary containing the response data:
            - On success:
                - body (str): A string saying delete was successful.
            - On error:
                - statusCode (int): The HTTP status code.
                - body (str): A JSON string containing the error message.
    """
    table = dynamodb.Table(os.environ.get("DB_TABLE_NAME"))
    logging.info(f"## Loaded table: {table.name}")
    try:
        item = json.loads(event["body"])
        logging.info(f"## Received payload: {item}")

        # Check existence of required fields
        required_fields = {"name", "category"}
        missing_fields = required_fields - set(item.keys())
        if missing_fields:
            error_message = f"Missing required field(s): {', '.join(missing_fields)}"
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_message}),
            }

        # Delete item with same name and category(unique)
        response = table.delete_item(
            Key={"name": item["name"], "category": item["category"]}
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"{item['name']} of {item['category']} category was deleted successfully"
                }
            ),
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
        logger.info("## DeleteInventoryFunction execution completed")
