import json
from datetime import datetime, timedelta
from dateutil import parser
from .config import Config
from .models import ProcessedCommand, CalendarEvent, CalendarAction, InputType, ChoresCommand, ChoresAction
import openai  # Updated import for v0.28.1
from openai import OpenAI

class NLPProcessor:
    def __init__(self):
        self.base_system_prompt = """
You are a positive, helpful, friendly, and accommodating AI assistant that helps manage a family calendar and chores through natural language commands. You understand natural language commands and convert them into structured actions.

Your task is to:
1. Identify the intended action (create, update, delete, read, list) for calendar OR (add, assign, complete, update, remove, query) for chores
2. Extract event details (title, date/time, location, attendees, description) for calendar events
3. Extract chore details (description, assignee) for chores
4. Handle multiple events in a single command when requested
5. Return a JSON response with the structured data

CRITICAL: Distinguish between CALENDAR and CHORES commands:
- CALENDAR keywords: calendar, schedule, appointment, meeting, event, appointment
- CHORES keywords: chore, chores, housework, task, tasks, cleaning, cooking, laundry, dishes, vacuum, trash

CALENDAR ACTIONS:
- CREATE: User wants to add/schedule a new calendar event
- READ: User wants to see/view/check existing calendar events

CHORES ACTIONS:
- ADD: User wants to create a new chore (e.g., "add dinner to my chores")
- ASSIGN: User wants to assign an existing chore to themselves or someone else
- COMPLETE: User wants to mark a chore as done
- UPDATE: User wants to modify an existing chore
- REMOVE: User wants to delete a chore
- QUERY: User wants to see what chores exist

IMPORTANT FOR CHORES: When extracting chore descriptions, only include the core task name, not time/date words:
- "Add dinner to my chores for today" → chore description: "dinner" (not "dinner today")
- "Add vacuum the living room to my chores" → chore description: "vacuum the living room"
- "Add wash dishes for tomorrow" → chore description: "wash dishes" (not "wash dishes for tomorrow")
- "Add take out trash today" → chore description: "take out trash" (not "take out trash today")

Time and date information should be ignored when extracting chore descriptions.

CHORES DESCRIPTION EXTRACTION RULES:
1. Extract ONLY the core task/activity name
2. Remove all time-related words: today, tomorrow, yesterday, tonight, this week, next week, this month, next month
3. Remove all date-related words: Monday, Tuesday, etc.
4. Remove all prepositional phrases about time: "for today", "for tomorrow", "this afternoon", etc.
5. Keep the essential task description: "dinner", "wash dishes", "vacuum living room", "take out trash"

EXAMPLES OF CORRECT EXTRACTION:
- Input: "Add dinner to my chores for today" → Output: "dinner"
- Input: "Add wash dishes for tomorrow" → Output: "wash dishes" 
- Input: "Add vacuum the living room today" → Output: "vacuum the living room"
- Input: "Add take out trash this afternoon" → Output: "take out trash"
- Input: "Add make breakfast for tomorrow morning" → Output: "make breakfast"

READ action keywords: what, show, list, check, see, tell me, what's, what is, schedule (when asking about existing schedule), events, appointments, meetings
CREATE action keywords: schedule, add, create, book, set up, arrange, plan (when creating new calendar events)

CHORES action keywords:
- ADD: add, create, new, make, put, schedule (when followed by "chores")
- ASSIGN: assign, pick up, take, do, claim
- COMPLETE: complete, done, finish, mark as done, mark complete
- UPDATE: update, edit, change, modify, rename
- REMOVE: remove, delete, cancel, clear
- QUERY: what chores, show chores, list chores, check chores

IMPORTANT: If the user asks about a specific date (e.g., "on July 17th", "for tomorrow", "next Friday"), ALWAYS extract and return a start_time and end_time for that date in the event object, even if the user does not use explicit date range language. Do not rely only on the query field for date-based questions.

Return a JSON object with this structure:
{
    "action": "create|read|update|delete|list|add|assign|complete|update|remove|query",
    "type": "calendar|chores",
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
    "chores": [
        {
            "description": "Chore description",
            "assignee": "user_email_or_name",
            "action": "add|assign|complete|update|remove"
        }
    ],
    "query": "search query for read/list actions",
    "confidence": 0.95
}

EXAMPLES:

CALENDAR ACTIONS:
- "Schedule a meeting tomorrow at 2pm" → CREATE action with single event
- "What's on my calendar today?" → READ action with event.start_time and event.end_time set to today

CHORES ACTIONS:
- "Add dinner to my chores for today" → ADD action with chore description "dinner"
- "Assign vacuuming to me" → ASSIGN action with chore description "vacuuming"
- "Mark dishes as complete" → COMPLETE action with chore description "dishes"
- "What chores do I have today?" → QUERY action for chores
- "Remove making dinner from my chores" → REMOVE action with chore description "making dinner"
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
                
                # Check if this is a chores command
                if data.get('type') == 'chores':
                    chores_data = data.get('chores', [])
                    if chores_data:
                        chore_data = chores_data[0]
                        # Clean up chore description by removing time/date words
                        description = chore_data.get('description', '')
                        time_words = ['today', 'tomorrow', 'yesterday', 'tonight', 'this week', 'next week', 'this month', 'next month']
                        for time_word in time_words:
                            description = description.replace(time_word, '').strip()
                        # Clean up extra spaces
                        description = ' '.join(description.split())
                        
                        return ChoresCommand(
                            action=ChoresAction(chore_data.get('action', 'query')),
                            chore_description=description,
                            assignee=chore_data.get('assignee', ''),
                            raw_input=text
                        )
                    else:
                        return ChoresCommand(
                            action=ChoresAction.QUERY,
                            raw_input=text
                        )
                
                # Handle calendar events (existing logic)
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

    def _fallback_processing(self, text: str, input_type: InputType):
        text_lower = text.lower()
        now = datetime.now()
        default_end = now + timedelta(hours=1)
        # Chores intent detection
        chores_keywords = ['chore', 'chores', 'housework', 'task', 'tasks']
        assign_keywords = ['assign', 'pick up', 'take', 'do', 'claim']
        complete_keywords = ['complete', 'done', 'finish', 'mark as done', 'mark complete']
        add_keywords = ['add', 'create', 'new', 'make', 'put', 'schedule']
        update_keywords = ['update', 'edit', 'change', 'modify', 'rename']
        remove_keywords = ['remove', 'delete', 'cancel', 'clear']
        if any(word in text_lower for word in chores_keywords):
            if any(word in text_lower for word in add_keywords):
                # Extract description using word-based filtering
                words = text.split()
                filtered_words = []
                skip_words = set(chores_keywords + add_keywords + ['to', 'for', 'my', 'the', 'a', 'an'])
                for word in words:
                    if word.lower() not in skip_words:
                        filtered_words.append(word)
                desc = ' '.join(filtered_words).strip(' .:,')
                return ChoresCommand(
                    action=ChoresAction.ADD,
                    chore_description=desc,
                    raw_input=text
                )
            elif any(word in text_lower for word in assign_keywords):
                words = text.split()
                filtered_words = []
                skip_words = set(chores_keywords + assign_keywords + ['to', 'for', 'my', 'the', 'a', 'an'])
                for word in words:
                    if word.lower() not in skip_words:
                        filtered_words.append(word)
                desc = ' '.join(filtered_words).strip(' .:,')
                return ChoresCommand(
                    action=ChoresAction.ASSIGN,
                    chore_description=desc,
                    raw_input=text
                )
            elif any(word in text_lower for word in complete_keywords):
                words = text.split()
                filtered_words = []
                skip_words = set(chores_keywords + complete_keywords + ['to', 'for', 'my', 'the', 'a', 'an'])
                for word in words:
                    if word.lower() not in skip_words:
                        filtered_words.append(word)
                desc = ' '.join(filtered_words).strip(' .:,')
                return ChoresCommand(
                    action=ChoresAction.COMPLETE,
                    chore_description=desc,
                    raw_input=text
                )
            elif any(word in text_lower for word in update_keywords):
                words = text.split()
                filtered_words = []
                skip_words = set(chores_keywords + update_keywords + ['to', 'for', 'my', 'the', 'a', 'an'])
                for word in words:
                    if word.lower() not in skip_words:
                        filtered_words.append(word)
                desc = ' '.join(filtered_words).strip(' .:,')
                return ChoresCommand(
                    action=ChoresAction.UPDATE,
                    chore_description=desc,
                    raw_input=text
                )
            elif any(word in text_lower for word in remove_keywords):
                words = text.split()
                filtered_words = []
                skip_words = set(chores_keywords + remove_keywords + ['to', 'for', 'my', 'the', 'a', 'an'])
                for word in words:
                    if word.lower() not in skip_words:
                        filtered_words.append(word)
                desc = ' '.join(filtered_words).strip(' .:,')
                return ChoresCommand(
                    action=ChoresAction.REMOVE,
                    chore_description=desc,
                    raw_input=text
                )
            else:
                return ChoresCommand(
                    action=ChoresAction.QUERY,
                    raw_input=text
                )
        # Calendar fallback logic
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