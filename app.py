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

def main_page():
    """Main dashboard page"""
    st.title("🏠 Dashboard")
    st.write(f"Welcome back, {st.session_state.user_settings['name']}!")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items", len(st.session_state.wardrobe_items))
    
    with col2:
        tops = filter_items_by_type(st.session_state.wardrobe_items, "t-shirt") + \
               filter_items_by_type(st.session_state.wardrobe_items, "shirt") + \
               filter_items_by_type(st.session_state.wardrobe_items, "sweater")
        st.metric("Tops", len(tops))
    
    with col3:
        pants = filter_items_by_type(st.session_state.wardrobe_items, "pants")
        st.metric("Pants", len(pants))
    
    with col4:
        shoes = filter_items_by_type(st.session_state.wardrobe_items, "shoes")
        st.metric("Shoes", len(shoes))
    
    # Quick outfit suggestion
    st.subheader("🎯 Quick Outfit Suggestion")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        formality = st.selectbox("Formality", ["Casual", "Business Casual", "Formal"], key="quick_formality")
    with col2:
        activity = st.selectbox("Activity", ["General", "Work", "School", "Exercise", "Social"], key="quick_activity")
    with col3:
        if st.button("Generate Outfit", key="quick_generate"):
            if len(st.session_state.wardrobe_items) >= 3:
                try:
                    outfit_crew = OutfitSuggestionCrew(st.session_state.wardrobe_items)
                    suggestion = outfit_crew.suggest_outfit(
                        location=st.session_state.user_settings['location'],
                        formality=formality,
                        activity=activity
                    )
                    st.session_state.current_suggestion = suggestion
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating outfit: {str(e)}")
            else:
                st.warning("You need at least 3 items in your wardrobe to generate an outfit.")
    
    # Display current suggestion
    if 'current_suggestion' in st.session_state:
        st.subheader("✨ Your Suggested Outfit")
        display_outfit_suggestion(st.session_state.current_suggestion, st.session_state.wardrobe_items)

def wardrobe_page():
    """Wardrobe management page"""
    st.title("👕 Wardrobe Management")
    
    # Add new item section
    st.subheader("➕ Add New Clothing Item")
    
    uploaded_file = st.file_uploader(
        "Upload an image of your clothing item",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear image of the clothing item you want to add to your wardrobe"
    )
    
    if uploaded_file is not None:
        # Show preview
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=200)
        
        if st.button("Add to Wardrobe"):
            if add_clothing_item(uploaded_file):
                st.rerun()
    
    # Display current wardrobe
    st.subheader("📁 Your Wardrobe")
    
    if not st.session_state.wardrobe_items:
        st.info("Your wardrobe is empty. Add some clothing items to get started!")
    else:
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.selectbox(
                "Filter by type",
                ["All", "t-shirt", "shirt", "sweater", "pants", "shoes", "parka"],
                key="wardrobe_filter"
            )
        with col2:
            search_term = st.text_input("Search by name or color", key="wardrobe_search")
        
        # Filter items
        filtered_items = st.session_state.wardrobe_items
        if filter_type != "All":
            filtered_items = filter_items_by_type(filtered_items, filter_type)
        
        if search_term:
            filtered_items = [
                item for item in filtered_items 
                if search_term.lower() in item['id'].lower() or 
                   search_term.lower() in item['color'].lower()
            ]
        
        # Display items
        if filtered_items:
            for i, item in enumerate(filtered_items):
                with st.expander(f"{item['id']} - {item['type'].title()}", expanded=False):
                    display_wardrobe_item(item, unique_key=f"wardrobe_{i}")
        else:
            st.info("No items match your current filters.")

