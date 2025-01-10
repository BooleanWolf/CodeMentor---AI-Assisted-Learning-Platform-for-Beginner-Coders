from pydantic import BaseModel
from bson import ObjectId

class MentorLog(BaseModel):
    title: str
    user_id: ObjectId
    context: str 
    question: str 
    content_id: ObjectId 
    response: str 

    
    class Config:
        json_encoders = {ObjectId: str}
