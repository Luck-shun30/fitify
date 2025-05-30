import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from mistralai import Mistral
from dotenv import load_dotenv
import os
import json
import base64
import shutil
from datetime import datetime

def ensure_wardrobe_folder():
    """Ensure the wardrobe folder exists"""
    if not os.path.exists("wardrobe"):
        os.makedirs("wardrobe")

def save_image(image_path, item_id):
    """Save image to wardrobe folder with unique name"""
    ensure_wardrobe_folder()
    # Get file extension
    _, ext = os.path.splitext(image_path)
    # Create new filename with timestamp and item_id
    new_filename = f"{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    new_path = os.path.join("wardrobe", new_filename)
    # Copy the image to wardrobe folder
    shutil.copy2(image_path, new_path)
    return new_path

def encode_image_base64(image_path): 
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def image_to_json(path):
    load_dotenv()

    # Initialize the Mistral AI client
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    # Define the prompt for outfit suggestions
    with open("data/wardrobe.json", "r") as f:
        wardrobe = json.load(f)

    existing_ids = [item["id"] for item in wardrobe["items"]]
    prompt = """
    Describe the clothing item in the image you see in the following JSON format:
    {
        "id": "name1",
        "type": "type" (t-shirt, pants, shorts, shoes),
        "form": "form" (t like denim, cotton, chinos, leather etc.),
        "weather": ["warm", "hot"], ("cold", "rainy", "snowy", "windy", "sunny"),
        "color": "specific color of the item",
        "notes": "Notes about the item",
        "count": 1
    }

    Do not include any additional text or explanations, just the JSON object.
    Do not make the id the same as the following:
    """ + "\n".join(existing_ids)

    # Encode the image to base64
    image_base64 = encode_image_base64(path)

    # Get outfit suggestions from the Mistral AI model
    response = client.chat.complete(
        model="pixtral-12b-2409",
        messages = [
            {"role": "user", 
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": "data:image/png;base64," + image_base64},     
                ] 
            } 
        ]
    )

    json_resp = response.choices[0].message.content
    try:
        if isinstance(json_resp, str):
            # Remove markdown code block formatting if present
            if json_resp.startswith('```json'):
                json_resp = json_resp[7:]  # Remove ```json
            if json_resp.startswith('```'):
                json_resp = json_resp[3:]  # Remove ```
            if json_resp.endswith('```'):
                json_resp = json_resp[:-3]  # Remove trailing ```
            json_resp = json_resp.strip()  # Remove any extra whitespace
            item_data = json.loads(json_resp)
        else:
            # Handle non-string json_resps
            json_resp_str = json_resp.raw if hasattr(json_resp, 'raw') else str(json_resp)
            if json_resp_str.startswith('```json'):
                json_resp_str = json_resp_str[7:]
            if json_resp_str.startswith('```'):
                json_resp_str = json_resp_str[3:]
            if json_resp_str.endswith('```'):
                json_resp_str = json_resp_str[:-3]
            json_resp_str = json_resp_str.strip()
            item_data = json.loads(json_resp_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing outfit suggestions: {str(e)}")
        print(f"Raw json_resp: {json_resp}")
        # Return a default outfit suggestion
        item_data = {
            "id": "default",
            "type": "default",
            "form": "default",
            "weather": ["default", "default"],
            "color": "default",
            "notes": "default",
            "count": 1
        }
    
    # Save the image and add its path to the item data
    image_path = save_image(path, item_data["id"])
    item_data["image"] = image_path
    
    return item_data

def add_to_wardrobe(path):
    with open("data/wardrobe.json", "r") as f:
        wardrobe = json.load(f)
    wardrobe["items"].append(image_to_json(path))
    with open("data/wardrobe.json", "w") as f:
        json.dump(wardrobe, f, indent=2)

if __name__ == "__main__":
    add_to_wardrobe("data/shirt.png")
    add_to_wardrobe("data/tshirt.png")
    add_to_wardrobe("data/tshirt2.png")
    add_to_wardrobe("data/shirt2.png")
    add_to_wardrobe("data/jeans.png")
    add_to_wardrobe("data/parka.png")
    add_to_wardrobe("data/shoes.png")