import aws_cdk as core
import aws_cdk.assertions as assertions

from inventory_management_system.inventory_management_system_stack import InventoryManagementSystemStack

# example tests. To run these tests, uncomment this file along with the example
# resource in inventory_management_system/inventory_management_system_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = InventoryManagementSystemStack(app, "inventory-management-system")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
