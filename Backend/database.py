from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Replace the old MongoDB client with the async motor client
client = AsyncIOMotorClient("mongodb+srv://admin:admin@cluster0.2y8y5ks.mongodb.net/codementor?retryWrites=true&w=majority&appName=Cluster0")
db = client.get_database()  # Automatically gets the default database
