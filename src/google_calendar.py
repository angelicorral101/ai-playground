import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser
from dateutil import tz
from .config import Config
from .models import CalendarEvent, CalendarResponse

class GoogleCalendarManager:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.calendar_id = Config.CALENDAR_ID
        self.scopes = Config.SCOPES
        self._authenticate()
        
        # Calendar name to ID mapping
        self.calendar_mapping = {
            'family': 'family04216910528477616445@group.calendar.google.com',
            'shared_family': 'family04216910528477616445@group.calendar.google.com',
            'work': 'angeli.corral@gmail.com',  # Default to primary for work
            'primary': 'angeli.corral@gmail.com',
            'main': 'angeli.corral@gmail.com'
        }
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        token_path = 'token.json'
        
        # Load existing credentials if available
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.scopes)
        
        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Create temporary credentials file for OAuth flow with proper security
                import tempfile
                import stat
                
                credentials_data = {
                    "installed": {
                        "client_id": Config.GOOGLE_CLIENT_ID,
                        "client_secret": Config.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                }
                
                # Create temporary file with restricted permissions
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_creds:
                    json.dump(credentials_data, temp_creds)
                    temp_creds_path = temp_creds.name
                
                # Set restrictive permissions (owner read/write only)
                os.chmod(temp_creds_path, stat.S_IRUSR | stat.S_IWUSR)
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(temp_creds_path, self.scopes)
                    creds = flow.run_local_server(port=0)
                finally:
                    # Clean up temporary credentials file
                    try:
                        os.unlink(temp_creds_path)
                        print(f"🗑️  Cleaned up temporary credentials file")
                    except OSError as e:
                        print(f"⚠️  Warning: Could not delete temporary credentials file: {e}")
            
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
    
    def _convert_to_chicago_time(self, dt: datetime) -> datetime:
        """Convert a datetime to America/Chicago timezone"""
        if dt.tzinfo is None:
            # If no timezone info, assume UTC
            dt = dt.replace(tzinfo=tz.UTC)
        
        # Convert to Chicago time
        chicago_tz = tz.gettz('America/Chicago')
        return dt.astimezone(chicago_tz)
    
    def _parse_event_time(self, time_str: str) -> datetime:
        """Parse event time and convert to Chicago timezone"""
        parsed_time = parser.parse(time_str)
        return self._convert_to_chicago_time(parsed_time)
    
    def create_event(self, event: CalendarEvent) -> CalendarResponse:
        """Create a new calendar event"""
        try:
            event_body = {
                'summary': event.summary,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'America/Chicago',  # Central Time
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'America/Chicago',
                },
                'location': event.location,
                'attendees': [{'email': email} for email in (event.attendees or [])],
                'reminders': event.reminders or {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                }
            }
            
            # Use specified calendar_id or default to primary calendar
            calendar_id = event.calendar_id or self.calendar_id
            
            # Map friendly calendar names to actual calendar IDs
            if calendar_id in self.calendar_mapping:
                calendar_id = self.calendar_mapping[calendar_id]
            
            event_result = self.service.events().insert(
                calendarId=calendar_id,
                body=event_body,
                sendUpdates='all'
            ).execute()
            
            return CalendarResponse(
                success=True,
                message=f"Event '{event.summary}' created successfully",
                event_id=event_result['id']
            )
            
        except HttpError as error:
            return CalendarResponse(
                success=False,
                message="Failed to create event",
                error=str(error)
            )
    
    def update_event(self, event_id: str, event: CalendarEvent) -> CalendarResponse:
        """Update an existing calendar event"""
        try:
            event_body = {
                'summary': event.summary,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'America/Chicago',
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'America/Chicago',
                },
                'location': event.location,
                'attendees': [{'email': email} for email in (event.attendees or [])],
            }
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event_body,
                sendUpdates='all'
            ).execute()
            
            return CalendarResponse(
                success=True,
                message=f"Event '{event.summary}' updated successfully",
                event_id=updated_event['id']
            )
            
        except HttpError as error:
            return CalendarResponse(
                success=False,
                message="Failed to update event",
                error=str(error)
            )
    
    def delete_event(self, event_id: str) -> CalendarResponse:
        """Delete a calendar event"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return CalendarResponse(
                success=True,
                message="Event deleted successfully"
            )
            
        except HttpError as error:
            return CalendarResponse(
                success=False,
                message="Failed to delete event",
                error=str(error)
            )
    
    def get_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, 
                   max_results: int = 10) -> CalendarResponse:
        """Get calendar events within a date range"""
        try:
            if not start_date:
                start_date = datetime.utcnow()
            if not end_date:
                end_date = start_date + timedelta(days=7)

            def format_gcal_time(dt):
                if dt.tzinfo is None:
                    return dt.isoformat() + 'Z'
                else:
                    return dt.isoformat()

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=format_gcal_time(start_date),
                timeMax=format_gcal_time(end_date),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            calendar_events = []

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                calendar_events.append(CalendarEvent(
                    id=event.get('id'),
                    summary=event['summary'],
                    description=event.get('description'),
                    start_time=self._parse_event_time(start),
                    end_time=self._parse_event_time(end),
                    location=event.get('location'),
                    attendees=[attendee['email'] for attendee in event.get('attendees', [])]
                ))

            return CalendarResponse(
                success=True,
                message=f"Found {len(calendar_events)} events",
                events=calendar_events
            )

        except HttpError as error:
            return CalendarResponse(
                success=False,
                message="Failed to retrieve events",
                error=str(error)
            )
    
    def list_calendars(self) -> CalendarResponse:
        """List all available calendars"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = []
            for cal in calendar_list['items']:
                calendars.append({
                    'id': cal['id'],
                    'summary': cal['summary'],
                    'description': cal.get('description', ''),
                    'primary': cal.get('primary', False)
                })
            return CalendarResponse(
                success=True,
                message=f"Found {len(calendars)} calendars",
                calendars=calendars,
                events=None,
                error=None
            )
        except HttpError as error:
            return CalendarResponse(
                success=False,
                message="Failed to list calendars",
                error=str(error)
            )

    def search_events(self, query: str, max_results: int = 10) -> CalendarResponse:
        """Search for events by query string"""
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            calendar_events = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                calendar_events.append(CalendarEvent(
                    id=event.get('id'),
                    summary=event['summary'],
                    description=event.get('description'),
                    start_time=self._parse_event_time(start),
                    end_time=self._parse_event_time(end),
                    location=event.get('location'),
                    attendees=[attendee['email'] for attendee in event.get('attendees', [])]
                ))
            
            return CalendarResponse(
                success=True,
                message=f"Found {len(calendar_events)} events matching '{query}'",
                events=calendar_events
            )
            
        except HttpError as error:
            return CalendarResponse(
                success=False,
                message="Failed to search events",
                error=str(error)
            ) 

    def get_events_all_calendars(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, max_results: int = 10) -> CalendarResponse:
        """Get events from all calendars within a date range and combine them."""
        try:
            if not start_date:
                start_date = datetime.utcnow()
            if not end_date:
                end_date = start_date + timedelta(days=7)

            print(f"[DEBUG] get_events_all_calendars: start_date={start_date} end_date={end_date}")

            # Helper to format datetime for Google API
            def format_gcal_time(dt):
                if dt.tzinfo is None:
                    return dt.isoformat() + 'Z'
                else:
                    return dt.isoformat()

            # Get all calendar IDs
            calendar_list_resp = self.list_calendars()
            if not calendar_list_resp.success or not getattr(calendar_list_resp, 'calendars', None):
                print(f"[DEBUG] Failed to list calendars: {calendar_list_resp.error}")
                return CalendarResponse(success=False, message="Failed to list calendars", error=calendar_list_resp.error)
            calendar_ids = [cal['id'] for cal in getattr(calendar_list_resp, 'calendars', [])]
            print(f"[DEBUG] Querying {len(calendar_ids)} calendars: {calendar_ids}")

            all_events = []
            for cal_id in calendar_ids:
                try:
                    print(f"[DEBUG] Querying calendar: {cal_id}")
                    events_result = self.service.events().list(
                        calendarId=cal_id,
                        timeMin=format_gcal_time(start_date),
                        timeMax=format_gcal_time(end_date),
                        maxResults=max_results,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    events = events_result.get('items', [])
                    print(f"[DEBUG] Found {len(events)} events in calendar {cal_id}")
                    for event in events:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        end = event['end'].get('dateTime', event['end'].get('date'))
                        all_events.append(CalendarEvent(
                            id=event.get('id'),
                            summary=event['summary'],
                            description=event.get('description'),
                            start_time=self._parse_event_time(start),
                            end_time=self._parse_event_time(end),
                            location=event.get('location'),
                            attendees=[attendee['email'] for attendee in event.get('attendees', [])]
                        ))
                except Exception as e:
                    print(f"[DEBUG] Error querying calendar {cal_id}: {e}")
                    continue  # Skip calendars that error out

            # Sort all events by start_time
            all_events.sort(key=lambda e: e.start_time)
            print(f"[DEBUG] Total events found across all calendars: {len(all_events)}")
            return CalendarResponse(
                success=True,
                message=f"Found {len(all_events)} events across all calendars",
                events=all_events
            )
        except Exception as error:
            print(f"[DEBUG] Exception in get_events_all_calendars: {error}")
            return CalendarResponse(
                success=False,
                message="Failed to retrieve events from all calendars",
                error=str(error)
            ) 