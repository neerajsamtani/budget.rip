from pprint import pprint
from pymongo import MongoClient

# Replace these variables with your MongoDB connection details
MONGO_URI = ''  # Change to your MongoDB URI
DATABASE_NAME = 'flask_db'
COLLECTION_NAME = 'events'

# Create a MongoDB client
client = MongoClient(MONGO_URI)

# Access the database
db = client[DATABASE_NAME]

# Access the collection
collection = db[COLLECTION_NAME]

# Define the filter to find documents where `is_duplicate_transaction` is null
filter_query = {'is_duplicate_transaction': ""}

# Perform the dry run: find documents matching the filter
documents_to_update = collection.find(filter_query)

# Print the documents that would be updated
print("Documents that would be updated:")
for doc in documents_to_update:
    pprint(doc)

# Define the update to set `is_duplicate_transaction` to false
update_query = {'$set': {'is_duplicate_transaction': False}}

# Update all documents matching the filter query
result = collection.update_many(filter_query, update_query)

# Print the number of documents updated
print(f'Number of documents updated: {result.modified_count}')

# Close the client connection
client.close()
