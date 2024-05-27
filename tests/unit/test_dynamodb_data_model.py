from aws_cdk import aws_dynamodb as dynamodb
from inventory_management_system.data_model.dynamodb_data_model import (
    SecondaryIndex,
    ExtendedEnum,
    CategoryEnum,
    DynamoDbTableModel,
    create_db_attribute,
    create_secondary_indexes,
)


def test_secondary_index_init():
    index_name = "ItemsPriceIndex"
    partition_key = create_db_attribute("static_pk")
    sort_key = create_db_attribute(name="price", type=dynamodb.AttributeType.NUMBER)

    secondary_index = SecondaryIndex(index_name, partition_key, sort_key)

    assert secondary_index.index_name == index_name
    assert secondary_index.partition_key == partition_key
    assert secondary_index.sort_key == sort_key
    assert secondary_index.projection_type == dynamodb.ProjectionType.ALL
    assert secondary_index.non_key_attributes is None


def test_secondary_index_all_arguments():
    index_name = "TestIndex"
    partition_key = create_db_attribute("test_pk")
    sort_key = create_db_attribute(name="test_sk", type=dynamodb.AttributeType.NUMBER)
    projection_type = dynamodb.ProjectionType.INCLUDE
    non_key_attributes = ["test_att1", "test_att2"]

    secondary_index = SecondaryIndex(
        index_name, partition_key, sort_key, projection_type, non_key_attributes
    )

    assert secondary_index.index_name == index_name
    assert secondary_index.partition_key == partition_key
    assert secondary_index.sort_key == sort_key
    assert secondary_index.projection_type == projection_type
    assert secondary_index.non_key_attributes == non_key_attributes


def test_extended_enum_list_method():
    class ExampleEnum(ExtendedEnum):
        OPTION1 = "Option 1"
        OPTION2 = "Option 2"

    assert ExampleEnum.list() == ["Option 1", "Option 2"]


def test_category_enum_str_representation():
    assert str(CategoryEnum.MUSIC) == "Music"


def test_category_enum_list_method():
    assert CategoryEnum.list() == [
        "Music",
        "Grocery",
        "Clothing",
        "Home",
        "Books",
        "Outdoors",
        "Electrics",
        "Beauty",
    ]


def test_create_db_attribute():
    attribute = create_db_attribute(name="test_attribute")
    assert attribute.name == "test_attribute"
    assert attribute.type == dynamodb.AttributeType.STRING


def test_create_secondary_indexes():
    expected_indexes = [
        SecondaryIndex(
            index_name="ItemsPriceIndex",
            partition_key=create_db_attribute("static_pk"),
            sort_key=create_db_attribute(
                name="price", type=dynamodb.AttributeType.NUMBER
            ),
        ),
        SecondaryIndex(
            index_name="CategoryPriceIndex",
            partition_key=create_db_attribute("category"),
            sort_key=create_db_attribute(name="name"),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["id", "last_updated_dt", "price"],
        ),
        SecondaryIndex(
            index_name="ItemsLastUpdatedDtIndex",
            partition_key=create_db_attribute("static_pk"),
            sort_key=create_db_attribute("last_updated_dt"),
        ),
    ]
    actual_indexes = create_secondary_indexes()
    assert len(expected_indexes) == len(actual_indexes)
    for expected_index, actual_index in zip(expected_indexes, actual_indexes):
        assert expected_index.index_name == actual_index.index_name
        assert expected_index.partition_key == actual_index.partition_key
        assert expected_index.sort_key == actual_index.sort_key
        assert expected_index.projection_type == actual_index.projection_type
        assert expected_index.non_key_attributes == actual_index.non_key_attributes


def test_dynamodb_table_model_init():
    partition_key = create_db_attribute("partition_key")
    sort_key = create_db_attribute("sort_key")
    global_secondary_indexes = ["idx1", "idx2", "idx3"]
    model = DynamoDbTableModel(
        table_name="TestTable",
        partition_key=partition_key,
        sort_key=sort_key,
        global_secondary_indexes=global_secondary_indexes,
    )
    assert model.table_name == "TestTable"
    assert model.partition_key == partition_key
    assert model.sort_key == sort_key
    assert model.global_secondary_indexes == global_secondary_indexes
