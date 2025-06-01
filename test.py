from src.Wardrobe import OutfitSuggestionCrew
from tools.laundry_manager import filter_wardrobe_items, increment_laundry_count
from tools.db_manager import remove_item, add_item
import json
from typing import Dict, Any
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def save_state(wardrobe: Dict[str, Any], worn: Dict[str, Any]):
    """Save the current state of wardrobe and worn items to their respective JSON files."""
    with open("data/wardrobe.json", "w") as f:
        json.dump(wardrobe, f, indent=2)
    with open("data/worn.json", "w") as f:
        json.dump(worn, f, indent=2)

def main():
    # Load wardrobe items
    with open("data/wardrobe.json", "r") as f:
        wardrobe = json.load(f)
    
    # Initialize OutfitSuggestionCrew with the loaded items
    outfit_suggestion = OutfitSuggestionCrew(wardrobe["items"])

    run = input("Enter to get outfit suggestions: ").strip().lower()

    while run != "quit":
        suggestions = outfit_suggestion.suggest_outfit(available_items=wardrobe["items"])

        print("Outfit Suggestions:")
        # Load wardrobe items
        id_to_notes = {item["id"]: item["notes"] for item in wardrobe["items"]}
        # Print each item's notes/description
        for item_id in suggestions["suggestions"]["outfits"][0].get("items", []):
            print(f"{item_id}: {id_to_notes.get(item_id, 'Unknown item')}")

        thought = input("Enter your thoughts on the suggestions (yes/no): ").strip().lower()

        if thought == "yes":
            print("Glad you liked the suggestions!")
            outfit = []
            for item in suggestions["suggestions"]["outfits"][0].get("items", []):
                outfit.append(item)
                # Only remove if "shoe" not in id
                if "shoe" not in item:
                    # Remove the item from wardrobe
                    wardrobe["items"] = [i for i in wardrobe["items"] if i["id"] != item]

        run = input("Enter to get outfit suggestions: ").strip().lower()

def test_get_outfit_suggestion():
    """Test getting an outfit suggestion"""
    # Load wardrobe items
    with open("data/wardrobe.json", "r") as f:
        wardrobe = json.load(f)
    
    # Test with default parameters
    response = requests.get(f"{BASE_URL}/suggest_outfit")
    assert response.status_code == 200
    data = response.json()
    assert "outfits" in data
    assert "weather" in data
    assert "recommendations" in data
    
    # Test with custom parameters
    params = {
        "location": "New York, US",
        "formality": "Formal",
        "activity": "Work",
        "available_items": json.dumps(wardrobe["items"])
    }
    response = requests.get(f"{BASE_URL}/suggest_outfit", params=params)
    assert response.status_code == 200
    data = response.json()
    assert len(data["outfits"]) > 0

def test_log_outfit():
    """Test logging an outfit"""
    outfit_log = {
        "outfit_id": "test_outfit_1",
        "items": ["top1", "bottom1", "shoe1"],
        "date_worn": datetime.now().isoformat(),
        "weather": {
            "temperature": 72,
            "conditions": "sunny"
        },
        "activity": "Work",
        "formality": "Casual",
        "notes": "Test outfit log"
    }
    
    response = requests.post(f"{BASE_URL}/log_outfit", json=outfit_log)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_get_outfit_history():
    """Test getting outfit history"""
    response = requests.get(f"{BASE_URL}/outfit_history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data

def test_add_item():
    """Test adding a new clothing item"""
    new_item = {
        "id": "test_item_1",
        "type": "t-shirt",
        "form": "cotton",
        "weather": ["warm", "hot"],
        "color": "blue",
        "notes": "Test item",
        "image": "test_image.jpg"
    }
    
    response = requests.post(f"{BASE_URL}/add_item", json=new_item)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_remove_item():
    """Test removing a clothing item"""
    item_id = "test_item_1"
    response = requests.delete(f"{BASE_URL}/remove_item/{item_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_get_wardrobe():
    """Test getting all wardrobe items"""
    response = requests.get(f"{BASE_URL}/wardrobe")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data

def run_all_tests():
    """Run all tests"""
    print("Running tests...")
    
    print("\nTesting outfit suggestion...")
    test_get_outfit_suggestion()
    
    print("\nTesting outfit logging...")
    test_log_outfit()
    
    print("\nTesting outfit history...")
    test_get_outfit_history()
    
    print("\nTesting wardrobe management...")
    test_add_item()
    test_get_wardrobe()
    test_remove_item()
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    run_all_tests()