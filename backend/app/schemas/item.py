from typing import Optional
from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="The title of the item")
    description: Optional[str] = Field(None, max_length=500, description="A description of the item")

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class Item(ItemBase):
    id: int = Field(..., description="The unique identifier of the item")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "Example Item",
                "description": "This is a sample item description."
            }
        }
    }
