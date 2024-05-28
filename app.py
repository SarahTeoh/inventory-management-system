#!/usr/bin/env python3
import os
import aws_cdk as cdk
from inventory_management_system.api_lambda_stack import ApiLambdaStack
from inventory_management_system.dynamodb_stack import DynamoDbStack
from inventory_management_system.data_model.dynamodb_data_model import (
    dynamodb_table_model,
)

app = cdk.App()
dynamo_db_stack = DynamoDbStack(
    app,
    "DynamoDbStack",
    dynamodb_data_model=dynamodb_table_model,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

ApiLambdaStack(
    app,
    "ApiLambdaStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
    dynamodb_table=dynamo_db_stack.inventory_table,
)
app.synth()
