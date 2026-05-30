from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.item import Item, ItemCreate, ItemUpdate

router = APIRouter()

# In-memory storage for demonstrating full CRUD functionality
MOCK_ITEMS_DB: List[Item] = [
    Item(id=1, title="Premium Feature", description="Fully customized Next.js + FastAPI integration"),
    Item(id=2, title="Responsive Design", description="Elegant styling across all viewport sizes"),
]

@router.get("/", response_model=List[Item])
def get_items():
    """
    Retrieve all mock items.
    """
    return MOCK_ITEMS_DB

@router.get("/{item_id}", response_model=Item)
def get_item(item_id: int):
    """
    Get a single item by its ID.
    """
    for item in MOCK_ITEMS_DB:
        if item.id == item_id:
            return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"Item with ID {item_id} not found"
    )

@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate):
    """
    Create a new item.
    """
    new_id = max([item.id for item in MOCK_ITEMS_DB], default=0) + 1
    new_item = Item(id=new_id, **item_in.model_dump())
    MOCK_ITEMS_DB.append(new_item)
    return new_item

@router.put("/{item_id}", response_model=Item)
def update_item(item_id: int, item_in: ItemUpdate):
    """
    Update an existing item by its ID.
    """
    for i, item in enumerate(MOCK_ITEMS_DB):
        if item.id == item_id:
            update_data = item_in.model_dump(exclude_unset=True)
            updated_item = item.model_copy(update=update_data)
            MOCK_ITEMS_DB[i] = updated_item
            return updated_item
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"Item with ID {item_id} not found"
    )

@router.delete("/{item_id}", response_model=Item)
def delete_item(item_id: int):
    """
    Delete an item by its ID.
    """
    for i, item in enumerate(MOCK_ITEMS_DB):
        if item.id == item_id:
            return MOCK_ITEMS_DB.pop(i)
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"Item with ID {item_id} not found"
    )
