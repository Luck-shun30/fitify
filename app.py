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

