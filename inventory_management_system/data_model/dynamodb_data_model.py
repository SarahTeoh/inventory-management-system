from enum import Enum
from aws_cdk import aws_dynamodb as dynamodb


class SecondaryIndex:
    """Represents a secondary index of a DynamoDB Table

    Attributes:
        index_name(str): The name of the secondary index
        partition_key(dynamodb.Attribute): The partition key attribute of the index.
        sort_key(dynamodb.Attribute): The sort key attribute of the index.
        projection_type(dynamodb.ProjectionType, optional): The projection type of the index (default(ProjectionType.ALL).
        non_key_attributes(List[str], optional): The list of non-key attributes to include in the index projection (default: None).
    """

    def __init__(
        self,
        index_name: str,
        partition_key: dynamodb.Attribute,
        sort_key: dynamodb.Attribute,
        projection_type: dynamodb.ProjectionType = dynamodb.ProjectionType.ALL,
        non_key_attributes: list[str] = None,
    ) -> None:
        self.index_name = index_name
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.projection_type = projection_type
        self.non_key_attributes = non_key_attributes


class ExtendedEnum(Enum):
    """Entension of standard Enum to provide list functionality

    Methods:
        list(enum_class: list[Enum]): Returns a list of values from the Enum items

    """

    @classmethod
    def list(enum_class: list[Enum]):
        return [category.value for category in enum_class]


class CategoryEnum(ExtendedEnum):
    MUSIC = "Music"
    GROCERY = "Grocery"
    CLOTHING = "Clothing"
    HOME = "Home"
    BOOKS = "Books"
    OUTDOORS = "Outdoors"
    ELECTRICS = "Electrics"
    BEAUTY = "Beauty"

    def __str__(self) -> str:
        return str(self.value)


class DynamoDbTableModel:
    """Data model for DynamoDB table

    Attributes:
        table_name(str): Name of the DynamoDB table
        partition_key(dynamodb.Attribute): Partition key of the table
        sort_key(dynamodb.Attribute): Sort key of the table
        global_secondary_indexes(List[SecondaryIndex], optional): List of global secondary indexes for the table (default: None)
    """

    def __init__(
        self,
        table_name: str,
        partition_key: dynamodb.Attribute,
        sort_key: dynamodb.Attribute,
        global_secondary_indexes: list[SecondaryIndex] = None,
    ) -> None:
        self.table_name = table_name
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.global_secondary_indexes = global_secondary_indexes


def create_db_attribute(
    name: str, type: dynamodb.AttributeType = dynamodb.AttributeType.STRING
) -> dynamodb.Attribute:
    """Helper function to set attribute type of dynamodb.Attribute object to
    dynamodb.AttributeType.STRING when not specified

    Args:
        name(str): The name of the attribute
        type(dynamodb.AttributeType, optional): The type of the attribute (default: AttributeType.STRING)

    Returns:
        dynamodb.Attribute: The created DynamoDB attribute.
    """
    return dynamodb.Attribute(name=name, type=type)


def create_secondary_indexes() -> list[SecondaryIndex]:
    """Creates secondary indexes for a DynamoDB table

    Returns:
        list[SecondaryIndex]: List of secondary indexes created
    """
    items_price_index = SecondaryIndex(
        index_name="ItemsPriceIndex",
        partition_key=create_db_attribute("static_pk"),
        sort_key=create_db_attribute(name="price", type=dynamodb.AttributeType.NUMBER),
    )
    category_price_index = SecondaryIndex(
        index_name="CategoryPriceIndex",
        partition_key=create_db_attribute("category"),
        sort_key=create_db_attribute(name="price", type=dynamodb.AttributeType.NUMBER),
        projection_type=dynamodb.ProjectionType.INCLUDE,
        non_key_attributes=["id", "last_updated_dt", "name"],
    )
    items_last_updated_dt_index = SecondaryIndex(
        index_name="ItemsLastUpdatedDtIndex",
        partition_key=create_db_attribute("static_pk"),
        sort_key=create_db_attribute("last_updated_dt"),
    )

    return [
        items_price_index,
        category_price_index,
        items_last_updated_dt_index,
    ]


global_secondary_indexes = create_secondary_indexes()
dynamodb_table_model = DynamoDbTableModel(
    table_name="InventoryTable",
    partition_key=create_db_attribute(name="name"),
    sort_key=create_db_attribute(name="category"),
    global_secondary_indexes=global_secondary_indexes,
)
