import json

def remove_item(item_id):
    with open("data/wardrobe.json", "r") as f:
        data = json.load(f)
    # Filter out the item with the given id
    data["items"] = [item for item in data["items"] if item["id"] != item_id]
    with open("data/wardrobe.json", "w") as f:
        json.dump(data, f, indent=2)

def add_item(new_item):
    with open("data/wardrobe.json", "r") as f:
        data = json.load(f)
    # Ensure "items" key exists and is a list
    if "items" not in data or not isinstance(data["items"], list):
        data["items"] = []
    data["items"].append(new_item)
    with open("data/wardrobe.json", "w") as f:
        json.dump(data, f, indent=2)
    with open("data/wardrobe.json", "w") as f:
        json.dump(data, f, indent=2)