import openai
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dateutil import parser
from .config import Config
from .models import ProcessedCommand, CalendarEvent, CalendarAction, InputType

class NLPProcessor:
    def __init__(self):
        # Remove the deprecated openai.api_key assignment
        self.base_system_prompt = """
You are an AI assistant that helps manage a family calendar. You understand natural language commands and convert them into structured calendar actions.

Your task is to:
1. Identify the intended action (create, update, delete, read, list)
2. Extract event details (title, date/time, location, attendees, description)
3. Handle multiple events in a single command when requested
4. Return a JSON response with the structured data

IMPORTANT: If the user asks about a specific date (e.g., "on July 17th", "for tomorrow", "next Friday"), ALWAYS extract and return a start_time and end_time for that date in the event object, even if the user does not use explicit date range language. Do not rely only on the query field for date-based questions.

Common patterns:
- "Schedule a meeting" → CREATE action with single event
- "Create events tomorrow and Thursday" → CREATE action with multiple events
- "What's on my calendar on July 17th?" → READ action with event.start_time and event.end_time set to July 17th
- "Delete the meeting" → DELETE action
- "Update the appointment" → UPDATE action

For multiple events, if the user mentions multiple dates/times for the same event, create separate events for each date.

Return a JSON object with this structure:
{
    "action": "create|read|update|delete|list",
    "events": [
        {
            "summary": "Event title",
            "description": "Event description",
            "start_time": "YYYY-MM-DDTHH:MM:SS",
            "end_time": "YYYY-MM-DDTHH:MM:SS",
            "location": "Event location",
            "attendees": ["email1@example.com", "email2@example.com"],
            "calendar_id": "calendar_id_or_name",
            "reminders": [
                {"method": "popup", "minutes": 60},
                {"method": "email", "minutes": 1440}
            ]
        }
    ],
    "query": "search query for read/list actions",
    "confidence": 0.95
}

For calendar selection, extract calendar information from phrases like:
- "on my Shared Family calendar" → calendar_id: "shared_family"
- "on my work calendar" → calendar_id: "work"
- "on the family calendar" → calendar_id: "family"
- "put it on [calendar name]" → calendar_id: "[calendar_name]"

For reminders/notifications, extract timing from phrases like:
- "alert 1 hour before" → reminders: [{"method": "popup", "minutes": 60}]
- "notify 30 minutes before" → reminders: [{"method": "popup", "minutes": 30}]
- "remind me 2 hours before" → reminders: [{"method": "popup", "minutes": 120}]
- "email reminder 1 day before" → reminders: [{"method": "email", "minutes": 1440}]
- "alert 15 minutes before and 1 hour before" → reminders: [{"method": "popup", "minutes": 15}, {"method": "popup", "minutes": 60}]

EXAMPLES:
- "Create an event tomorrow and on Thursday that says Amelie's Tryouts at 3.45" → Creates 2 events: one for tomorrow at 3:45 PM and one for Thursday at 3:45 PM
- "Schedule meetings Monday and Wednesday at 2pm" → Creates 2 events: one for Monday at 2 PM and one for Wednesday at 2 PM
- "What's on my calendar on July 17th?" → Returns a READ action with event.start_time and event.end_time set to July 17th (all-day)
"""

    def _get_system_prompt_with_current_date(self) -> str:
        """Get the system prompt with current date injected"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        current_weekday = datetime.now().strftime("%A")
        
        # Calculate specific dates for weekdays
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        # Calculate next occurrences of each weekday
        def next_weekday(current_date, target_weekday):
            days_ahead = target_weekday - current_date.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return current_date + timedelta(days=days_ahead)
        
        next_monday = next_weekday(today, 0)  # Monday = 0
        next_tuesday = next_weekday(today, 1)  # Tuesday = 1
        next_wednesday = next_weekday(today, 2)  # Wednesday = 2
        next_thursday = next_weekday(today, 3)  # Thursday = 3
        next_friday = next_weekday(today, 4)  # Friday = 4
        next_saturday = next_weekday(today, 5)  # Saturday = 5
        next_sunday = next_weekday(today, 6)  # Sunday = 6
        
        date_context = f"""
CURRENT DATE AND TIME: {current_date} at {current_time} ({current_weekday})

When resolving relative dates, use this as the reference point:
- "today" = {current_date}
- "tomorrow" = {tomorrow.strftime('%Y-%m-%d')}
- "yesterday" = {yesterday.strftime('%Y-%m-%d')}
- "next week" = {(today + timedelta(days=7)).strftime('%Y-%m-%d')}

