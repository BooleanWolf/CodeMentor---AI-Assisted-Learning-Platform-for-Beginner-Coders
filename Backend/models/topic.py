from bson import ObjectId
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import Optional, List
from pydantic.functional_validators import BeforeValidator
from pydantic import ConfigDict

# Annotating the PyObjectId type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class TopicModel(BaseModel):
    """
    Container for a single topic record. This model includes a reference to the user by user_id.
    """

    # The primary key for the TopicModel, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB, but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id") 
    
    # New user_id field to reference the user who created or owns the topic
    user_id: Optional[PyObjectId] = Field(None, alias="user_id")

    # Topic properties
    prompt_name: Optional[str] = Field(None)
    topic_list: Optional[str] = Field(None)  # The topic's name or description
    public: Optional[bool] = Field(None)
    


    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like ObjectId
        json_schema_extra = {
            "example": {
                "id": "60e5bba4b2a8f8c4b6e978ff",  # Example of Topic ID
                "user_id": "60e5bba4b2a8f8c4b6e978f0",  # Example of User ID (ObjectId of user)
                "prompt_name": "Physics 101",
                "topic_list": "Mechanics, Thermodynamics, Optics",
                "public": False,
            }
        }
