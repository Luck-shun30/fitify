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