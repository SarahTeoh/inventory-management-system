from decimal import Decimal
import os, boto3, json, logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")


def build_dynamodb_query_params(
    table_name: str, filters: dict, sort: dict, pagination: dict
):
    name = filters.get("name", "")
    category = filters.get("category", "")
    price_range = filters.get("price_range", [])
    min_price = Decimal(str(price_range[0])) if price_range else None
    max_price = Decimal(str(price_range[1])) if price_range else None
    page_size = int(pagination.get("limit", 10))

    # Initialize dynamodb query parameters
    params = {
        "TableName": table_name,
        "ProjectionExpression": "id, #name, category, price",
        "ExpressionAttributeNames": {"#name": "name"},
        "Limit": page_size,
    }

    key_condition = None
    filter_expression = None

    # Define the key condition expression for the query based on the query params
    if name:
        key_condition = Key("name").eq(name)
        if sort and sort["field"] == "price" and sort["order"] == "desc":
            params["ScanIndexForward"] = False
        if category:
            key_condition &= Key("category").eq(category)
        if min_price and max_price:
            filter_expression = Attr("price").between(min_price, max_price)
    elif category:
        params["IndexName"] = "CategoryPriceIndex"
        key_condition = Key("category").eq(category)
        if sort and sort["field"] == "price" and sort["order"] == "desc":
            params["ScanIndexForward"] = False
        if min_price and max_price:
            key_condition &= Key("price").between(min_price, max_price)
    elif min_price and max_price:
        params["IndexName"] = "ItemsPriceIndex"
        key_condition = Key("static_pk").eq("PRODUCT") & Key("price").between(
            min_price, max_price
        )

    else:
        # If no filters are given, return all items paginated, and sorted by last_updated_dt by default
        params["IndexName"] = "ItemsLastUpdatedDtIndex"
        key_condition = Key("static_pk").eq("PRODUCT")
        if sort and sort["field"] == "price" and sort["order"] == "desc":
            params["ScanIndexForward"] = False

    params["KeyConditionExpression"] = key_condition
    if filter_expression:
        params["FilterExpression"] = filter_expression

    return params


def handler(event, _):
    table = dynamodb.Table(os.environ.get("DB_TABLE_NAME"))
    logging.info(f"## Loaded table name: {table.name}")
    try:
        # Extract parameters from event
        body = json.loads(event["body"])
        logging.info(f"## Received payload: {body}")

        filters = body.get("filters", {})
        pagination = body.get("pagination", {})
        sort = body.get("sort", {})

        # Pagination parameter processing
        page = pagination.get("page", 1)
        page_size = pagination.get("limit", 10)

        dynamodb_query_params = build_dynamodb_query_params(
            table.name, filters, sort, pagination
        )

        data = {}
        combined_items = []
        while True:
            response = table.query(**dynamodb_query_params)

            data[page] = {
                "items": response["Items"],
                "count": response["Count"],
                "page": page,
                "limit": page_size,
            }

            for page_data in response["Items"]:
                combined_items.append(page_data)

            # No LastEvaluatedKey means no more items to retrieve
            if "LastEvaluatedKey" not in response:
                break

            # If there are possibly more items, update the start key for the next page
            dynamodb_query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            page += 1

        """ Only return data of a specific page if page is specified,
        else return all data in a list(For frontend)."""
        return_data = combined_items
        if pagination and "page" in pagination.keys():
            return_data = data[pagination["page"]]

        return return_data
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
        logger.info("## QueryInventoryFunction execution completed")
