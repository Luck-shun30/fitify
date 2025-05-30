from crewai import Agent, Task, Crew, Process, LLM
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import pyowm
from ..tools.calendar_manager import CalendarManager

# Load environment variables
load_dotenv()

class WeatherAgent:
    def __init__(self):
        self.llm = LLM(
            model="mistral/mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.7
        )
        
        self.agent = Agent(
            role='Weather Analyst',
            goal='Fetch and analyze weather data for outfit suggestions',
            backstory="""You are an expert at analyzing weather data and determining appropriate clothing recommendations.
            You understand how different weather conditions affect clothing choices and can provide detailed weather context
            for outfit planning.""",
            verbose=True,
            llm=self.llm
        )
        
        # Initialize Python Weather
        api_key = os.getenv("PYTHON_WEATHER_API_KEY")
        if not api_key:
            raise ValueError("PYTHON_WEATHER_API_KEY environment variable is not set")
        self.owm = pyowm.OWM(api_key)
    
    def get_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather data using Python Weather."""
        try:
            # Get weather data
            observation = self.owm.weather_manager().weather_at_place(location)
            if not observation:
                raise ValueError(f"No weather data found for location: {location}")
            
            weather = observation.weather
            
            # Get temperature in Fahrenheit
            temp_f = weather.temperature('fahrenheit')['temp']
            
            # Create weather analysis prompt
            weather_prompt = f"""Analyze the following weather data and provide clothing recommendations:
            Temperature: {temp_f}°F
            Conditions: {weather.detailed_status}
            Humidity: {weather.humidity}%
            Wind Speed: {weather.wind()['speed']} mph
            
            Provide recommendations in JSON format:
            {{
                "temperature_category": "cold|cool|mild|warm|hot",
                "weather_conditions": ["rainy", "windy", "sunny", etc],
                "clothing_recommendations": ["light layers", "rain gear", etc],
                "special_considerations": ["UV protection", "wind resistance", etc]
            }}"""
            
            weather_task = Task(
                description=weather_prompt,
                agent=self.agent,
                expected_output="JSON formatted weather analysis with clothing recommendations."
            )
            
            crew = Crew(
                agents=[self.agent],
                tasks=[weather_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                if isinstance(result, str):
                    # Remove markdown code block formatting if present
                    if result.startswith('```json'):
                        result = result[7:]  # Remove ```json
                    if result.startswith('```'):
                        result = result[3:]  # Remove ```
                    if result.endswith('```'):
                        result = result[:-3]  # Remove trailing ```
                    result = result.strip()  # Remove any extra whitespace
                    weather_analysis = json.loads(result)
                else:
                    # Handle non-string results
                    result_str = result.raw if hasattr(result, 'raw') else str(result)
                    if result_str.startswith('```json'):
                        result_str = result_str[7:]
                    if result_str.startswith('```'):
                        result_str = result_str[3:]
                    if result_str.endswith('```'):
                        result_str = result_str[:-3]
                    result_str = result_str.strip()
                    weather_analysis = json.loads(result_str)
            except json.JSONDecodeError as e:
                print(f"Error parsing weather analysis: {str(e)}")
                print(f"Raw result: {result}")
                # Create a default analysis based on temperature
                weather_analysis = {
                    "temperature_category": "mild" if 60 <= temp_f <= 75 else "warm" if temp_f > 75 else "cool",
                    "weather_conditions": [weather.detailed_status.lower()],
                    "clothing_recommendations": ["appropriate layers for the temperature"],
                    "special_considerations": ["check local weather conditions"]
                }
            
            return {
                'raw_data': {
                    'temperature': temp_f,
                    'conditions': weather.detailed_status,
                    'humidity': weather.humidity,
                    'wind_speed': weather.wind()['speed']
                },
                'analysis': weather_analysis
            }
            
        except ValueError as e:
            print(f"Error: {str(e)}")
            return None
        except Exception as e:
            print(f"Error fetching weather data: {str(e)}")
            return None

class WardrobeAgent:
    def __init__(self):
        self.llm = LLM(
            model="mistral/mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.7
        )
        
        self.agent = Agent(
            role='Wardrobe Manager',
            goal='Manage and filter clothing items based on context',
            backstory="""You are an expert at managing wardrobes and suggesting appropriate clothing combinations.
            You understand different clothing styles, formality levels, and weather compatibility.
            You can filter and match clothing items based on multiple criteria.""",
            verbose=True,
            llm=self.llm
        )
        
        # Load wardrobe database
        self.wardrobe_db = self._load_wardrobe_db()
        # Initialize laundry manager
        # self.laundry_manager = LaundryManager()
    
    def _load_wardrobe_db(self) -> Dict[str, Any]:
        """Load wardrobe database from JSON file."""
        try:
            with open('data/wardrobe.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default wardrobe database
            default_db = {
                'items': [
                    {
                        'id': 'item1',
                        'type': 'hoodie',
                        'form': 'casual',
                        'weather': ['cool', 'mild'],
                        'color': 'black',
                        'notes': 'Comfortable for everyday wear'
                    }
                ]
            }
            os.makedirs('data', exist_ok=True)
            with open('data/wardrobe.json', 'w') as f:
                json.dump(default_db, f, indent=2)
            return default_db
    
    def filter_items(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter wardrobe items based on context."""
        # First filter by laundry availability
        available_items = self.laundry_manager.get_available_items(self.wardrobe_db['items'])
        
        filter_task = Task(
            description=f"""Filter the wardrobe items based on the following context:
            Weather: {context.get('weather', {})}
            Formality: {context.get('formality', 'casual')}
            Activity: {context.get('activity', 'general')}
            
            Available Items:
            {json.dumps(available_items, indent=2)}
            
            Return filtered items in JSON format:
            {{
                "matching_items": [
                    {{
                        "id": "item_id",
                        "type": "item_type",
                        "form": "formality",
                        "weather": ["compatible_weather"],
                        "color": "color",
                        "notes": "notes"
                    }}
                ],
                "excluded_items": [
                    {{
                        "id": "item_id",
                        "reason": "exclusion_reason"
                    }}
                ]
            }}""",
            agent=self.agent,
            expected_output="JSON formatted list of matching and excluded wardrobe items."
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[filter_task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Parse the result
        try:
            if isinstance(result, str):
                # Remove markdown code block formatting if present
                if result.startswith('```json'):
                    result = result[7:]  # Remove ```json
                if result.startswith('```'):
                    result = result[3:]  # Remove ```
                if result.endswith('```'):
                    result = result[:-3]  # Remove trailing ```
                result = result.strip()  # Remove any extra whitespace
                return json.loads(result)
            else:
                # Handle non-string results
                result_str = result.raw if hasattr(result, 'raw') else str(result)
                if result_str.startswith('```json'):
                    result_str = result_str[7:]
                if result_str.startswith('```'):
                    result_str = result_str[3:]
                if result_str.endswith('```'):
                    result_str = result_str[:-3]
                result_str = result_str.strip()
                return json.loads(result_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing wardrobe items: {str(e)}")
            print(f"Raw result: {result}")
            # Return a default filtered wardrobe
            return {
                "matching_items": [
                    {
                        "id": "default",
                        "type": "t-shirt",
                        "form": "casual",
                        "weather": ["mild"],
                        "color": "neutral",
                        "notes": "Basic casual item"
                    }
                ],
                "excluded_items": [
                    {
                        "id": "all_others",
                        "reason": "Error occurred while filtering items"
                    }
                ]
            }

class OutfitGeneratorAgent:
    def __init__(self):
        self.llm = LLM(
            model="mistral/mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.7
        )
        
        self.agent = Agent(
            role='Outfit Generator',
            goal='Generate appropriate outfit combinations',
            backstory="""You are an expert at creating stylish and appropriate outfit combinations.
            You understand how to match different clothing items, consider weather conditions,
            and maintain a good balance of style and comfort.""",
            verbose=True,
            llm=self.llm
        )
    
    def generate_outfit(self, context: Dict[str, Any], available_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate outfit suggestions based on context and available items."""
        outfit_task = Task(
            description=f"""Generate outfit suggestions based on the following context:
            Weather: {context.get('weather', {})}
            Formality: {context.get('formality', 'casual')}
            Activity: {context.get('activity', 'general')}
            
            Available Items:
            {json.dumps(available_items, indent=2)}
            
            Return outfit suggestions in JSON format:
            {{
                "outfits": [
                    {{
                        "name": "outfit_name",
                        "items": [
                            {{
                                "id": "item_id",
                                "type": "item_type",
                                "color": "color"
                            }}
                        ],
                        "shoes": {{
                            "id": "shoe_id",
                            "type": "shoe_type",
                            "color": "color",
                            "style": "style_notes"
                        }},
                        "style_notes": "style_notes",
                        "weather_compatibility": "weather_compatibility",
                        "formality_level": "formality_level"
                    }}
                ],
                "recommendations": [
                    "recommendation1",
                    "recommendation2"
                ]
            }}""",
            agent=self.agent,
            expected_output="JSON formatted outfit suggestions with recommendations."
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[outfit_task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Parse the result
        try:
            if isinstance(result, str):
                # Remove markdown code block formatting if present
                if result.startswith('```json'):
                    result = result[7:]  # Remove ```json
                if result.startswith('```'):
                    result = result[3:]  # Remove ```
                if result.endswith('```'):
                    result = result[:-3]  # Remove trailing ```
                result = result.strip()  # Remove any extra whitespace
                return json.loads(result)
            else:
                # Handle non-string results
                result_str = result.raw if hasattr(result, 'raw') else str(result)
                if result_str.startswith('```json'):
                    result_str = result_str[7:]
                if result_str.startswith('```'):
                    result_str = result_str[3:]
                if result_str.endswith('```'):
                    result_str = result_str[:-3]
                result_str = result_str.strip()
                return json.loads(result_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing outfit suggestions: {str(e)}")
            print(f"Raw result: {result}")
            # Return a default outfit suggestion
            return {
                "outfits": [
                    {
                        "name": "Default Casual Outfit",
                        "items": [
                            {
                                "id": "default",
                                "type": "t-shirt",
                                "color": "neutral"
                            },
                            {
                                "id": "default",
                                "type": "pants",
                                "color": "neutral"
                            }
                        ],
                        "shoes": {
                            "id": "default",
                            "type": "sneakers",
                            "color": "neutral",
                            "style": "Comfortable casual sneakers"
                        },
                        "style_notes": "Basic casual outfit",
                        "weather_compatibility": "Suitable for mild weather",
                        "formality_level": "casual"
                    }
                ],
                "recommendations": [
                    "Check the weather forecast for more specific recommendations",
                    "Consider your activity level when choosing layers",
                    "Make sure your shoes are appropriate for the weather conditions"
                ]
            }

class OutfitSuggestionCrew:
    def __init__(self):
        self.weather_agent = WeatherAgent()
        self.wardrobe_agent = WardrobeAgent()
        self.outfit_generator = OutfitGeneratorAgent()
        
        # Initialize calendar manager
        credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH')
        if credentials_path:
            self.calendar_manager = CalendarManager(credentials_path)
        else:
            self.calendar_manager = None
    
    def _check_calendar_events(self) -> Dict[str, Any]:
        """Check calendar events for today to determine formality and activities."""
        if not self.calendar_manager:
            return {
                'formality': 'casual',
                'activities': []
            }
        
        try:
            # Get today's events
            today = datetime.now().date()
            events = self.calendar_manager.get_events(1)  # Get events for next 24 hours
            
            formality = 'casual'
            activities = []
            
            for event in events:
                start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                if start.date() == today:
                    # Check for formal events
                    if any(keyword in event['summary'].lower() for keyword in ['meeting', 'interview', 'competition', 'presentation']):
                        formality = 'formal'
                    
                    # Check for athletic activities
                    if any(keyword in event['summary'].lower() for keyword in ['practice', 'training', 'workout', 'gym']):
                        activities.append({
                            'type': 'athletic',
                            'time': start.strftime('%H:%M'),
                            'duration': event.get('duration', '1h')
                        })
            
            return {
                'formality': formality,
                'activities': activities
            }
            
        except Exception as e:
            print(f"Warning: Could not check calendar events: {str(e)}")
            return {
                'formality': 'casual',
                'activities': []
            }
    
    def suggest_outfit(self, location: str = "Chicago, US", formality: str = None, activity: str = None) -> Dict[str, Any]:
        """Generate outfit suggestions based on weather, wardrobe, and context."""
        # Get calendar events
        calendar_info = self._check_calendar_events()
        
        # Use calendar formality if not specified
        if formality is None:
            formality = calendar_info['formality']
        
        # Get weather data
        weather_data = self.weather_agent.get_weather(location)
        if not weather_data:
            return {"error": "Could not fetch weather data"}
        
        # Create context
        context = {
            'weather': weather_data['analysis'],
            'formality': formality,
            'activity': activity
        }
        
        # Filter wardrobe items
        filtered_items = self.wardrobe_agent.filter_items(context)
        
        # Generate outfit suggestions
        outfit_suggestions = self.outfit_generator.generate_outfit(
            context,
            filtered_items['matching_items']
        )
        
        # If there are athletic activities, generate additional athletic outfits
        if calendar_info['activities']:
            athletic_context = context.copy()
            athletic_context['activity'] = 'athletic'
            athletic_outfits = self.outfit_generator.generate_outfit(
                athletic_context,
                filtered_items['matching_items']
            )
            
            # Add athletic outfits to suggestions
            outfit_suggestions['athletic_outfits'] = athletic_outfits['outfits']
            outfit_suggestions['athletic_recommendations'] = athletic_outfits['recommendations']
        
        # Save the outfit suggestions to a markdown file
        with open('data/outfit_suggestions.md', 'w') as f:
            f.write('# Outfit Suggestions\n\n')
            
            # Weather information
            f.write('## Weather Information\n\n')
            f.write(f"Location: {location}\n")
            f.write(f"Temperature: {weather_data['raw_data']['temperature']}°F\n")
            f.write(f"Conditions: {weather_data['raw_data']['conditions']}\n")
            f.write(f"Humidity: {weather_data['raw_data']['humidity']}%\n")
            f.write(f"Wind Speed: {weather_data['raw_data']['wind_speed']} mph\n\n")
            
            # Weather analysis
            f.write('### Weather Analysis\n\n')
            f.write(f"Temperature Category: {weather_data['analysis']['temperature_category']}\n")
            f.write("Weather Conditions:\n")
            for condition in weather_data['analysis']['weather_conditions']:
                f.write(f"- {condition}\n")
            f.write("\nClothing Recommendations:\n")
            for rec in weather_data['analysis']['clothing_recommendations']:
                f.write(f"- {rec}\n")
            f.write("\nSpecial Considerations:\n")
            for consideration in weather_data['analysis']['special_considerations']:
                f.write(f"- {consideration}\n")
            f.write('\n')
            
            # Outfit suggestions
            f.write('## Outfit Suggestions\n\n')
            for outfit in outfit_suggestions['outfits']:
                f.write(f"### {outfit['name']}\n\n")
                f.write("Items:\n")
                for item in outfit['items']:
                    f.write(f"- {item['color']} {item['type']}\n")
                f.write(f"\nShoes:\n")
                f.write(f"- {outfit['shoes']['color']} {outfit['shoes']['type']} ({outfit['shoes']['style']})\n")
                f.write(f"\nStyle Notes: {outfit['style_notes']}\n")
                f.write(f"Weather Compatibility: {outfit['weather_compatibility']}\n")
                f.write(f"Formality Level: {outfit['formality_level']}\n\n")
            
            # Athletic outfits if any
            if 'athletic_outfits' in outfit_suggestions:
                f.write('## Athletic Outfits\n\n')
                for outfit in outfit_suggestions['athletic_outfits']:
                    f.write(f"### {outfit['name']}\n\n")
                    f.write("Items:\n")
                    for item in outfit['items']:
                        f.write(f"- {item['color']} {item['type']}\n")
                    f.write(f"\nShoes:\n")
                    f.write(f"- {outfit['shoes']['color']} {outfit['shoes']['type']} ({outfit['shoes']['style']})\n")
                    f.write(f"\nStyle Notes: {outfit['style_notes']}\n")
                    f.write(f"Weather Compatibility: {outfit['weather_compatibility']}\n")
                    f.write(f"Formality Level: {outfit['formality_level']}\n\n")
            
            # General recommendations
            f.write('## Recommendations\n\n')
            for rec in outfit_suggestions['recommendations']:
                f.write(f"- {rec}\n")
            
            # Athletic recommendations if any
            if 'athletic_recommendations' in outfit_suggestions:
                f.write('\n### Athletic Recommendations\n\n')
                for rec in outfit_suggestions['athletic_recommendations']:
                    f.write(f"- {rec}\n")
        
        return {
            'weather': weather_data,
            'available_items': filtered_items,
            'suggestions': outfit_suggestions,
            'calendar_info': calendar_info
        } 