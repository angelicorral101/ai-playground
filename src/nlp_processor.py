import json
from datetime import datetime, timedelta
from dateutil import parser
from .config import Config
from .models import ProcessedCommand, CalendarEvent, CalendarAction, InputType
import openai  # Updated import for v0.28.1
from openai import OpenAI

class NLPProcessor:
    def __init__(self):
        self.base_system_prompt = """
You are a positive, helpful, friendly, and accommodating AI assistant that helps manage a family calendar. You understand natural language commands and convert them into structured calendar actions.

Your task is to:
1. Identify the intended action (create, update, delete, read, list)
2. Extract event details (title, date/time, location, attendees, description)
3. Handle multiple events in a single command when requested
4. Return a JSON response with the structured data

CRITICAL: Distinguish between CREATE and READ actions:
- CREATE: User wants to add/schedule a new event
- READ: User wants to see/view/check existing events

READ action keywords: what, show, list, check, see, tell me, what's, what is, schedule (when asking about existing schedule), events, appointments, meetings
CREATE action keywords: schedule, add, create, book, set up, arrange, plan (when creating new events)

IMPORTANT: If the user asks about a specific date (e.g., "on July 17th", "for tomorrow", "next Friday"), ALWAYS extract and return a start_time and end_time for that date in the event object, even if the user does not use explicit date range language. Do not rely only on the query field for date-based questions.

Common patterns:
- "Schedule a meeting" → CREATE action with single event
- "Create events tomorrow and Thursday" → CREATE action with multiple events
- "What's on my calendar on July 17th?" → READ action with event.start_time and event.end_time set to July 17th
- "Show me my schedule for the week" → READ action with query about week
- "What do I have planned tomorrow?" → READ action with event.start_time and event.end_time set to tomorrow
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

CREATE ACTIONS:
- "Create an event tomorrow and on Thursday that says Amelie's Tryouts at 3:45" → Creates 2 events: one for tomorrow at 3:45 PM and one for Thursday at 3:45 PM
- "Schedule meetings Monday and Wednesday at 2pm" → Creates 2 events: one for Monday at 2 PM and one for Wednesday at 2 PM
- "Add a dentist appointment next Friday at 2pm" → CREATE action with single event

READ ACTIONS:
- "What's on my calendar on July 17th?" → READ action with event.start_time and event.end_time set to July 17 (all-day)
- "What do I have scheduled on July 21st?" → READ action with event.start_time and event.end_time set to July 21 (all-day)
- "What is my schedule tomorrow?" → READ action with event.start_time and event.end_time set to tomorrow
- "Show me my events this week" → READ action with query: "this week"
- "What's on my schedule for the week?" → READ action with query: "week"
- "Tell me what I have planned for next week" → READ action with query: "next week"
- "What do I have on my calendar today?" → READ action with event.start_time and event.end_time set to today
- "Check my schedule for Friday" → READ action with event.start_time and event.end_time set to Friday
- "What meetings do I have this week?" → READ action with query: "meetings this week"
- "Show me my appointments for tomorrow" → READ action with event.start_time and event.end_time set to tomorrow
- "What's on my calendar this month?" → READ action with query: "this month"
- "List my events for next Monday" → READ action with event.start_time and event.end_time set to next Monday
"""

    def _get_system_prompt_with_current_date(self) -> str:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        current_weekday = datetime.now().strftime("%A")
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        def next_weekday(current_date, target_weekday):
            days_ahead = target_weekday - current_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return current_date + timedelta(days=days_ahead)
        next_monday = next_weekday(today, 0)
        next_tuesday = next_weekday(today, 1)
        next_wednesday = next_weekday(today, 2)
        next_thursday = next_weekday(today, 3)
        next_friday = next_weekday(today, 4)
        next_saturday = next_weekday(today, 5)
        next_sunday = next_weekday(today, 6)
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

For specific dates mentioned in queries (like "July 21st", "December 25th", etc.), parse them correctly and set the event start_time and end_time to cover the entire day (00:00:00 to 23:59:59) for that specific date.
"""
        return self.base_system_prompt + date_context

    def process_text(self, text: str, input_type: InputType) -> ProcessedCommand:
        try:
            print(f"🤖 Processing text: '{text}'")
            system_prompt = self._get_system_prompt_with_current_date()
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            
            # Log the request details
            print(f"📤 OpenAI Request:")
            print(f"   Model: gpt-3.5-turbo")
            print(f"   Temperature: 0.1")
            print(f"   Max tokens: 1000")
            print(f"   System prompt length: {len(system_prompt)} chars")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Process this command: {text}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Log response details
            print(f"📥 OpenAI Response Details:")
            # Usage and finish_reason may need to be accessed differently in v1.x
            # print(f"   Usage: {response.usage}")
            # print(f"   Finish reason: {response.choices[0].finish_reason}")
            
            content = response.choices[0].message.content
            if content:
                content = content.strip()
            else:
                content = ""
            print(f"📤 OpenAI Response Content: {content}")
            try:
                data = json.loads(content)
                print(f"✅ Parsed JSON: {json.dumps(data, indent=2)}")
                events_data = data.get('events', [])
                if not events_data and data.get('event'):
                    events_data = [data.get('event')]
                if not events_data:
                    return self._fallback_processing(text, input_type)
                for event in events_data:
                    if not event.get('calendar_id'):
                        event['calendar_id'] = 'family'
                event_data = events_data[0]
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
                result = ProcessedCommand(
                    action=CalendarAction(data.get('action', 'read')),
                    event=event,
                    query=data.get('query', ''),
                    confidence=data.get('confidence', 0.5),
                    raw_input=text,
                    input_type=input_type,
                    additional_events=events_data[1:] if len(events_data) > 1 else None
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
        text_lower = text.lower()
        now = datetime.now()
        default_end = now + timedelta(hours=1)
        read_keywords = ['what', 'show', 'list', 'check', 'see', 'tell me', "what's", 'what is', 'events', 'appointments', 'meetings', 'schedule']
        create_keywords = ['schedule', 'add', 'create', 'book', 'set up', 'arrange', 'plan']
        relative_queries = [
            'this week', 'the week', 'week', 'current week', 'next week', 'last week', 'previous week',
            'today', 'tomorrow', 'this month', 'current month', 'next month', 'last month', 'previous month'
        ]
        if any(word in text_lower for word in read_keywords):
            if any(rel in text_lower for rel in relative_queries):
                # For relative queries, do not set event, only query
                return ProcessedCommand(
                    action=CalendarAction.READ,
                    event=None,
                    query=text,
                    confidence=0.3,
                    raw_input=text,
                    input_type=input_type
                )
            else:
                # For non-relative queries, set a default event
                return ProcessedCommand(
                    action=CalendarAction.READ,
                    event=CalendarEvent(summary='', description='', start_time=now, end_time=default_end, location='', attendees=[], reminders=None, calendar_id='family'),
                    query=text,
                    confidence=0.3,
                    raw_input=text,
                    input_type=input_type
                )
        elif any(word in text_lower for word in create_keywords):
            return ProcessedCommand(
                action=CalendarAction.CREATE,
                event=CalendarEvent(summary=text, description='', start_time=now, end_time=default_end, location='', attendees=[], reminders=None, calendar_id='family'),
                query='',
                confidence=0.3,
                raw_input=text,
                input_type=input_type
            )
        else:
            return ProcessedCommand(
                action=CalendarAction.READ,
                event=CalendarEvent(summary='', description='', start_time=now, end_time=default_end, location='', attendees=[], reminders=None, calendar_id='family'),
                query=text,
                confidence=0.1,
                raw_input=text,
                input_type=input_type
            ) 