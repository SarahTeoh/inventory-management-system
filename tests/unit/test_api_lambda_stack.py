import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template
from inventory_management_system.api_lambda_stack import ApiLambdaStack

from inventory_management_system.dynamodb_stack import (
    DynamoDbStack,
)
from inventory_management_system.data_model.dynamodb_data_model import (
    DynamoDbTableModel,
    global_secondary_indexes,
    create_db_attribute,
)


@pytest.fixture
def api_lambda_stack():
    app = cdk.App()

    table_model = DynamoDbTableModel(
        table_name="InventoryTestTable",
        partition_key=create_db_attribute(name="name"),
        sort_key=create_db_attribute(name="category"),
        global_secondary_indexes=global_secondary_indexes,
    )

    # Create the DynamoDbStack that ApiLambdaStack will refer
    dynamodb_stack = DynamoDbStack(
        app, "DynamoDbTestStack", dynamodb_data_model=table_model
    )

    # Create the ApiLambdaStack
    api_lambda_stack = ApiLambdaStack(
        app, "ApiLambdaTestStack", dynamodb_table=dynamodb_stack.inventory_table
    )

    return api_lambda_stack


@pytest.fixture
def template(api_lambda_stack):
    # synthesized template
    return Template.from_stack(api_lambda_stack)


def test_lambda_functions_created(template):
    # Assert that upsertInventoryFunction created
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "upsertInventoryFunction.handler",
            "Runtime": "python3.12",
        },
    )

    # Assert that filterInventoryByDateRangeFunctionFunction created
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "filterInventoryByDateRangeFunction.handler",
            "Runtime": "python3.12",
        },
    )


def test_api_created(template):
    # Assert that API created
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Api",
        {"Name": "InventoryApi", "ProtocolType": "HTTP"},
    )

    # Assert that upsert route and integration created
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {"RouteKey": "POST /inventories"},
    )

    # Assert that filterByDateRange route and integration created
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {"RouteKey": "GET /inventories/filterByDateRange"},
    )
