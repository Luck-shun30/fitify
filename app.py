import streamlit as st
import json
import os
from datetime import datetime, timedelta
from PIL import Image
import tempfile
from src.FitIdentification import image_to_json, add_to_wardrobe
from src.Wardrobe import OutfitSuggestionCrew

# Page configuration
st.set_page_config(
    page_title="Shipwrecked Outfit Suggestion",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_settings' not in st.session_state:
    st.session_state.user_settings = {
        'name': 'User',
        'laundry_cycle_days': 7,
        'location': 'Chicago, US',
        'preferred_formality': 'Casual',
        'preferred_activity': 'General'
    }

if 'wardrobe_items' not in st.session_state:
    try:
        with open("data/wardrobe.json", "r") as f:
            wardrobe_data = json.load(f)
            st.session_state.wardrobe_items = wardrobe_data["items"]
    except FileNotFoundError:
        st.session_state.wardrobe_items = []

if 'outfit_history' not in st.session_state:
    st.session_state.outfit_history = []

def save_user_settings():
    """Save user settings to a JSON file"""
    with open("data/user_settings.json", "w") as f:
        json.dump(st.session_state.user_settings, f, indent=2)

def load_user_settings():
    """Load user settings from JSON file"""
    try:
        with open("data/user_settings.json", "r") as f:
            st.session_state.user_settings = json.load(f)
    except FileNotFoundError:
        pass

def save_wardrobe():
    """Save wardrobe items to JSON file"""
    wardrobe_data = {"items": st.session_state.wardrobe_items}
    with open("data/wardrobe.json", "w") as f:
        json.dump(wardrobe_data, f, indent=2)

def add_clothing_item(uploaded_file):
    """Add a new clothing item to the wardrobe, enforcing a strict ID naming convention."""
    if uploaded_file is not None:
        try:
            # Create a temporary file to be processed by the AI
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Process the image to get its properties
            with st.spinner("Analyzing clothing item..."):
                item_data = image_to_json(tmp_path)

            # Enforce the strict ID naming convention (top#, bottom#, shoe#)
            item_type = item_data.get('type', '').lower()
            prefix = ""
            if item_type in ['shirt', 't-shirt', 'sweater', 'parka', 'top']:
                prefix = 'top'
            elif item_type in ['pants', 'shorts', 'bottom']:
                prefix = 'bottom'
            elif item_type == 'shoes':
                prefix = 'shoe'
            
            if not prefix:
                st.error(f"Unknown item type: '{item_type}'. Cannot generate a standardized ID.")
                os.unlink(tmp_path) # Clean up temp file
                return False

            # Find the highest number for the given prefix to determine the next ID
            max_num = 0
            for item in st.session_state.wardrobe_items:
                if item['id'].startswith(prefix):
                    try:
                        # Extract number from IDs like "top1", "shoe12"
                        num = int(item['id'][len(prefix):])
                        if num > max_num:
                            max_num = num
                    except (ValueError, IndexError):
                        # Ignore malformed IDs
                        continue
            
            # Set the new, standardized ID
            new_id = f"{prefix}{max_num + 1}"
            item_data['id'] = new_id
            
            # Add the item with the new ID to the wardrobe
            st.session_state.wardrobe_items.append(item_data)
            save_wardrobe()
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            st.success(f"✅ Added {item_data['type']} as '{item_data['id']}' to your wardrobe!")
            return True
            
        except Exception as e:
            st.error(f"❌ Error processing image: {str(e)}")
            # Ensure temp file is cleaned up on error as well
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return False
    return False

def display_wardrobe_item(item, show_actions=True, unique_key=""):
    """Display a single wardrobe item with image and details"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if os.path.exists(item.get('image', '')):
            image = Image.open(item['image'])
            st.image(image, caption=item['id'], use_column_width=True)
        else:
            st.image("data/tshirt.png", caption="Image not found", use_column_width=True)
    
    with col2:
        st.write(f"**Type:** {item['type'].title()}")
        st.write(f"**Material:** {item['form'].title()}")
        st.write(f"**Color:** {item['color'].title()}")
        st.write(f"**Weather:** {', '.join(item['weather']).title()}")
        if item.get('notes'):
            st.write(f"**Notes:** {item['notes']}")
        
        if show_actions:
            # Use unique key to prevent duplicate widget errors
            button_key = f"remove_{item['id']}_{unique_key}"
            if st.button(f"Remove {item['id']}", key=button_key):
                st.session_state.wardrobe_items = [i for i in st.session_state.wardrobe_items if i['id'] != item['id']]
                save_wardrobe()
                st.rerun()

def filter_items_by_type(items, item_type):
    """Filter wardrobe items by type"""
    return [item for item in items if item['type'].lower() == item_type.lower()]

def display_outfit_suggestion(suggestion, wardrobe_items):
    """
    Display outfit suggestion with robust handling of different data structures.
    This function will intelligently find the outfit data within the suggestion object.
    """
    if not suggestion:
        st.warning("No outfit suggestion available.")
        return

    # Intelligently find the 'outfits' list from various possible structures
    outfits = []
    if isinstance(suggestion, dict):
        if 'outfits' in suggestion and isinstance(suggestion['outfits'], list):
            outfits = suggestion['outfits']
        elif 'suggestions' in suggestion and isinstance(suggestion['suggestions'], dict):
            if 'outfits' in suggestion['suggestions']:
                outfits = suggestion['suggestions']['outfits']
            elif 'outfit' in suggestion['suggestions']:
                outfits = [suggestion['suggestions']['outfit']]

    if not outfits:
        st.warning("No outfit could be generated from the available items. Try adding more clothes to your wardrobe!")
        return
    
    # Find the first valid outfit from the list and parse it into a standard format
    outfit_to_display = None
    for o in outfits:
        parsed_outfit = {}
        if isinstance(o, dict):
            # Handle the new format with an 'items' list
            if 'items' in o and isinstance(o['items'], list):
                for item_id in o['items']:
                    item_details = next((item for item in wardrobe_items if item['id'] == item_id), None)
                    if item_details:
                        item_type = item_details.get('type', '').lower()
                        if item_type in ['shirt', 't-shirt', 'sweater', 'parka', 'top']:
                            parsed_outfit['top'] = item_id
                        elif item_type in ['pants', 'shorts', 'bottom']:
                            parsed_outfit['bottom'] = item_id
                        elif item_type == 'shoes':
                            parsed_outfit['shoes'] = item_id
            # Handle the old format with direct keys
            elif 'top' in o or 'bottom' in o or 'shoes' in o:
                parsed_outfit['top'] = o.get('top')
                parsed_outfit['bottom'] = o.get('bottom')
                parsed_outfit['shoes'] = o.get('shoes')
        
        # If we successfully parsed a valid outfit, use it and stop searching
        if parsed_outfit.get('top') or parsed_outfit.get('bottom') or parsed_outfit.get('shoes'):
            outfit_to_display = parsed_outfit
            break

    if not outfit_to_display:
        st.warning("The generated outfit was empty. Please try again.")
        return

    col1, col2, col3 = st.columns(3)
    
    # Display top
    if outfit_to_display.get('top'):
        with col1:
            st.write("**👕 Top**")
            top_item = next((item for item in wardrobe_items if item['id'] == outfit_to_display['top']), None)
            if top_item:
                display_wardrobe_item(top_item, show_actions=False, unique_key="suggestion_top")
            else:
                st.write(f"*{outfit_to_display['top']} (not found in wardrobe)*")
    
    # Display bottom
    if outfit_to_display.get('bottom'):
        with col2:
            st.write("**👖 Bottom**")
            bottom_item = next((item for item in wardrobe_items if item['id'] == outfit_to_display['bottom']), None)
            if bottom_item:
                display_wardrobe_item(bottom_item, show_actions=False, unique_key="suggestion_bottom")
            else:
                st.write(f"*{outfit_to_display['bottom']} (not found in wardrobe)*")
    
    # Display shoes
    if outfit_to_display.get('shoes'):
        with col3:
            st.write("**👟 Shoes**")
            shoe_item = next((item for item in wardrobe_items if item['id'] == outfit_to_display['shoes']), None)
            if shoe_item:
                display_wardrobe_item(shoe_item, show_actions=False, unique_key="suggestion_shoes")
            else:
                st.write(f"*{outfit_to_display['shoes']} (not found in wardrobe)*")
    
    # Weather info
    if 'weather' in suggestion and isinstance(suggestion['weather'], dict):
        raw_data = suggestion['weather'].get('raw_data', {})
        temp = raw_data.get('temperature', 'N/A')
        conditions = raw_data.get('conditions', 'N/A')
        st.info(f"🌤️ Weather: {temp}°F, {conditions}")
    
    # Recommendations
    if 'suggestions' in suggestion and isinstance(suggestion['suggestions'], dict):
        recommendations = suggestion['suggestions'].get('recommendations', [])
    elif 'recommendations' in suggestion and isinstance(suggestion['recommendations'], list):
        recommendations = suggestion['recommendations']
    else:
        recommendations = []

    if recommendations:
        st.write("**💡 Recommendations:**")
        for rec in recommendations:
            st.write(f"• {rec}")