def outfit_generator_page():
    """Outfit generation page with item swapping functionality"""
    st.title("🎨 Outfit Generator")

    # Initialize session state for this page if it doesn't exist
    if 'generator_outfit' not in st.session_state:
        st.session_state.generator_outfit = None
    if 'generator_context' not in st.session_state:
        st.session_state.generator_context = {}

    # --- Outfit Context ---
    st.subheader("⚙️ Outfit Context")
    col1, col2, col3 = st.columns(3)
    with col1:
        formality = st.selectbox("Formality Level", ["Casual", "Business Casual", "Formal"], key="outfit_formality")
    with col2:
        activity = st.selectbox("Activity", ["General", "Work", "School", "Exercise", "Social"], key="outfit_activity")
    with col3:
        location = st.text_input("Location", value=st.session_state.user_settings['location'], key="outfit_location")

    # --- Generate Button ---
    if st.button("✨ Generate Outfit", key="generate_full_outfit"):
        if len(st.session_state.wardrobe_items) >= 3:
            try:
                outfit_crew = OutfitSuggestionCrew(st.session_state.wardrobe_items)
                with st.spinner("Generating your perfect outfit..."):
                    suggestion = outfit_crew.suggest_outfit(
                        location=location,
                        formality=formality,
                        activity=activity
                    )
                
                # Intelligently find and parse the first valid outfit from the response
                outfits = []
                if isinstance(suggestion, dict):
                    if 'outfits' in suggestion and isinstance(suggestion.get('outfits'), list):
                        outfits = suggestion['outfits']
                    elif 'suggestions' in suggestion and isinstance(suggestion.get('suggestions'), dict):
                        outfits = suggestion['suggestions'].get('outfits', [])
                
                parsed_outfit = {}
                if outfits:
                    outfit_data = outfits[0]
                    if 'items' in outfit_data and isinstance(outfit_data['items'], list):
                        for item_id in outfit_data['items']:
                            item_details = next((item for item in st.session_state.wardrobe_items if item['id'] == item_id), None)
                            if item_details:
                                item_type = item_details.get('type', '').lower()
                                if item_type in ['shirt', 't-shirt', 'sweater', 'parka', 'top'] and 'top' not in parsed_outfit:
                                    parsed_outfit['top'] = item_id
                                elif item_type in ['pants', 'shorts', 'bottom'] and 'bottom' not in parsed_outfit:
                                    parsed_outfit['bottom'] = item_id
                                elif item_type == 'shoes' and 'shoes' not in parsed_outfit:
                                    parsed_outfit['shoes'] = item_id
                    else: # Handle old format
                        parsed_outfit = {'top': outfit_data.get('top'), 'bottom': outfit_data.get('bottom'), 'shoes': outfit_data.get('shoes')}

                if parsed_outfit:
                    st.session_state.generator_outfit = parsed_outfit
                    st.session_state.generator_context = {
                        'weather': suggestion.get('weather'),
                        'recommendations': suggestion.get('recommendations', suggestion.get('suggestions', {}).get('recommendations', []))
                    }
                else:
                    st.session_state.generator_outfit = None
                    st.warning("Could not generate a complete outfit. Please try again or add more items.")

                st.rerun()

            except Exception as e:
                st.error(f"Error generating outfit: {str(e)}")
        else:
            st.warning("You need at least 3 items in your wardrobe (top, bottom, shoes) to generate an outfit.")
    
    # --- Display Generated Outfit and Swap Buttons ---
    if st.session_state.generator_outfit:
        st.markdown("---")
        st.subheader("🎯 Your Outfit")
        current_outfit = st.session_state.generator_outfit
        
        # Display current items
        col1, col2, col3 = st.columns(3)
        with col1:
            if current_outfit.get('top'):
                item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit['top']), None)
                if item:
                    display_wardrobe_item(item, show_actions=False, unique_key="gen_top")
        with col2:
            if current_outfit.get('bottom'):
                item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit['bottom']), None)
                if item:
                    display_wardrobe_item(item, show_actions=False, unique_key="gen_bottom")
        with col3:
            if current_outfit.get('shoes'):
                item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit['shoes']), None)
                if item:
                    display_wardrobe_item(item, show_actions=False, unique_key="gen_shoes")

        st.markdown("---")
        st.write("Not quite right? Swap an item:")
        
        # --- Swap Buttons ---
        b_col1, b_col2, b_col3 = st.columns(3)
        outfit_crew = OutfitSuggestionCrew(st.session_state.wardrobe_items)

        with b_col1:
            if st.button("🔄 Swap Top", key="swap_top"):
                with st.spinner("Finding a new top..."):
                    # Safely build context for the AI
                    current_bottoms = []
                    if current_outfit.get('bottom'):
                        item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit.get('bottom')), None)
                        if item:
                            current_bottoms.append(item)

                    current_shoes = []
                    if current_outfit.get('shoes'):
                        item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit.get('shoes')), None)
                        if item:
                            current_shoes.append(item)

                    suggestions = outfit_crew.suggest_tops(location=location, formality=formality, activity=activity, current_bottoms=current_bottoms, current_shoes=current_shoes)
                    # Correctly parse the suggestions from the response
                    new_tops = suggestions.get('tops', [])
                    # Find a top that is different from the current one
                    new_top_id = next((top for top in new_tops if top != current_outfit.get('top')), None)
                    
                    if new_top_id:
                        st.session_state.generator_outfit['top'] = new_top_id
                        st.rerun()
                    else:
                        st.warning("No other suitable tops found.")

        with b_col2:
            if st.button("🔄 Swap Bottom", key="swap_bottom"):
                with st.spinner("Finding new bottoms..."):
                    # Safely build context
                    current_tops = []
                    if current_outfit.get('top'):
                        item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit.get('top')), None)
                        if item:
                            current_tops.append(item)
                    
                    current_shoes = []
                    if current_outfit.get('shoes'):
                        item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit.get('shoes')), None)
                        if item:
                            current_shoes.append(item)

                    suggestions = outfit_crew.suggest_bottoms(location=location, formality=formality, activity=activity, current_tops=current_tops, current_shoes=current_shoes)
                    new_bottoms = suggestions.get('bottoms', [])
                    new_bottom_id = next((b for b in new_bottoms if b != current_outfit.get('bottom')), None)
                    
                    if new_bottom_id:
                        st.session_state.generator_outfit['bottom'] = new_bottom_id
                        st.rerun()
                    else:
                        st.warning("No other suitable bottoms found.")

        with b_col3:
            if st.button("🔄 Swap Shoes", key="swap_shoes"):
                with st.spinner("Finding new shoes..."):
                    # Safely build context
                    current_tops = []
                    if current_outfit.get('top'):
                        item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit.get('top')), None)
                        if item:
                            current_tops.append(item)

                    current_bottoms = []
                    if current_outfit.get('bottom'):
                        item = next((i for i in st.session_state.wardrobe_items if i['id'] == current_outfit.get('bottom')), None)
                        if item:
                            current_bottoms.append(item)

                    suggestions = outfit_crew.suggest_shoes(location=location, formality=formality, activity=activity, current_tops=current_tops, current_bottoms=current_bottoms)
                    new_shoes = suggestions.get('shoes', [])
                    new_shoe_id = next((s for s in new_shoes if s != current_outfit.get('shoes')), None)

                    if new_shoe_id:
                        st.session_state.generator_outfit['shoes'] = new_shoe_id
                        st.rerun()
                    else:
                        st.warning("No other suitable shoes found.")
        
        # --- Display Context ---
        context = st.session_state.generator_context
        if context.get('weather'):
            weather_data = context['weather'].get('raw_data', {})
            st.info(f"🌤️ Weather: {weather_data.get('temperature', 'N/A')}°F, {weather_data.get('conditions', 'N/A')}")
        if context.get('recommendations'):
            st.write("**💡 Recommendations:**")
            for rec in context['recommendations']:
                st.write(f"• {rec}")

