from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db  # Assuming db is a MongoDB client instance
from models.content import ContentModel  # Assuming TopicModel is imported correctly
from models.user import UserModel  # Assuming UserModel is imported correctly
import json
from typing import List 

from swarm import Swarm, Agent
from dotenv import load_dotenv


router = APIRouter(prefix="/content", tags=["content"])


########################## AGENT #####################################################
load_dotenv()


# Initialize Swarm client
client = Swarm()

content_theory_agent = Agent(
    instructions=f"You will explain the topic given to you considering the user's age and experience. Don't say welcome or hi. Just start with explaining with metaphors or real world examples. Don't show any code of that topic. Try to make him understand the concept of the topic. Also consider the preference of the user when generating the documentation."
)

content_code_agent = Agent(
    instructions=f"You will generate 5 coding examples on the topic you are given for the user to learn considering the user's preference.Don't say welcome or hi or things like 'That's a great choice'. Just start with the code. "
)

content_syntax_agent = Agent(
    instructions=f"You will explain the user the syntax of a given topic considering the user's preference. If the topic doesn't have any coding concept then just return NULL. Don't say welcome or hi or things like 'That's a great choice'."
)


#######################################################################################################



# ObjectIdEncoder to serialize ObjectId to string in the response
class ObjectIdEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)
    

# Route to create new content
@router.post("/create", response_model=ContentModel)
async def create_content(content: ContentModel):
    """
    Create a new content entry, process it with the appropriate agents, and add it to the user's contents list.
    """
    # Generate content theory
    theory_response = client.run(
        agent=content_theory_agent,
        messages=[{"role": "user", "content": content.prompt}],
    )
    content.content_theory = theory_response.messages[-1]["content"]

    print(content.content_theory)

    # Generate content codes
    code_response = client.run(
        agent=content_code_agent,
        messages=[{"role": "user", "content": content.prompt}],
    )
    content.content_codes = code_response.messages[-1]["content"]

    print(content.content_codes)

    # Generate content syntax
    syntax_response = client.run(
        agent=content_syntax_agent,
        messages=[{"role": "user", "content": content.prompt}],
    )
    content.content_syntax = syntax_response.messages[-1]["content"]

    print(content.content_syntax)

    # Insert the content into the database
    result = await db["content"].insert_one(content.dict(by_alias=True, exclude=["id"]))

    # Fetch the inserted content to return it with the generated ID
    created_content = await db["content"].find_one({"_id": result.inserted_id})

    if not created_content:
        raise HTTPException(status_code=400, detail="Content creation failed")

    # Add the content ID to the user's contents list
    user_id = content.user_id  # Ensure the content has a user_id field
    user_update_result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"contents": created_content["_id"]}}  # Push the new content ID into the contents field
    )

    if user_update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update user's contents list")

    # Serialize the content to include ObjectId as string
    return json.loads(json.dumps(created_content, cls=ObjectIdEncoder))



@router.get("/public", response_model=List[ContentModel])
async def get_public_content():
    """
    Get all content where public is set to true.
    """
    public_content = await db["content"].find({"public": True}).to_list(length=100)

    if not public_content:
        raise HTTPException(status_code=404, detail="No public content found")

    return json.loads(json.dumps(public_content, cls=ObjectIdEncoder))


@router.get("/public/titles", response_model=List[str])
async def get_public_titles():
    """
    Get all titles of public content available in the database.
    """
    public_titles = await db["content"].find({"public": True}, {"title": 1, "_id": 0}).to_list(length=100)

    if not public_titles:
        raise HTTPException(status_code=404, detail="No public titles found")

    return [title["title"] for title in public_titles]

# Route to get all content titles
@router.get("/titles", response_model=List[str])
async def get_all_titles():
    """
    Get all content titles available in the database.
    """
    titles = await db["content"].find({}, {"title": 1, "_id": 0}).to_list(length=100)
    return [title["title"] for title in titles]


# Route to get content by ID
@router.get("/{content_id}", response_model=ContentModel)
async def get_content_by_id(content_id: str):
    """
    Get content by its ID.
    """
    content = await db["content"].find_one({"_id": ObjectId(content_id)})

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return json.loads(json.dumps(content, cls=ObjectIdEncoder))


# Route to get all content for a user
@router.get("/user/{user_id}", response_model=List[ContentModel])
async def get_user_content(user_id: str):
    """
    Get all content created by a specific user.
    """
    user_content = await db["content"].find({"user_id": user_id}).to_list(length=100)

    if not user_content:
        raise HTTPException(status_code=404, detail="No content found for the user")

    return json.loads(json.dumps(user_content, cls=ObjectIdEncoder))

