from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigatewayv2 as api_gatewayv2,
    aws_dynamodb as dynamodb,
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct


class ApiLambdaStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        dynamodb_table: dynamodb.TableV2,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        lambdas = self.create_lambda_functions(dynamodb_table)
        self.create_api_gw(lambdas=lambdas)

    def create_api_gw(self, lambdas: list) -> None:
        inventory_api = api_gatewayv2.HttpApi(self, "InventoryApi")

        upsert_inventory_integration = HttpLambdaIntegration(
            "UpsertInventoryIntegration", lambdas["upsert_inventory_fn"]
        )

        inventory_api.add_routes(
            path="/inventories",
            methods=[api_gatewayv2.HttpMethod.POST],
            integration=upsert_inventory_integration,
        )

    def create_lambda_functions(
        self,
        dynamodb_table: dynamodb.TableV2,
    ) -> dict[str, _lambda.Function]:
        # Backend Task 1: Upsert item
        upsert_inventory_fn = _lambda.Function(
            self,
            "upsertInventoryFunction",
            function_name="upsertInventoryFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambdas"),
            handler="upsertInventoryFunction.handler",
            environment={
                "DB_TABLE_NAME": dynamodb_table.table_name,
            },
        )

        # grant Dynamodb table read and write permission to Lambda
        dynamodb_table.grant_read_write_data(upsert_inventory_fn)

        return {"upsert_inventory_fn": upsert_inventory_fn}
