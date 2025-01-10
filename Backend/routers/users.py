from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db
from models.user import UserModel
import json


router = APIRouter(prefix="/users", tags=["users"])

class ObjectIdEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

@router.post("/create")
async def create_user(user: UserModel):
    """
    Insert a new user record.
    
    A unique `id` will be created and provided in the response.
    """
    # Insert the user into the database, excluding the `id` field
    new_user = await db["users"].insert_one(
        user.model_dump(by_alias=True, exclude=["id"])  # Exclude the `id` when inserting
    )
    
    # Find the created user to return it with the new `id`
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    
    return json.loads(json.dumps(created_user, cls=ObjectIdEncoder))  # Serialize ObjectId to string
  

@router.get("/{user_id}")
async def get_user(user_id: str):
    """
    Get a user by their ID along with their topics and contents.
    """
    # Fetch the user from the database using ObjectId
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch the associated topics and contents using their ObjectIds
    topics = await db["topics"].find({"_id": {"$in": user.get("topics", [])}}).to_list(length=None)
    contents = await db["contents"].find({"_id": {"$in": user.get("contents", [])}}).to_list(length=None)
    
    # Serialize ObjectId to string for the response
    user = json.loads(json.dumps(user, cls=ObjectIdEncoder))
    
    # Return the user along with the topics and contents
    return {
        "user": user,
        "topics": json.loads(json.dumps(topics, cls=ObjectIdEncoder)),
        "contents": json.loads(json.dumps(contents, cls=ObjectIdEncoder)),
    }