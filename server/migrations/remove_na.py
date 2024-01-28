from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("localhost", 27017)
db = client.flask_db

# Access the 'events' collection
events_collection = db.events

# Update documents with category = 'N/A' to 'Transfer'
query = {"category": "Transfer"}
update_query = {"$set": {"category": "Transfer"}}
result = events_collection.update_many(query, update_query)

# Print the number of documents updated
print("Number of documents updated:", result.modified_count)
