# Shipwrecked Outfit Suggestion

An AI-powered wardrobe management and outfit suggestion app built with Streamlit, Mistral AI, and CrewAI.

## Features

- **👕 Wardrobe Management**: Upload and classify clothing items using AI
- **🎨 Outfit Generator**: Get personalized outfit suggestions based on weather, formality, and activity
- **📅 Outfit History**: Track what you've worn and when
- **⚙️ Settings**: Customize your preferences and laundry cycle
- **🌤️ Weather Integration**: Get weather-based outfit recommendations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Luck-shun30/fitify
cd shipwrecked_outfit_suggestion
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
MISTRAL_API_KEY=your_mistral_api_key_here
PYTHON_WEATHER_API_KEY=your_weather_api_key_here
```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Pages

### 🏠 Dashboard
- Overview of your wardrobe statistics
- Quick outfit suggestions
- Weather information

### 👕 Wardrobe
- Upload new clothing items
- View and manage your wardrobe
- Filter and search items

### 🎨 Outfit Generator
- Generate outfit suggestions by category (tops, pants, shoes)
- Complete outfit recommendations
- Weather-aware suggestions

### 📅 History
- Log outfits you've worn
- View outfit history
- Track your style patterns

### ⚙️ Settings
- Customize user preferences
- Set laundry cycle
- Export/import wardrobe data

## How it Works

1. **Image Classification**: Uses Mistral AI's Pixtral model to analyze clothing images and extract details like type, material, color, and weather suitability.

2. **Outfit Generation**: Uses CrewAI agents to generate personalized outfit suggestions based on:
   - Current weather conditions
   - Formality requirements
   - Activity type
   - Available wardrobe items

3. **Weather Integration**: Fetches real-time weather data to provide context-aware recommendations.

## File Structure

```
shipwrecked_outfit_suggestion/
├── app.py                 # Main Streamlit application
├── src/
│   ├── FitIdentification.py  # AI-powered clothing classification
│   └── Wardrobe.py          # Outfit suggestion logic
├── data/
│   ├── wardrobe.json       # Wardrobe data
│   ├── user_settings.json  # User preferences
│   └── outfit_history.json # Outfit history
├── wardrobe/              # Stored clothing images
└── requirements.txt       # Python dependencies
```

## Requirements

- Python 3.8+
- Mistral AI API key
- Python Weather API key (optional, for weather features)

## License

This project is licensed under the MIT License. 
