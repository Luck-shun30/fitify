import sys
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.Wardrobe import OutfitSuggestionCrew
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Pydantic models for request/response validation
class ClothingItem(BaseModel):
    id: str
    type: str
    form: str
    weather: List[str]
    color: str
    notes: str
    image: str

class OutfitLog(BaseModel):
    outfit_id: str
    items: List[str]
    date_worn: str
    weather: Dict[str, Any]
    activity: str
    formality: str
    notes: str = ""

class OutfitResponse(BaseModel):
    outfits: List[Dict[str, Any]]
    weather: Dict[str, Any]
    recommendations: List[str]

# Global state (in a real app, this would be a database)
wardrobe_items = []
outfit_history = []

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/suggest_outfit")
def suggest_outfit(
    location: str = "Chicago, US", 
    formality: str = "Casual", 
    activity: str = "School",
    available_items: str = None
) -> OutfitResponse:
    try:
        # Parse available items from JSON string
        items = json.loads(available_items) if available_items else wardrobe_items
        
        # Initialize outfit suggestion with available items
        outfit = OutfitSuggestionCrew(items)
        
        # Get outfit suggestion
        suggestion = outfit.suggest_outfit(location, formality, activity)
        
        # Format response according to OutfitResponse model
        return OutfitResponse(
            outfits=suggestion["suggestions"]["outfits"],
            weather=suggestion["weather"],
            recommendations=suggestion["suggestions"]["recommendations"]
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for available_items")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/log_outfit")
def log_outfit(outfit_log: OutfitLog):
    """Log an outfit that was worn"""
    try:
        # Add to history
        outfit_history.append(outfit_log.dict())
        return {"status": "success", "message": "Outfit logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/outfit_history")
def get_outfit_history():
    """Get history of worn outfits"""
    return {"history": outfit_history}

@app.post("/add_item")
def add_item(item: ClothingItem):
    """Add a new clothing item to the wardrobe"""
    try:
        wardrobe_items.append(item.dict())
        return {"status": "success", "message": "Item added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/remove_item/{item_id}")
def remove_item(item_id: str):
    """Remove an item from the wardrobe"""
    try:
        global wardrobe_items
        wardrobe_items = [item for item in wardrobe_items if item["id"] != item_id]
        return {"status": "success", "message": "Item removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wardrobe")
def get_wardrobe():
    """Get all items in the wardrobe"""
    return {"items": wardrobe_items}

if __name__ == "__main__":
    import uvicorn
    with open("data/wardrobe.json", "r") as f:
        wardrobe = json.load(f)
        wardrobe_items = wardrobe["items"]
    print(json.dumps(wardrobe_items, indent=2))
    uvicorn.run(app, host="127.0.0.1", port=8000)