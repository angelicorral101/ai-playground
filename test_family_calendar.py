#!/usr/bin/env python3
"""
Test script to create an event on the Family calendar
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.google_calendar import GoogleCalendarManager
from src.models import CalendarEvent
from datetime import datetime, timedelta

def test_family_calendar():
    """Test creating an event on the Family calendar"""
    
    print("Testing Family Calendar Event Creation...")
    
    try:
        # Initialize calendar manager
        calendar = GoogleCalendarManager()
        
        # Create a test event for the Family calendar
        test_event = CalendarEvent(
            summary="Test Family Event",
            description="This is a test event for the Family calendar",
            start_time=datetime.now() + timedelta(days=1, hours=10),  # Tomorrow at 10am
            end_time=datetime.now() + timedelta(days=1, hours=11),    # Tomorrow at 11am
            location="Home",
            attendees=[],
            calendar_id="family"  # This will be mapped to the Family calendar ID
        )
        
        print(f"Creating event: {test_event.summary}")
        print(f"Calendar ID: {test_event.calendar_id}")
        print(f"Start time: {test_event.start_time}")
        print(f"End time: {test_event.end_time}")
        
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
    test_family_calendar() 