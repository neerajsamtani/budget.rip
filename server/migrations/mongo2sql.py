from pymongo import MongoClient


def generate_sql_schema_from_document(document, prefix=""):
    sql_schema = ""
    for key, value in document.items():
        if isinstance(value, dict):
            # Recursively handle nested documents
            nested_sql_schema = generate_sql_schema_from_document(
                value, prefix=f"{prefix}{key}_"
            )
            sql_schema += nested_sql_schema
            sql_schema += f"{prefix}{key}_id INT,"
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # List of nested documents
            nested_sql_schema = generate_sql_schema_from_document(
                value[0], prefix=f"{prefix}{key}_"
            )
            sql_schema += f"{prefix}{key}_id INT,"
            sql_schema += nested_sql_schema
        else:
            # Handle other types
            if isinstance(value, int):
                sql_schema += f"{prefix}{key} INT,"
            elif isinstance(value, float):
                sql_schema += f"{prefix}{key} FLOAT,"
            elif isinstance(value, str):
                sql_schema += f"{prefix}{key} VARCHAR(255),"
            elif isinstance(value, bool):
                sql_schema += f"{prefix}{key} BOOLEAN,"
    return sql_schema


def generate_sql_schemas(database_name):
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client[database_name]

    # Get a list of all collection names in the database
    collection_names = db.list_collection_names()

    sql_schemas = {}
    for collection_name in collection_names:
        sample_doc = db[collection_name].find_one()
        sql_schema = generate_sql_schema_from_document(sample_doc)
        sql_schemas[collection_name] = sql_schema

    return sql_schemas


if __name__ == "__main__":
    database_name = input("Enter the name of the MongoDB database: ")
    sql_schemas = generate_sql_schemas(database_name)

    print("Corresponding SQL schemas:")
    for collection_name, sql_schema in sql_schemas.items():
        print(f"Collection: {collection_name}")
        print(f"CREATE TABLE IF NOT EXISTS {collection_name} (")
        print(sql_schema.rstrip(","))
        print(");")
        print()
