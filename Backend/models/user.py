from bson import ObjectId
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import Optional, List
from pydantic.functional_validators import BeforeValidator
from pydantic import ConfigDict, BaseModel, Field


PyObjectId = Annotated[str, BeforeValidator(str)]


class UserModel(BaseModel):
    """
    Container for a single student record.
    """

    # The primary key for the UserModel, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB,
    # but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id") 
    
    name: Optional[str] = Field(None)
    email: str = Field(...)  # Email is required
    topics: Optional[List[PyObjectId]] = Field(default_factory=list)  # List of ObjectIds, optional
    contents: Optional[List[PyObjectId]] = Field(default_factory=list)  # List of ObjectIds, optional
    credit: Optional[float] = Field(None)  # Optional credit value

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like ObjectId
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "topics": ["60e5bba4b2a8f8c4b6e978ff", "60e5bba4b2a8f8c4b6e97900"],
                "contents": ["60e5bba4b2a8f8c4b6e97901", "60e5bba4b2a8f8c4b6e97902"],
                "credit": 3.0,
            }
        }