For weekday references, use these EXACT dates:
- "Monday" = {next_monday.strftime('%Y-%m-%d')}
- "Tuesday" = {next_tuesday.strftime('%Y-%m-%d')}
- "Wednesday" = {next_wednesday.strftime('%Y-%m-%d')}
- "Thursday" = {next_thursday.strftime('%Y-%m-%d')}
- "Friday" = {next_friday.strftime('%Y-%m-%d')}
- "Saturday" = {next_saturday.strftime('%Y-%m-%d')}
- "Sunday" = {next_sunday.strftime('%Y-%m-%d')}

IMPORTANT: Use the EXACT dates listed above. Do not calculate them yourself.
Always use the current date ({current_date}) as the reference for relative date calculations.
"""
        
        return self.base_system_prompt + date_context

    def process_text(self, text: str, input_type: InputType) -> ProcessedCommand:
        """Process natural language text and extract calendar command"""
        try:
            print(f"🤖 Processing text: '{text}'")
            
            # Get system prompt with current date
            system_prompt = self._get_system_prompt_with_current_date()
            
            openai.api_key = Config.OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Process this command: {text}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            if content:
                content = content.strip()
            else:
                content = ""
            print(f"📤 OpenAI Response: {content}")
            
            # Try to parse JSON response
            try:
                data = json.loads(content)
                print(f"✅ Parsed JSON: {json.dumps(data, indent=2)}")
                
                # Handle both single event (backward compatibility) and multiple events
                events_data = data.get('events', [])
                if not events_data and data.get('event'):
                    # Backward compatibility: convert single event to array
                    events_data = [data.get('event')]
                
                if not events_data:
                    return self._fallback_processing(text, input_type)
                
                # Default calendar_id to 'family' if not specified
                for event in events_data:
                    if not event.get('calendar_id'):
                        event['calendar_id'] = 'family'
                
                # Process the first event (for now, we'll handle multiple events in the calendar agent)
                event_data = events_data[0]
                
                # Parse start and end times with fallback to current time
                start_time = datetime.now()
                end_time = datetime.now() + timedelta(hours=1)
                
                if event_data.get('start_time'):
                    try:
                        start_time = parser.parse(event_data.get('start_time'))
                    except:
                        start_time = datetime.now()
                
                if event_data.get('end_time'):
                    try:
                        end_time = parser.parse(event_data.get('end_time'))
                    except:
                        end_time = start_time + timedelta(hours=1)
                
                # Parse reminders if provided
                reminders = None
                if event_data.get('reminders'):
                    reminders = {
                        'useDefault': False,
                        'overrides': event_data.get('reminders', [])
                    }
                
                event = CalendarEvent(
                    summary=event_data.get('summary', ''),
                    description=event_data.get('description', ''),
                    start_time=start_time,
                    end_time=end_time,
                    location=event_data.get('location', ''),
                    attendees=event_data.get('attendees', []),
                    reminders=reminders,
                    calendar_id=event_data.get('calendar_id')
                )
                
                # Store all events data for multiple event processing
                result = ProcessedCommand(
                    action=CalendarAction(data.get('action', 'read')),
                    event=event,
                    query=data.get('query', ''),
                    confidence=data.get('confidence', 0.5),
                    raw_input=text,
                    input_type=input_type,
                    additional_events=events_data[1:] if len(events_data) > 1 else []  # Store additional events
                )
                
                print(f"🎯 Final Result: {result}")
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                return self._fallback_processing(text, input_type)
                
        except Exception as e:
            print(f"❌ Error processing text: {e}")
            return self._fallback_processing(text, input_type)

    def _fallback_processing(self, text: str, input_type: InputType) -> ProcessedCommand:
        """Fallback processing when OpenAI fails"""
        text_lower = text.lower()
        
        # Simple keyword-based processing
        now = datetime.now()
        default_end = now + timedelta(hours=1)
        
        if any(word in text_lower for word in ['schedule', 'add', 'create', 'book']):
            return ProcessedCommand(
                action=CalendarAction.CREATE,
                event=CalendarEvent(summary=text, description='', start_time=now, end_time=default_end, location='', attendees=[], reminders=None),
                query='',
                confidence=0.3,
                raw_input=text,
                input_type=input_type
            )
        elif any(word in text_lower for word in ['what', 'show', 'list', 'read']):
            return ProcessedCommand(
                action=CalendarAction.READ,
                event=CalendarEvent(summary='', description='', start_time=now, end_time=default_end, location='', attendees=[], reminders=None),
                query=text,
                confidence=0.3,
                raw_input=text,
                input_type=input_type
            )
        else:
            return ProcessedCommand(
                action=CalendarAction.READ,
                event=CalendarEvent(summary='', description='', start_time=now, end_time=default_end, location='', attendees=[], reminders=None),
                query=text,
                confidence=0.1,
                raw_input=text,
                input_type=input_type
            ) 