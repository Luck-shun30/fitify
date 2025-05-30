from src.Wardrobe import OutfitSuggestionCrew
from tools.laundry_manager import filter_wardrobe_items, increment_laundry_count
from tools.db_manager import remove_item, add_item
import json

def main():
    outfit_suggestion = OutfitSuggestionCrew()

    run = input("Enter to get outfit suggestions: ").strip().lower()

    while run != "quit":
        with open("data/wardrobe.json", "r") as f:
            wardrobe = json.load(f)
        with open("data/worn.json", "r") as f:
            worn = json.load(f)
        
        increment_laundry_count() 
        suggestions = outfit_suggestion.suggest_outfit(available_items=filter_wardrobe_items())

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
                    remove_item(item)

            # Prepare items to add
            items_to_add = []
            for item_id in outfit:
                if "shoe" not in item_id:
                    item = next((i for i in wardrobe["items"] if i["id"] == item_id), None)
                    if item:
                        item_copy = item.copy()
                        item_copy["count"] = 0
                        items_to_add.append(item_copy)
                        print(item_copy)
            # Add all at once
            worn["laundry"].extend(items_to_add)
            with open("data/worn.json", "w") as f:
                json.dump(worn, f, indent=2)

        elif thought == "no":
            print("Sorry to hear that. Let's try again.")
            choice = input("Which item would you like to shuffle? (1/2/3/Enter): ").strip().lower()
            
            # Get current items from the outfit
            current_tops = []
            current_bottoms = []
            current_shoes = []
            
            for item in suggestions["suggestions"]["outfits"][0].get("items", []):
                item_data = next((i for i in wardrobe["items"] if i["id"] == item), None)
                if item_data:
                    if "tshirt" in item or "shirt" in item:
                        current_tops.append(item_data)
                    elif "pants" in item or "shorts" in item:
                        current_bottoms.append(item_data)
                    elif "shoes" in item:
                        current_shoes.append(item_data)
            
            if choice == "1":
                new_suggestions = outfit_suggestion.suggest_tops(
                    available_items=filter_wardrobe_items(),
                    current_bottoms=current_bottoms,
                    current_shoes=current_shoes
                )
                # Update the outfit with new tops while keeping original bottoms and shoes
                original_bottoms = [item for item in suggestions["suggestions"]["outfits"][0]["items"] if "pants" in item or "shorts" in item]
                original_shoes = [item for item in suggestions["suggestions"]["outfits"][0]["items"] if "shoe" in item]
                suggestions["suggestions"]["outfits"][0]["items"] = [
                    item["item_id"] for item in new_suggestions["suggestions"]["tops"]
                ] + original_bottoms + original_shoes
                
            elif choice == "2":
                new_suggestions = outfit_suggestion.suggest_bottoms(
                    available_items=filter_wardrobe_items(),
                    current_tops=current_tops,
                    current_shoes=current_shoes
                )
                # Update the outfit with new bottoms while keeping original tops and shoes
                original_tops = [item for item in suggestions["suggestions"]["outfits"][0]["items"] if "tshirt" in item or "shirt" in item]
                original_shoes = [item for item in suggestions["suggestions"]["outfits"][0]["items"] if "shoe" in item]
                suggestions["suggestions"]["outfits"][0]["items"] = original_tops + [
                    item["item_id"] for item in new_suggestions["suggestions"]["bottoms"]
                ] + original_shoes
                
            elif choice == "3":
                new_suggestions = outfit_suggestion.suggest_shoes(
                    available_items=filter_wardrobe_items(),
                    current_tops=current_tops,
                    current_bottoms=current_bottoms
                )
                # Update the outfit with new shoes while keeping original tops and bottoms
                original_tops = [item for item in suggestions["suggestions"]["outfits"][0]["items"] if "tshirt" in item or "shirt" in item]
                original_bottoms = [item for item in suggestions["suggestions"]["outfits"][0]["items"] if "pants" in item or "shorts" in item]
                suggestions["suggestions"]["outfits"][0]["items"] = original_tops + original_bottoms + [
                    item["item_id"] for item in new_suggestions["suggestions"]["shoes"]
                ]

            # Show the updated outfit
            print("\nUpdated Outfit:")
            for item_id in suggestions["suggestions"]["outfits"][0].get("items", []):
                print(f"{item_id}: {id_to_notes.get(item_id, 'Unknown item')}")

            # Ask if they like the new suggestion
            thought = input("Do you like this updated outfit? (yes/no): ").strip().lower()
            if thought == "yes":
                print("Great! The outfit has been updated.")
                outfit = []
                for item in suggestions["suggestions"]["outfits"][0].get("items", []):
                    outfit.append(item)
                    # Only remove if "shoe" not in id
                    if "shoe" not in item:
                        remove_item(item)

                # Prepare items to add
                items_to_add = []
                for item_id in outfit:
                    if "shoe" not in item_id:
                        item = next((i for i in wardrobe["items"] if i["id"] == item_id), None)
                        if item:
                            item_copy = item.copy()
                            item_copy["count"] = 0
                            items_to_add.append(item_copy)
                            print(item_copy)
                # Add all at once
                worn["laundry"].extend(items_to_add)
                with open("data/worn.json", "w") as f:
                    json.dump(worn, f, indent=2)

        run = input("Enter to get outfit suggestions: ").strip().lower()

if __name__ == "__main__":
    main()