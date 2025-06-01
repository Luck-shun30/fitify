import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from crewai import Agent, Task, Crew, Process, LLM
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import pyowm
from tools.calendar_manager import CalendarManager

load_dotenv()

class WeatherAgent:
    def __init__(self):
        self.owm = pyowm.OWM(os.getenv('PYTHON_WEATHER_API_KEY'))

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
                expected_output="JSON formatted weather analysis with clothing recommendations with no ``` or 'JSON' text outside the JSON code."
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
    def __init__(self, wardrobe_items: List[Dict[str, Any]]):
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
        self.wardrobe_items = wardrobe_items

    def filter(self, context: Dict[str, Any]):
        filter_task = Task(
            description=f"""Filter the wardrobe items based on the following context:
            Weather: {context.get('weather', {})}
            Formality: {context.get('formality', 'casual')}
            Activity: {context.get('activity', 'general')}
            
            Available Items:
            {json.dumps(self.wardrobe_items, indent=2)}
            
            Return filtered items in JSON format:
            {{
                "matching_items": [
                    id1: "item_id1",
                    id2: "item_id2",
                    id3: "item_id3",
                    ...,
                    idn: "item_idn"
                ],
            }}""",
            agent=self.agent,
            expected_output="JSON formatted list of matching items with no ``` or 'JSON' text outside the JSON code."
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[filter_task],
            verbose=True
        )
        
        result = crew.kickoff()

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
    
    def generate_tops(self, context: Dict[str, Any], available_items: List[Dict[str, Any]], current_bottoms: List[Dict[str, Any]], current_shoes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alternative top suggestions while keeping the same bottoms and shoes."""
        tops_task = Task(
            description=f"""Generate alternative top suggestions while keeping the same bottoms and shoes.
            Current Bottoms: {json.dumps(current_bottoms, indent=2)}
            Current Shoes: {json.dumps(current_shoes, indent=2)}
            
            Weather: {context.get('weather', {})}
            Formality: {context.get('formality', 'casual')}
            Activity: {context.get('activity', 'general')}

            Available Items (Only choose tops that match with the current bottoms and shoes):
            {json.dumps(available_items, indent=2)}

            Return only the new suggestion in JSON format:
            {{
                "tops": [
                    {{
                        "item_id": "item_id",
                        "compatibility_notes": "How well it matches with the current bottoms and shoes",
                        "style_notes": "Additional style notes"
                    }}
                ],
                "recommendations": [
                    "recommendation1",
                    "recommendation2"
                ]
            }}""",
            agent=self.agent,
            expected_output="JSON formatted top suggestions with recommendations."
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[tops_task],
            verbose=True
        )
        
        result = crew.kickoff()
        output = self._parse_result(result)
        output["tops"] = [output["tops"][0]]
        return output

    def generate_bottoms(self, context: Dict[str, Any], available_items: List[Dict[str, Any]], current_tops: List[Dict[str, Any]], current_shoes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alternative bottom suggestions while keeping the same tops and shoes."""
        bottoms_task = Task(
            description=f"""Generate alternative bottom suggestions while keeping the same tops and shoes.
            Current Tops: {json.dumps(current_tops, indent=2)}
            Current Shoes: {json.dumps(current_shoes, indent=2)}
            
            Weather: {context.get('weather', {})}
            Formality: {context.get('formality', 'casual')}
            Activity: {context.get('activity', 'general')}

            Available Items (Only choose bottoms that match with the current tops and shoes):
            {json.dumps(available_items, indent=2)}

            RETURN ONLY THE NEW SUGGESTION (NOT THE OLD BOTTOMS) IN JSON FORMAT:
            {{
                "bottoms": [
                    {{
                        "item_id": "item_id",
                        "compatibility_notes": "How well it matches with the current tops and shoes",
                        "style_notes": "Additional style notes"
                    }}
                ],
                "recommendations": [
                    "recommendation1",
                    "recommendation2"
                ]
            }}
            REMEMBER TO RETURN ONLY THE NEW SUGGESTION (NOT THE OLD BOTTOMS) IN JSON FORMAT.
            """,
            agent=self.agent,
            expected_output="JSON formatted bottom suggestions with recommendations."
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[bottoms_task],
            verbose=True
        )
        
        result = crew.kickoff()
        output = self._parse_result(result)
        output["bottoms"] = [output["bottoms"][0]]
        return output

    def generate_shoes(self, context: Dict[str, Any], available_items: List[Dict[str, Any]], current_tops: List[Dict[str, Any]], current_bottoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alternative shoe suggestions while keeping the same tops and bottoms."""
        shoes_task = Task(
            description=f"""Generate alternative shoe suggestions while keeping the same tops and bottoms.
            Current Tops: {json.dumps(current_tops, indent=2)}
            Current Bottoms: {json.dumps(current_bottoms, indent=2)}
            
            Weather: {context.get('weather', {})}
            Formality: {context.get('formality', 'casual')}
            Activity: {context.get('activity', 'general')}

            Available Items (Only choose shoes that match with the current tops and bottoms):
            {json.dumps(available_items, indent=2)}

            Return only the new suggestion in JSON format:
            {{
                "shoes": [
                    {{
                        "item_id": "item_id",
                        "compatibility_notes": "How well it matches with the current tops and bottoms",
                        "style_notes": "Additional style notes"
                    }}
                ],
                "recommendations": [
                    "recommendation1",
                    "recommendation2"
                ]
            }}""",
            agent=self.agent,
            expected_output="JSON formatted shoe suggestions with recommendations."
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[shoes_task],
            verbose=True
        )
        
        result = crew.kickoff()
        output = self._parse_result(result)
        output["shoes"] = [output["shoes"][0]]
        return output

    def _parse_result(self, result) -> Dict[str, Any]:
        """Helper method to parse the result from the LLM."""
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
            print(f"Error parsing suggestions: {str(e)}")
            print(f"Raw result: {result}")
            return {
                "error": "Failed to parse suggestions",
                "raw_result": str(result)
            }

    def generate_outfit(self, context: Dict[str, Any], available_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate outfit suggestions based on context and available items."""
        outfit_task = Task(
        description=f"""You must create an outfit that includes EXACTLY one top, one bottom, and one shoe. This is a strict requirement.
        If there are no bottoms (pants/shorts) in the available items, you MUST find one from the worn items.
        The outfit must be complete with all three components.
        IMPORTANT: You can ONLY use items that are listed in the Available Items below. Do not suggest items that are not in this list.
        Each item_id in your response MUST match exactly with an id from the Available Items list.

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
                        "item_id1",  # Must be a top from Available Items
                        "item_id2",  # Must be a bottom from Available Items
                        "item_id3"   # Must be a shoe from Available Items
                    ],
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
                            "item_id1",
                            "item_id2",
                            "item_id3"
                        ],
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
    def __init__(self, wardrobe_items: List[Dict[str, Any]]):
        self.weather_agent = WeatherAgent()
        self.wardrobe_agent = WardrobeAgent(wardrobe_items)
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
    
    def suggest_outfit(self, location: str = "Chicago, US", formality: str = "Casual", activity: str = "School", available_items=None) -> Dict[str, Any]:
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
        if available_items is not None:
            filtered_items = {"matching_items": available_items}
        else:
            filtered_items = self.wardrobe_agent.filter(context)
        
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
        
        return {
            'weather': weather_data,
            'available_items': filtered_items,
            'suggestions': outfit_suggestions,
            'calendar_info': calendar_info
        }

    def suggest_tops(self, location: str = "Chicago, US", formality: str = "Casual", activity: str = "School", current_bottoms: List[Dict[str, Any]] = None, current_shoes: List[Dict[str, Any]] = None, available_items: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate top suggestions based on weather, wardrobe, and context."""
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
        if available_items is not None:
            filtered_items = {"matching_items": available_items}
        else:
            filtered_items = self.wardrobe_agent.filter(context)
        
        # Generate top suggestions
        top_suggestions = self.outfit_generator.generate_tops(
            context,
            filtered_items['matching_items'],
            current_bottoms or [],
            current_shoes or []
        )
        
        return {
            'weather': weather_data,
            'available_items': filtered_items,
            'suggestions': top_suggestions,
            'calendar_info': calendar_info
        }

    def suggest_bottoms(self, location: str = "Chicago, US", formality: str = "Casual", activity: str = "School", current_tops: List[Dict[str, Any]] = None, current_shoes: List[Dict[str, Any]] = None, available_items: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate bottom suggestions based on weather, wardrobe, and context."""
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
        if available_items is not None:
            filtered_items = {"matching_items": available_items}
        else:
            filtered_items = self.wardrobe_agent.filter(context)
        
        # Generate bottom suggestions
        bottom_suggestions = self.outfit_generator.generate_bottoms(
            context,
            filtered_items['matching_items'],
            current_tops or [],
            current_shoes or []
        )
        
        return {
            'weather': weather_data,
            'available_items': filtered_items,
            'suggestions': bottom_suggestions,
            'calendar_info': calendar_info
        }

    def suggest_shoes(self, location: str = "Chicago, US", formality: str = "Casual", activity: str = "School", current_tops: List[Dict[str, Any]] = None, current_bottoms: List[Dict[str, Any]] = None, available_items: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate shoe suggestions based on weather, wardrobe, and context."""
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
        if available_items is not None:
            filtered_items = {"matching_items": available_items}
        else:
            filtered_items = self.wardrobe_agent.filter(context)
        
        # Generate shoe suggestions
        shoe_suggestions = self.outfit_generator.generate_shoes(
            context,
            filtered_items['matching_items'],
            current_tops or [],
            current_bottoms or []
        )
        
        return {
            'weather': weather_data,
            'available_items': filtered_items,
            'suggestions': shoe_suggestions,
            'calendar_info': calendar_info
        }