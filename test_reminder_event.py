#!/usr/bin/env python3
"""
Test script to create an actual event with reminders
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.google_calendar import GoogleCalendarManager
from src.models import CalendarEvent
from datetime import datetime, timedelta

def test_reminder_event():
    """Test creating an event with reminders"""
    
    print("Testing Event Creation with Reminders...")
    
    try:
        # Initialize calendar manager
        calendar = GoogleCalendarManager()
        
        # Create a test event with reminders
        test_event = CalendarEvent(
            summary="Test Event with Reminders",
            description="This is a test event with custom reminders",
            start_time=datetime.now() + timedelta(days=1, hours=10),  # Tomorrow at 10am
            end_time=datetime.now() + timedelta(days=1, hours=11),    # Tomorrow at 11am
            location="Home",
            attendees=[],
            calendar_id="family",  # Family calendar
            reminders={
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},   # 1 hour before
                    {'method': 'email', 'minutes': 1440}  # 1 day before
                ]
            }
        )
        
        print(f"Creating event: {test_event.summary}")
        print(f"Calendar ID: {test_event.calendar_id}")
        print(f"Start time: {test_event.start_time}")
        print(f"End time: {test_event.end_time}")
        print(f"Reminders: {test_event.reminders}")
        
        # Create the event
        response = calendar.create_event(test_event)
        
        if response.success:
            print(f"✅ Success! Event created with ID: {response.event_id}")
            print(f"Message: {response.message}")
        else:
            print(f"❌ Failed to create event: {response.error}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reminder_event() 