def settings_page():
    """Settings page for user preferences"""
    st.title("⚙️ Settings")
    
    # Load existing settings
    load_user_settings()
    
    st.subheader("👤 User Profile")
    
    # User name
    name = st.text_input("Your Name", value=st.session_state.user_settings.get('name', 'User'))
    st.session_state.user_settings['name'] = name
    
    # Laundry cycle
    laundry_cycle = st.number_input(
        "Laundry Cycle (days)",
        min_value=1,
        max_value=30,
        value=st.session_state.user_settings.get('laundry_cycle_days', 7),
        help="How often do you do laundry?"
    )
    st.session_state.user_settings['laundry_cycle_days'] = laundry_cycle
    
    # Default location
    default_location = st.text_input(
        "Default Location",
        value=st.session_state.user_settings.get('location', 'Chicago, US'),
        help="Your default location for weather-based outfit suggestions"
    )
    st.session_state.user_settings['location'] = default_location
    
    # Preferred formality
    preferred_formality = st.selectbox(
        "Preferred Formality Level",
        ["Casual", "Business Casual", "Formal"],
        index=["Casual", "Business Casual", "Formal"].index(
            st.session_state.user_settings.get('preferred_formality', 'Casual')
        )
    )
    st.session_state.user_settings['preferred_formality'] = preferred_formality
    
    # Preferred activity
    preferred_activity = st.selectbox(
        "Preferred Activity",
        ["General", "Work", "School", "Exercise", "Social"],
        index=["General", "Work", "School", "Exercise", "Social"].index(
            st.session_state.user_settings.get('preferred_activity', 'General')
        )
    )
    st.session_state.user_settings['preferred_activity'] = preferred_activity
    
    # Save button
    if st.button("💾 Save Settings"):
        save_user_settings()
        st.success("Settings saved successfully!")
    
    # Data management
    st.subheader("🗄️ Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Wardrobe Data"):
            wardrobe_data = {"items": st.session_state.wardrobe_items}
            st.download_button(
                label="Download JSON",
                data=json.dumps(wardrobe_data, indent=2),
                file_name=f"wardrobe_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("🗑️ Clear All Data"):
            if st.checkbox("I understand this will delete all my wardrobe data"):
                st.session_state.wardrobe_items = []
                save_wardrobe()
                st.success("All wardrobe data cleared!")
                st.rerun()
    
    # App information
    st.subheader("ℹ️ App Information")
    st.write("**Shipwrecked Outfit Suggestion**")
    st.write("Version: 1.0.0")
    st.write("Powered by Mistral AI and CrewAI")

def outfit_history_page():
    """Outfit history and tracking page"""
    st.title("📅 Outfit History")
    
    # Add new outfit log
    st.subheader("➕ Log Today's Outfit")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_top = st.selectbox(
            "Top worn",
            ["None"] + [item['id'] for item in filter_items_by_type(st.session_state.wardrobe_items, "t-shirt") + 
                       filter_items_by_type(st.session_state.wardrobe_items, "shirt") + 
                       filter_items_by_type(st.session_state.wardrobe_items, "sweater")]
        )
        
        selected_pants = st.selectbox(
            "Pants worn",
            ["None"] + [item['id'] for item in filter_items_by_type(st.session_state.wardrobe_items, "pants")]
        )
        
        selected_shoes = st.selectbox(
            "Shoes worn",
            ["None"] + [item['id'] for item in filter_items_by_type(st.session_state.wardrobe_items, "shoes")]
        )
    
    with col2:
        activity = st.selectbox("Activity", ["General", "Work", "School", "Exercise", "Social"])
        formality = st.selectbox("Formality", ["Casual", "Business Casual", "Formal"])
        notes = st.text_area("Notes (optional)")
    
    if st.button("Log Outfit"):
        outfit_log = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "top": selected_top if selected_top != "None" else None,
            "pants": selected_pants if selected_pants != "None" else None,
            "shoes": selected_shoes if selected_shoes != "None" else None,
            "activity": activity,
            "formality": formality,
            "notes": notes
        }
        
        st.session_state.outfit_history.append(outfit_log)
        
        # Save to file
        with open("data/outfit_history.json", "w") as f:
            json.dump(st.session_state.outfit_history, f, indent=2)
        
        st.success("Outfit logged successfully!")
        st.rerun()
    
    # Display outfit history
    st.subheader("📋 Recent Outfits")
    
    if not st.session_state.outfit_history:
        st.info("No outfit history yet. Start logging your outfits!")
    else:
        # Load history from file
        try:
            with open("data/outfit_history.json", "r") as f:
                st.session_state.outfit_history = json.load(f)
        except FileNotFoundError:
            pass
        
        # Display recent outfits (last 10)
        recent_outfits = st.session_state.outfit_history[-10:]
        
        for outfit in reversed(recent_outfits):
            with st.expander(f"{outfit['date']} - {outfit['activity']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Top:** {outfit.get('top', 'None')}")
                    st.write(f"**Pants:** {outfit.get('pants', 'None')}")
                    st.write(f"**Shoes:** {outfit.get('shoes', 'None')}")
                
                with col2:
                    st.write(f"**Activity:** {outfit['activity']}")
                    st.write(f"**Formality:** {outfit['formality']}")
                    if outfit.get('notes'):
                        st.write(f"**Notes:** {outfit['notes']}")