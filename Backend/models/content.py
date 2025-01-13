from bson import ObjectId
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import Optional, List
from pydantic.functional_validators import BeforeValidator

# Annotating the PyObjectId type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]

class ContentModel(BaseModel):
    """
    Container for a single content record. This model includes a reference to the user by user_id.
    """

    # The primary key for the ContentModel, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB, but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")

    # Reference to the user who created or owns the content
    user_id: Optional[PyObjectId] = Field(None, alias="user_id")

    # Content properties
    title: str  # Title of the content
    prompt: str
    content_theory: Optional[str] = Field(None)  # Theoretical explanation of the content
    content_codes: Optional[str] = Field(None)  # Code examples related to the content
    content_syntax: Optional[str] = Field(None)  # Syntax details of the content
    public: Optional[bool] = Field(None)
    mentorLogs: Optional[List[PyObjectId]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like ObjectId
        json_encoders = {ObjectId: str}  # Encode ObjectId as a string in JSON
        json_schema_extra = {
            "example": {
                "id": "60e5bba4b2a8f8c4b6e978ff",  # Example of Content ID
                "user_id": "60e5bba4b2a8f8c4b6e978f0",  # Example of User ID (ObjectId of user)
                "prompt": "I am newbie, I want to learn", 
                "title": "Introduction to Python",
                "content_theory": "Python is a versatile programming language...",
                "content_codes": "print('Hello, World!')",
                "content_syntax": "print(<expression>)",
            }
        }
