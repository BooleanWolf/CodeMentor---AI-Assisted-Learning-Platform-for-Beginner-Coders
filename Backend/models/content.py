from pydantic import BaseModel
from bson import ObjectId

class Content(BaseModel):
    title: str
    user_id: ObjectId
    content_theory: str 
    content_codes: str 
    content_syntax: str 
    

    class Config:
        json_encoders = {ObjectId: str}
