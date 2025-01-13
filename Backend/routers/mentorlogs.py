from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db  # Assuming db is a MongoDB client instance
from models.mentorlog import MentorLog  # Assuming MentorLog is imported correctly
from models.user import UserModel  # Assuming UserModel is imported correctly
import json
from typing import List 

from swarm import Swarm, Agent
from dotenv import load_dotenv


router = APIRouter(prefix="/mentor", tags=["mentor"])


########################## AGENT #####################################################
load_dotenv()


# Initialize Swarm client
client = Swarm()

code_explanation_agent = Agent(
    instructions=f"You will be given a code. Explain the code line by line. Also in the beginning, tell the user what the code does in a short description. give them an easier version of code if needed."
)

text_explanation_agent = Agent(
    instructions=f"You will be given  a text. User will ask you question what  the user didn't understand from that text. Make them understand it by giving metaphors or real life examples. "
)

title_agent = Agent(
    instructions="Create a suitable title for the context and question within 6/7 words. Print only the title and nothing else."
)

def transfer_to_code_explanation_agent():
    return code_explanation_agent


def transfer_to_text_explanation_agent():
    return text_explanation_agent

teacher_agent = Agent(
    functions=[transfer_to_code_explanation_agent, transfer_to_text_explanation_agent], 
    instructions=f"You are a great teacher. Help user to understand code or text."
)

#######################################################################################################

# ObjectIdEncoder to serialize ObjectId to string in the response
class ObjectIdEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


# Route to create new content
@router.post("/create", response_model=MentorLog)
async def create_content(content: MentorLog):
    """
    Create a new content entry, process it with the appropriate agents, and add it to the user's contents list.
    """
    response_title = client.run(
        agent=title_agent,
        messages=[{"role": "user", "content": f"context: {content.context}. The question is {content.question}. "}],
    )

    content.title = response_title.messages[-1]["content"]
  
    print(content.title)

    # Generate content theory
    response_msg = client.run(
        agent=teacher_agent,
        messages=[{"role": "user", "content": f"context: {content.context}. The question is {content.question}. "}],
    )
    content.response = response_msg.messages[-1]["content"]

    print(content.response)

    print(content)
    # Insert the content into the database
    content_dict = content.dict(by_alias=True, exclude=["id"])  # Convert the content to a dictionary
    result = await db["mentor_log"].insert_one(content_dict)

    # Fetch the inserted content to return it with the generated ID
    created_log = await db["mentor_log"].find_one({"_id": result.inserted_id})

    if not created_log:
        raise HTTPException(status_code=400, detail="MentorLog creation failed")

    # Add the content ID to the user's contents list
    content_id = content.content_id  # Ensure the content has a content_id field
    user_update_result = await db["content"].update_one(
        {"_id": ObjectId(content_id)},
        {"$push": {"mentorLogs": created_log["_id"]}}  # Push the new content ID into the mentorLogs field
    )

    if user_update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update user's contents list")

    # Use Pydantic's from_orm method to return the created log correctly as a Pydantic model
    return MentorLog.parse_obj(created_log)




# Route to get all mentor logs associated with a content
@router.get("/content/{content_id}", response_model=List[MentorLog])
async def get_content_mentor_logs(content_id: str):
    """
    Get all MentorLogs associated with a specific content.
    """
    # Find the content by ID
    content = await db["content"].find_one({"_id": ObjectId(content_id)})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Get the mentorLogs list from the content
    mentor_log_ids = content.get("mentorLogs", [])
    
    if not mentor_log_ids:
        raise HTTPException(status_code=404, detail="No mentor logs found for this content")
    
    # Fetch all mentor logs
    mentor_logs = await db["mentor_log"].find({"_id": {"$in": mentor_log_ids}}).to_list(None)
    
    return [MentorLog.parse_obj(log) for log in mentor_logs]



# Route to get a mentor log by its ID
@router.get("/{mentor_log_id}", response_model=MentorLog)
async def get_mentor_log_by_id(mentor_log_id: str):
    """
    Get a MentorLog by its ID.
    """
    mentor_log = await db["mentor_log"].find_one({"_id": ObjectId(mentor_log_id)})
    if not mentor_log:
        raise HTTPException(status_code=404, detail="MentorLog not found")
    
    # Return the mentor log using Pydantic model
    return MentorLog.parse_obj(mentor_log)