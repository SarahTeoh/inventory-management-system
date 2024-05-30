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
    """Handles HTTP POST requests to upsert an inventory item.

    This Lambda function processes incoming HTTP POST requests containing a JSON payload
    with details for an inventory item. It will update an existing item's price with the same name and category
    or a new item is created if none exists.

    Args:
        event (dict): The HTTP event containing the request data.
            - body (str): The JSON payload containing the inventory item details:
                - name (str): The name of the item (required).
                - category (str): The category of the item (required).
                - price (decimal): The price of the item (required in int/ decimal format).

        _: The Lambda context object (not used in this function).

    Returns:
        A dictionary containing the response data:
            - On success:
                - body (str): A JSON string containing the ID of the updated/inserted item.
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
        required_fields = {"name", "category", "price"}
        missing_fields = required_fields - set(item.keys())
        if missing_fields:
            error_message = f"Missing required field(s): {', '.join(missing_fields)}"
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_message}),
            }

        # Update or Create with dynamodb update_item()
        now = datetime.now()
        response = table.update_item(
            Key={"name": item["name"], "category": item["category"]},
            UpdateExpression="SET #price=:price, #last_updated_dt=:last_updated_dt, #static_pk=if_not_exists(#static_pk, :static_pk), #id=if_not_exists(#id, :id)",
            ExpressionAttributeNames={
                "#price": "price",
                "#static_pk": "static_pk",
                "#last_updated_dt": "last_updated_dt",
                "#id": "id",
            },
            ExpressionAttributeValues={
                ":price": Decimal(str(item["price"])),
                ":static_pk": "PRODUCT",
                ":last_updated_dt": now.isoformat(),
                ":id": str(uuid.uuid4()),
            },
            ReturnValues="ALL_NEW",
        )
        logging.info(f"## Response: {response}")
        return {"body": json.dumps({"id": response["Attributes"]["id"]})}
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
        logger.info("## UpsertInventoryFunction execution completed")
