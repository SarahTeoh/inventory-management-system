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
    """Builds query parameters for DynamoDB table based on provided filters, sort order, and pagination.

    This function constructs the query parameters dictionary for querying DynamoDB table
    considering filters (name, category, price_range), sorting (field and order), and pagination (limit and page).
    These parameters are optional. For example, you can request only category: 'Clothing' in your POST request.

    If sorting is not specified, the query parameters will be built such that the records will be sorted by
    last_udpated_dt in ascending order.

    Args:
        table_name (str): The name of the DynamoDB table to query.
        filters (dict): A dictionary containing optional filters
            - name (str): The name of the item to search for (exact match).
            - category (str): The category of items to filter by. First letter capitalized or lowercased are both accepted.
            - price_range (list): A list of two elements representing the price range (min and max) in integer or decimal format.
        sort (dict): A dictionary containing optional sort criteria:
            - field (str): The field to sort by (eg: "name" or "category").
            - order (str): The sort order ("asc" or "desc").
        pagination: A dictionary containing optional pagination details:
            - limit (int): The maximum number of items to retrieve per page (default: 10).
            - page (int): The specific page number to retrieve (default: 1).

    Returns:
        A dictionary containing the constructed DynamoDB query parameters.
    """
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
        if sort and sort["field"] == "last_updated_dt" and sort["order"] == "desc":
            params["ScanIndexForward"] = False

    params["KeyConditionExpression"] = key_condition
    if filter_expression:
        params["FilterExpression"] = filter_expression

    return params


def handler(event, _):
    """Handles HTTP POST requests to query data.

    This Lambda function processes incoming HTTP POST requests containing a JSON payload
    with filters, sort criteria, and pagination details. It retrieves the corresponding
    items from a DynamoDB table and returns the data paginated. The parameters in payload are optional.
    For example, you can request only with only filters, or only sort criteria.

    Args:
        event (dict): The HTTP event containing the request data.
            - body (str): The JSON payload containing filters, sort, and pagination information.
        _: The Lambda context object (not used in this function).

    Returns:
        - On success:
            - If pagination is specified in request payload (eg: `page: 1`):
                - A dictionary containing these:
                    - items (list): A list of matching items for the requested page.
                    - count (int): The total number of items matching the filters in the page.
                    - page (int): The requested page number (if applicable).
                    - limit (int): The number of items per page.
            - If pagination is NOT specified:
                - A list of dictionaries consisting of all matching items. eg: [{item 1 attributes & vals}, {item 2 attributes & vals}, ...]
        - On error:
            - statusCode (int): The HTTP status code (e.g., 500).
            - body (str): A JSON string containing the error message.
    """
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

        # Build query parameters based on optional filters, sort and pagination parameters
        dynamodb_query_params = build_dynamodb_query_params(
            table.name, filters, sort, pagination
        )

        # data is a dictionary to return only a list of items of a specific page if page is specified
        data = {}
        # combined_list is a list that consists of all queried items
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

            # If no LastEvaluatedKey means no more items to retrieve
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
