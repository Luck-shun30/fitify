import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from typing import Union
from src.Wardrobe import OutfitSuggestionCrew
from fastapi import FastAPI

outfit = OutfitSuggestionCrew()
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/suggest_outfit")
def suggest_outfit(location: str = "Chicago, US", formality: str = "Casual", activity: str = "School"):
    return outfit.suggest_outfit(location, formality, activity)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)