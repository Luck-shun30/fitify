import json
from tools.db_manager import add_item, remove_item

def filter_wardrobe_items():
    LAUNDRY_CYCLE = 2

    with open("data/wardrobe.json", "r") as f:
        wardrobe = json.load(f)
    with open("data/worn.json", "r") as f:
        worn = json.load(f)
    
    for item in worn.get("laundry", [])[:]:
        if item["count"] >= LAUNDRY_CYCLE:
            print(f"Item {item['id']} has been through the laundry. It will be removed from the worn list.")
            worn["laundry"].remove(item)
            add_item(item)
            with open("data/worn.json", "w") as f:
                json.dump(worn, f, indent=2)

    worn_ids = {item["id"] for item in worn.get("laundry", [])}
    filtered_wardrobe_items = [item for item in wardrobe["items"] if item["id"] not in worn_ids]
    return filtered_wardrobe_items

def increment_laundry_count():
    with open("data/worn.json", "r") as f:
        worn = json.load(f)
    
    for item in worn.get("laundry", []):
        item["count"] += 1

    with open("data/worn.json", "w") as f:
        json.dump(worn, f, indent=2)