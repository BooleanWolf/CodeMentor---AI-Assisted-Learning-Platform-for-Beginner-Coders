from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db  # Assuming db is a MongoDB client instance
from models.topic import TopicModel  # Assuming TopicModel is imported correctly
from models.user import UserModel  # Assuming UserModel is imported correctly
import json
from typing import List 

from swarm import Swarm, Agent
from dotenv import load_dotenv

########################## AGENT #####################################################
load_dotenv()


# Initialize Swarm client
client = Swarm()

topic_agent_advanced = Agent(
    instructions=f"You will generate topic list that are needed to learn a programming language that the user wants to learn. Create a topic list for the user. The user want to learn everything in depth and advanced. Just generate the topic list with numbered bullets. Show only the topic name. Make sure the number of topics are between 8 and 9."
)

topic_agent_beginner = Agent(
    instructions=f"You will generate topic list that are needed to learn a programming language that the user wants to learn. Create a topic list for the user. The user is a beginner. Just generate the topic list with numbered bullets. Show only the topic name. Make sure the number of topics are between 15 and 20."
)

def transfer_to_topic_advanced():
    return topic_agent_advanced 

def transfe_to_topic_beginner():
    return topic_agent_beginner


topic_agent = Agent(
    functions=[transfer_to_topic_advanced, transfe_to_topic_beginner],
    instructions=f"You will generate topic list that are needed to learn a programming language that the user wants to learn. Create a topic list for the user. Consider his age and prior experience in coding. Just generate the topic list with numbered bullets. Show only the topic name. Make sure the number of topics are between 8 and 9."
)

###################################################################################################################

router = APIRouter(prefix="/topics", tags=["topics"])

# ObjectIdEncoder to serialize ObjectId to string in the response
class ObjectIdEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Route to create a new topic and add it to the user's topic_list
@router.post("/create", response_model=TopicModel)
async def create_topic(topic: TopicModel):
    """
    Create a new topic and associate it with a user. 
    Add the topic to the user's topic_list.
    """


    response = client.run(
        agent=topic_agent,
        messages=[{"role": "user", "content": f"{topic.prompt_name}"}],
    )
    
    topic.topic_list =  response.messages[-1]["content"]

    # Insert the topic into the database
    result = await db["topics"].insert_one(topic.dict(by_alias=True, exclude=["id"]))
    
    # Fetch the inserted topic to return it with the generated ID
    created_topic = await db["topics"].find_one({"_id": result.inserted_id})
    
    if not created_topic:
        raise HTTPException(status_code=400, detail="Topic creation failed")
    
    # Add the topic to the user's topic_list
    user_id = topic.user_id  # Ensure the topic has a user_id field
    user_update_result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"topic_list": created_topic["_id"]}}  # Push the new topic ID into the topic_list field
    )
    
    if user_update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update user's topic list")

    # Serialize the topic to include ObjectId as string
    return json.loads(json.dumps(created_topic, cls=ObjectIdEncoder))



# Route to get all public topics
@router.get("/public_topics", response_model=List[TopicModel])
async def get_public_topics():
    """
    Get all topics that are public (public: true).
    """
    # Fetch all public topics from the database
    public_topics = await db["topics"].find({"public": True}).to_list(length=100)
    
    if not public_topics:
        raise HTTPException(status_code=404, detail="No public topics found")
    
    # Serialize the public topics to include ObjectId as string
    return json.loads(json.dumps(public_topics, cls=ObjectIdEncoder))


# Route to get a topic by ID, including user info
@router.get("/{topic_id}", response_model=TopicModel)
async def get_topic(topic_id: str):
    """
    Get a topic by its ID and include user info associated with the topic.
    """
    # Fetch the topic from the database using ObjectId
    topic = await db["topics"].find_one({"_id": ObjectId(topic_id)})
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Fetch the user associated with this topic using user_id
    user_id = topic.get("user_id")
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Serialize both the topic and user data to include ObjectId as string
    topic = json.loads(json.dumps(topic, cls=ObjectIdEncoder))
    user = json.loads(json.dumps(user, cls=ObjectIdEncoder))
    
    # Combine the topic and user data into a single response
    response = {**topic, "user": user}
    
    return response

# Route to get all topics by a specific user
@router.get("/user/{user_id}", response_model=List[TopicModel])
async def get_user_topics(user_id: str):
    """
    Get all topics associated with a specific user by user ID.
    """
    # Fetch all topics associated with the user_id
    # Convert user_id to ObjectId for the query comparison
    topics = await db["topics"].find({"user_id": user_id}).to_list(length=100)
    
    if not topics:
        raise HTTPException(status_code=404, detail="No topics found for this user")
    
    # Serialize the topics to include ObjectId as string
    return json.loads(json.dumps(topics, cls=ObjectIdEncoder))