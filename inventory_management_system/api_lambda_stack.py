from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigatewayv2 as api_gatewayv2,
    aws_dynamodb as dynamodb,
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct
from inventory_management_system.data_model.dynamodb_data_model import (
    CategoryEnum,
)


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
        lambdas = self.create_lambda_functions(dynamodb_table=dynamodb_table)
        self.create_api_gw(lambdas=lambdas)

    def add_route(
        self,
        api: api_gatewayv2.HttpApi,
        path: str,
        methods: list[api_gatewayv2.HttpMethod],
        lambda_function: _lambda.Function,
        integration_id: str,
    ) -> None:
        """Helper function to add a route to the API Gateway."""
        integration = HttpLambdaIntegration(integration_id, lambda_function)

        api.add_routes(
            path=path,
            methods=methods,
            integration=integration,
        )

    def create_lambda_function_with_dynamodb_access(
        self,
        id: str,
        function_name: str,
        handler: str,
        dynamodb_table: dynamodb.TableV2,
        environment_vars: dict = None,
        read_write_access: bool = False,
    ) -> _lambda.Function:
        """Helper function to create a Lambda function"""
        fn = _lambda.Function(
            self,
            id,
            function_name=function_name,
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambdas"),
            handler=handler,
            environment=environment_vars,
        )

        if read_write_access:
            dynamodb_table.grant_read_write_data(fn)
        else:
            dynamodb_table.grant_read_data(fn)

        return fn

    def create_lambda_functions(
        self,
        dynamodb_table: dynamodb.TableV2,
    ) -> dict[str, _lambda.Function]:
        """Create needed lambda functions for backend tasks"""
        return {
            # Backend Task 1
            "upsert_inventory_fn": self.create_lambda_function_with_dynamodb_access(
                id="upsertInventoryFunction",
                function_name="upsertInventoryFunction",
                handler="upsertInventoryFunction.handler",
                dynamodb_table=dynamodb_table,
                environment_vars={"DB_TABLE_NAME": dynamodb_table.table_name},
                read_write_access=True,
            ),
            # Backend Task 2
            "filter_inventory_by_date_range_fn": self.create_lambda_function_with_dynamodb_access(
                id="filterInventoryByDateRangeFunction",
                function_name="filterInventoryByDateRangeFunction",
                handler="filterInventoryByDateRangeFunction.handler",
                dynamodb_table=dynamodb_table,
                environment_vars={"DB_TABLE_NAME": dynamodb_table.table_name},
            ),
            # Backend Task 3
            "aggregate_inventory_fn": self.create_lambda_function_with_dynamodb_access(
                id="AggregateInventoryFunction",
                function_name="aggregateInventoryFunction",
                handler="aggregateInventoryFunction.handler",
                dynamodb_table=dynamodb_table,
                environment_vars={
                    "DB_TABLE_NAME": dynamodb_table.table_name,
                    "CATEGORIES": str(CategoryEnum.list()),
                },
            ),
            # Backend Task 4
            "query_inventory_fn": self.create_lambda_function_with_dynamodb_access(
                id="QueryInventoryFunction",
                function_name="queryInventoryFunction",
                handler="queryInventoryFunction.handler",
                dynamodb_table=dynamodb_table,
                environment_vars={
                    "DB_TABLE_NAME": dynamodb_table.table_name,
                },
            ),
        }

    def create_api_gw(self, lambdas: list) -> None:
        """Create api routes"""
        inventory_api = api_gatewayv2.HttpApi(self, "InventoryApi")

        # Route for Backend Task 1: Upsert item
        self.add_route(
            api=inventory_api,
            path="/inventory",
            methods=[api_gatewayv2.HttpMethod.POST],
            lambda_function=lambdas["upsert_inventory_fn"],
            integration_id="upsertInventoryFunction",
        )

        # Route for Backend Task 2: Filter item by date range
        self.add_route(
            api=inventory_api,
            path="/inventories/filterByDateRange",
            methods=[api_gatewayv2.HttpMethod.GET],
            lambda_function=lambdas["filter_inventory_by_date_range_fn"],
            integration_id="filterInventoryByDateRangeFunction",
        )

        # Route for Backend Task 3: Aggregate item by category
        self.add_route(
            api=inventory_api,
            path="/inventories/aggregate",
            methods=[api_gatewayv2.HttpMethod.GET],
            lambda_function=lambdas["aggregate_inventory_fn"],
            integration_id="AggregateInventoryFunction",
        )

        # Route for Backend Task 4: Handle Filters, Pagination and Sorting Options
        self.add_route(
            api=inventory_api,
            path="/inventories",
            methods=[api_gatewayv2.HttpMethod.POST],
            lambda_function=lambdas["query_inventory_fn"],
            integration_id="QueryInventoryFunction",
        )
