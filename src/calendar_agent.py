from typing import Optional, Tuple, Union
from datetime import datetime
from .voice_processor import VoiceProcessor
from .nlp_processor import NLPProcessor
from .google_calendar import GoogleCalendarManager
from .conversation_manager import ConversationManager
from .tts_processor import TTSProcessor
from .models import (
    VoiceInput, TextInput, SMSInput, ProcessedCommand, 
    AgentResponse, CalendarResponse, InputType, CalendarEvent
)

class CalendarAgent:
    def __init__(self):
        self.voice_processor = VoiceProcessor()
        self.nlp_processor = NLPProcessor()
        self.calendar_manager = GoogleCalendarManager()
        self.conversation_manager = ConversationManager()
        self.tts_processor = TTSProcessor()
    
    def process_voice_command(self, voice_input: VoiceInput) -> AgentResponse:
        """Process voice command and execute calendar action"""
        try:
            print(f"🎤 Processing voice command: {len(voice_input.audio_data)} bytes, format: {voice_input.format}")
            
            # Convert voice to text
            text = self.voice_processor.process_voice_input(voice_input)
            if not text:
                return AgentResponse(
                    success=False,
                    message="Could not transcribe audio. Please check your recording and try again.",
                    confidence=0.0
                )
            
            print(f"📝 Transcribed text: '{text}'")
            
            # Process the text command
            return self._process_text_command(text, InputType.VOICE)
            
        except Exception as e:
            print(f"❌ Voice command error: {e}")
            return AgentResponse(
                success=False,
                message=f"Error processing voice command: {str(e)}",
                confidence=0.0
            )
    
    def process_text_command(self, text_input: TextInput) -> AgentResponse:
        """Process text command and execute calendar action"""
        return self._process_text_command(text_input.message, InputType.TEXT)
    
    def process_sms_command(self, sms_input: SMSInput) -> AgentResponse:
        """Process SMS command and execute calendar action"""
        return self._process_text_command(sms_input.message, InputType.SMS)
    
    def _process_text_command(self, text: str, input_type: InputType) -> AgentResponse:
        """Internal method to process text commands"""
        try:
            # Use NLP to understand the command
            command = self.nlp_processor.process_text(text, input_type)
            
            # Execute the calendar action
            calendar_response = self._execute_calendar_action(command)
            
            # Generate response message
            response_message = self._generate_response_message(command, calendar_response)
            
            return AgentResponse(
                success=calendar_response.success,
                message=response_message,
                calendar_response=calendar_response,
                confidence=command.confidence,
                suggestions=self._generate_suggestions(command)
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Error processing command: {str(e)}",
                confidence=0.0
            )
    
    def _execute_calendar_action(self, command: ProcessedCommand) -> CalendarResponse:
        """Execute the appropriate calendar action based on the command"""
        try:
            if command.action.value == "create":
                if command.event:
                    # Create the primary event
                    primary_response = self.calendar_manager.create_event(command.event)
                    
                    # If there are additional events, create them too
                    if command.additional_events and primary_response.success:
                        additional_responses = []
                        for event_data in command.additional_events:
                            try:
                                # Parse the additional event data
                                from datetime import datetime, timedelta
                                from dateutil import parser
                                
                                start_time = datetime.now()
                                end_time = datetime.now() + timedelta(hours=1)
                                
                                if event_data.get('start_time'):
                                    try:
                                        start_time = parser.parse(str(event_data.get('start_time')))
                                    except:
                                        start_time = datetime.now()
                                
                                if event_data.get('end_time'):
                                    try:
                                        end_time = parser.parse(str(event_data.get('end_time')))
                                    except:
                                        end_time = start_time + timedelta(hours=1)
                                
                                # Parse reminders if provided
                                reminders = None
                                if event_data.get('reminders'):
                                    reminders = {
                                        'useDefault': False,
                                        'overrides': event_data.get('reminders', [])
                                    }
                                
                                additional_event = CalendarEvent(
                                    summary=event_data.get('summary', command.event.summary),
                                    description=event_data.get('description', command.event.description),
                                    start_time=start_time,
                                    end_time=end_time,
                                    location=event_data.get('location', command.event.location),
                                    attendees=event_data.get('attendees', command.event.attendees or []),
                                    reminders=reminders,
                                    calendar_id=event_data.get('calendar_id', command.event.calendar_id)
                                )
                                
                                additional_response = self.calendar_manager.create_event(additional_event)
                                additional_responses.append(additional_response)
                                
                            except Exception as e:
                                print(f"Error creating additional event: {e}")
                                additional_responses.append(CalendarResponse(
                                    success=False,
                                    message=f"Failed to create additional event: {str(e)}",
                                    error=str(e)
                                ))
                        
                        # Return combined response
                        total_events = 1 + len(command.additional_events)
                        successful_events = 1 + sum(1 for r in additional_responses if r.success)
                        
                        if successful_events == total_events:
                            return CalendarResponse(
                                success=True,
                                message=f"Successfully created {total_events} events",
                                event_id=primary_response.event_id
                            )
                        else:
                            return CalendarResponse(
                                success=False,
                                message=f"Created {successful_events} out of {total_events} events. Some events failed to create.",
                                event_id=primary_response.event_id if primary_response.success else None
                            )
                    
                    return primary_response
                else:
                    return CalendarResponse(
                        success=False,
                        message="No event details provided for creation",
                        error="Missing event information"
                    )
            
            elif command.action.value == "update":
                # For update, we'd need an event ID - this is simplified
                if command.event:
                    # In a real implementation, you'd need to find the event first
                    return CalendarResponse(
                        success=False,
                        message="Update requires event ID. Please specify which event to update.",
                        error="Missing event ID"
                    )
                else:
                    return CalendarResponse(
                        success=False,
                        message="No event details provided for update",
                        error="Missing event information"
                    )
            
            elif command.action.value == "delete":
                # For delete, we'd need an event ID - this is simplified
                return CalendarResponse(
                    success=False,
                    message="Delete requires event ID. Please specify which event to delete.",
                    error="Missing event ID"
                )
            
            elif command.action.value == "read":
                # For read actions, prioritize date-based queries over text searches
                # If we have specific dates in the event, use those
                if command.event and command.event.start_time and command.event.end_time:
                    start_date = command.event.start_time
                    end_date = command.event.end_time
                    print(f"[DEBUG] Using event start_date: {start_date} end_date: {end_date}")
                    return self.calendar_manager.get_events_all_calendars(start_date=start_date, end_date=end_date)
                elif command.query:
                    # Try to parse date queries like "this week", "next week", etc.
                    date_range = self._parse_date_query(command.query)
                    if date_range:
                        start_date, end_date = date_range
                        print(f"[DEBUG] Using parsed query start_date: {start_date} end_date: {end_date}")
                        return self.calendar_manager.get_events_all_calendars(start_date=start_date, end_date=end_date)
                    else:
                        # Fall back to text search if no date range found
                        print(f"[DEBUG] Using text search for query: {command.query}")
                        return self.calendar_manager.search_events(command.query)
                else:
                    print("[DEBUG] Using default get_events_all_calendars()")
                    return self.calendar_manager.get_events_all_calendars()
            
            elif command.action.value == "list":
                # Use the date range from the command if available
                start_date = command.event.start_time if command.event else None
                end_date = command.event.end_time if command.event else None
                return self.calendar_manager.get_events(start_date=start_date, end_date=end_date)
            
            else:
                return CalendarResponse(
                    success=False,
                    message="Unknown action",
                    error="Invalid action type"
                )
                
        except Exception as e:
            return CalendarResponse(
                success=False,
                message="Error executing calendar action",
                error=str(e)
            )
    
    def _generate_response_message(self, command: ProcessedCommand, 
                                 calendar_response: CalendarResponse) -> str:
        """Generate a user-friendly response message"""
        if not calendar_response.success:
            return calendar_response.message
        
        if command.action.value == "create":
            return f"✅ {calendar_response.message}"
        
        elif command.action.value in ["read", "list"]:
            if calendar_response.events:
                event_count = len(calendar_response.events)
                if event_count == 0:
                    return "📅 No events found for the specified time period."
                elif event_count == 1:
                    event = calendar_response.events[0]
                    return f"📅 Found 1 event: {event.summary} on {event.start_time.strftime('%B %d at %I:%M %p')}"
                else:
                    event_list = "\n".join([
                        f"• {event.summary} - {event.start_time.strftime('%B %d at %I:%M %p')}"
                        for event in calendar_response.events[:5]  # Show first 5
                    ])
                    return f"📅 Found {event_count} events:\n{event_list}"
            else:
                return calendar_response.message
        
        else:
            return calendar_response.message
    
    def _generate_suggestions(self, command: ProcessedCommand) -> list:
        """Generate helpful suggestions based on the command"""
        suggestions = []
        
        if command.confidence < 0.7:
            suggestions.append("Try being more specific about the event details")
            suggestions.append("Include date and time information")
        
        if command.action.value == "create" and not command.event:
            suggestions.append("Try: 'Schedule a meeting tomorrow at 2pm'")
            suggestions.append("Try: 'Add dentist appointment on Friday at 3pm'")
        
        if command.action.value in ["read", "list"]:
            suggestions.append("Try: 'What's on my calendar tomorrow?'")
            suggestions.append("Try: 'Show my events this week'")
        
        return suggestions
    
    def _parse_date_query(self, query: str) -> Union[Tuple[datetime, datetime], None]:
        """Parse date queries like 'this week', 'next week', 'today', etc., and weekday names like 'Wednesday'."""
        from datetime import datetime, timedelta
        from dateutil import tz
        import re
        
        query_lower = query.lower().strip()
        now = datetime.now()
        
        # Get Chicago timezone
        chicago_tz = tz.gettz('America/Chicago')
        
        # Calculate current week boundaries (Monday to Sunday)
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        
        # Set time to start/end of day with timezone
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=chicago_tz)
        sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=chicago_tz)
        
        # Use substring matching to detect relative date phrases anywhere in the query
        if any(phrase in query_lower for phrase in ["this week", "the week", "week", "current week"]):
            return (monday, sunday)
        elif any(phrase in query_lower for phrase in ["next week"]):
            next_monday = monday + timedelta(days=7)
            next_sunday = sunday + timedelta(days=7)
            return (next_monday, next_sunday)
        elif any(phrase in query_lower for phrase in ["last week", "previous week"]):
            last_monday = monday - timedelta(days=7)
            last_sunday = sunday - timedelta(days=7)
            return (last_monday, last_sunday)
        elif any(phrase in query_lower for phrase in ["today"]):
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=chicago_tz)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=chicago_tz)
            return (today_start, today_end)
        elif any(phrase in query_lower for phrase in ["tomorrow"]):
            tomorrow = now + timedelta(days=1)
            tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=chicago_tz)
            tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=chicago_tz)
            return (tomorrow_start, tomorrow_end)
        elif any(phrase in query_lower for phrase in ["this month", "current month"]):
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=chicago_tz)
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            month_end = next_month - timedelta(days=1)
            month_end = month_end.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=chicago_tz)
            return (month_start, month_end)
        
        # Handle weekday queries (e.g., 'on Wednesday', 'next Wednesday')
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, weekday in enumerate(weekdays):
            # Regex to match 'on wednesday', 'next wednesday', or just 'wednesday'
            if re.search(rf"(on |next )?{weekday}", query_lower):
                # Calculate days until the next occurrence of the weekday
                days_ahead = (i - now.weekday() + 7) % 7
                if days_ahead == 0 and "next" in query_lower:
                    days_ahead = 7  # If today is the day and 'next' is specified, go to next week
                elif days_ahead == 0:
                    # If today is the day and 'next' is not specified, use today
                    pass
                target_date = now + timedelta(days=days_ahead)
                target_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=chicago_tz)
                target_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=chicago_tz)
                return (target_start, target_end)
        
        return None

    def record_and_process(self, duration: int = 5) -> AgentResponse:
        """Record voice from microphone and process the command"""
        try:
            text = self.voice_processor.record_from_microphone(duration)
            if not text:
                return AgentResponse(
                    success=False,
                    message="No speech detected. Please try again.",
                    confidence=0.0
                )
            
            return self._process_text_command(text, InputType.VOICE)
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Error recording voice: {str(e)}",
                confidence=0.0
            )
    
    def start_conversation(self, user_id: Optional[str] = None) -> str:
        """Start a new conversation and return conversation ID"""
        conversation_id = self.conversation_manager.create_conversation(user_id)
        print(f"💬 Started new conversation: {conversation_id}")
        return conversation_id
    
    def process_conversational_voice(self, voice_input: VoiceInput, conversation_id: str, 
                                   voice: str = None, model: str = None) -> AgentResponse:
        """Process voice input in a conversational context and return voice response"""
        try:
            print(f"💬 Processing conversational voice for conversation: {conversation_id}")
            
            # Convert voice to text
            text = self.voice_processor.process_voice_input(voice_input)
            if not text:
                return AgentResponse(
                    success=False,
                    message="Could not transcribe audio. Please try again.",
                    confidence=0.0
                )
            
            print(f"📝 Transcribed text: '{text}'")
            
            # Add user message to conversation
            self.conversation_manager.add_message(conversation_id, 'user', text, 'voice')
            
            # Get calendar context if the message mentions calendar or time-related words
            calendar_context = None
            calendar_keywords = ['calendar', 'event', 'schedule', 'appointment', 'meeting', 'date', 'when', 'what', 'have', 'got', 'doing']
            detected_keywords = [word for word in calendar_keywords if word in text.lower()]
            if detected_keywords:
                print(f"📅 Message mentions calendar/time keywords: {detected_keywords}")
                # Parse date queries like "tomorrow", "today", etc.
                date_range = self._parse_date_query(text)
                print(f"📅 Parsed date range: {date_range}")
                
                if date_range:
                    # Query for specific date range
                    start_date, end_date = date_range
                    calendar_response = self.calendar_manager.get_events_all_calendars(
                        start_date=start_date,
                        end_date=end_date,
                        max_results=10
                    )
                    print(f"📅 Querying calendar for date range: {start_date} to {end_date}")
                else:
                    # Get recent calendar events
                    calendar_response = self.calendar_manager.get_events_all_calendars(
                        max_results=5
                    )
                
                if calendar_response.success and calendar_response.events:
                    calendar_context = {
                        'query_date_range': date_range,
                        'events': [
                            {
                                'summary': event.summary,
                                'start_time': event.start_time.isoformat() if event.start_time else None,
                                'end_time': event.end_time.isoformat() if event.end_time else None
                            }
                            for event in calendar_response.events
                        ]
                    }
            
            # Generate conversational response
            response_text = self.conversation_manager.generate_response(
                conversation_id, text, calendar_context
            )
            
            print(f"🤖 AI Response: '{response_text}'")
            
            # Convert response to speech
            audio_data = self.tts_processor.text_to_speech(response_text, voice, model)

            # Prepare queried_date and queried_view for UI
            queried_date = None
            queried_view = None
            is_month_query = False
            if detected_keywords:
                if 'date_range' in locals() and date_range:
                    # If it's a range, return both as ISO
                    queried_date = [start_date.isoformat(), end_date.isoformat()]
                    # Determine if it's a week or month view
                    if (end_date - start_date).days >= 27:
                        queried_view = 'month'
                        is_month_query = True
                    elif (end_date - start_date).days >= 6:
                        queried_view = 'week'
                    else:
                        queried_view = 'day'
                elif 'date_range' in locals() and date_range is not None:
                    queried_date = date_range.isoformat() if hasattr(date_range, 'isoformat') else str(date_range)
                    queried_view = 'day'

            # If it's a month query, override the response text and ensure all month events are included
            if is_month_query:
                response_text = "Here’s your calendar for this month. Is there a specific week or day you’d like to review?"
                # Query all events for the month if not already done
                if not (calendar_response and calendar_response.success and calendar_response.events):
                    # Use the parsed month range
                    calendar_response = self.calendar_manager.get_events_all_calendars(
                        start_date=start_date,
                        end_date=end_date,
                        max_results=100
                    )

            if audio_data:
                print(f"🎤 Generated speech: {len(audio_data)} bytes")
                return AgentResponse(
                    success=True,
                    message=response_text,
                    confidence=0.9,
                    audio_response=audio_data,
                    queried_date=queried_date,
                    queried_view=queried_view,
                    calendar_response=calendar_response
                )
            else:
                print("⚠️  TTS failed, returning text only")
                return AgentResponse(
                    success=True,
                    message=response_text,
                    confidence=0.9,
                    queried_date=queried_date,
                    queried_view=queried_view,
                    calendar_response=calendar_response
                )
            
        except Exception as e:
            print(f"❌ Conversational voice error: {e}")
            return AgentResponse(
                success=False,
                message=f"Error processing conversational voice: {str(e)}",
                confidence=0.0
            )
    
    def process_conversational_text(self, text: str, conversation_id: str,
                                  voice: str = None, model: str = None) -> AgentResponse:
        """Process text input in a conversational context and return voice response"""
        try:
            print(f"💬 Processing conversational text for conversation: {conversation_id}")
            print(f"📝 Text: '{text}'")
            
            # Add user message to conversation
            self.conversation_manager.add_message(conversation_id, 'user', text, 'text')
            print(f"✅ Added user message to conversation")
            
            # Get calendar context if the message mentions calendar or time-related words
            calendar_context = None
            calendar_keywords = ['calendar', 'event', 'schedule', 'appointment', 'meeting', 'date', 'when', 'what', 'have', 'got', 'doing']
            detected_keywords = [word for word in calendar_keywords if word in text.lower()]
            if detected_keywords:
                print(f"📅 Message mentions calendar/time keywords: {detected_keywords}")
                # Parse date queries like "tomorrow", "today", etc.
                date_range = self._parse_date_query(text)
                
                if date_range:
                    # Query for specific date range
                    start_date, end_date = date_range
                    calendar_response = self.calendar_manager.get_events_all_calendars(
                        start_date=start_date,
                        end_date=end_date,
                        max_results=10
                    )
                    print(f"📅 Querying calendar for date range: {start_date} to {end_date}")
                else:
                    # Get recent calendar events
                    calendar_response = self.calendar_manager.get_events_all_calendars(
                        max_results=5
                    )
                
                if calendar_response.success and calendar_response.events:
                    calendar_context = {
                        'query_date_range': date_range,
                        'events': [
                            {
                                'summary': event.summary,
                                'start_time': event.start_time.isoformat() if event.start_time else None,
                                'end_time': event.end_time.isoformat() if event.end_time else None
                            }
                            for event in calendar_response.events
                        ]
                    }
            
            # Generate conversational response
            response_text = self.conversation_manager.generate_response(
                conversation_id, text, calendar_context
            )
            
            print(f"🤖 AI Response: '{response_text}'")
            
            # Convert response to speech
            audio_data = self.tts_processor.text_to_speech(response_text, voice, model)

            # Prepare queried_date and queried_view for UI
            queried_date = None
            queried_view = None
            is_month_query = False
            if detected_keywords:
                if 'date_range' in locals() and date_range:
                    queried_date = [start_date.isoformat(), end_date.isoformat()]
                    # Determine if it's a week or month view
                    if (end_date - start_date).days >= 27:
                        queried_view = 'month'
                        is_month_query = True
                    elif (end_date - start_date).days >= 6:
                        queried_view = 'week'
                    else:
                        queried_view = 'day'
                elif 'date_range' in locals() and date_range is not None:
                    queried_date = date_range.isoformat() if hasattr(date_range, 'isoformat') else str(date_range)
                    queried_view = 'day'

            # If it's a month query, override the response text
            if is_month_query:
                response_text = "Here’s your calendar for this month. Is there a specific week or day you’d like to review?"

            if audio_data:
                print(f"🎤 Generated speech: {len(audio_data)} bytes")
                return AgentResponse(
                    success=True,
                    message=response_text,
                    confidence=0.9,
                    audio_response=audio_data,
                    queried_date=queried_date,
                    queried_view=queried_view
                )
            else:
                print("⚠️  TTS failed, returning text only")
                return AgentResponse(
                    success=True,
                    message=response_text,
                    confidence=0.9,
                    queried_date=queried_date,
                    queried_view=queried_view
                )
            
        except Exception as e:
            print(f"❌ Conversational text error: {e}")
            return AgentResponse(
                success=False,
                message=f"Error processing conversational text: {str(e)}",
                confidence=0.0
            )
    
    def get_conversation_history(self, conversation_id: str) -> list:
        """Get conversation history"""
        return self.conversation_manager.get_conversation_history(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        return self.conversation_manager.delete_conversation(conversation_id)
    
    def list_conversations(self, user_id: Optional[str] = None) -> list:
        """List conversations for a user"""
        return self.conversation_manager.list_conversations(user_id) 