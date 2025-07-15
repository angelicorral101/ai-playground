#!/usr/bin/env python3
"""
Test script to check Google Calendar configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.google_calendar import GoogleCalendarManager
from src.models import CalendarEvent
from datetime import datetime, timedelta

def test_calendar():
    """Test Google Calendar functionality"""
    
    print("Testing Google Calendar configuration...")
    
    try:
        # Initialize calendar manager
        calendar = GoogleCalendarManager()
        
        # List available calendars
        print("\n1. Available calendars:")
        calendar_list = calendar.service.calendarList().list().execute()
        for cal in calendar_list['items']:
            print(f"  - {cal['summary']} (ID: {cal['id']})")
            if cal.get('primary'):
                print(f"    * This is your primary calendar")
        
        # Check current calendar ID
        print(f"\n2. Current calendar ID: {calendar.calendar_id}")
        
        # Test creating a simple event
        print("\n3. Testing event creation...")
        test_event = CalendarEvent(
            summary="Test Event - Please Delete",
            description="This is a test event to verify calendar integration",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            location="Test Location"
        )
        
        result = calendar.create_event(test_event)
        print(f"   Result: {result.success}")
        print(f"   Message: {result.message}")
        if result.event_id:
            print(f"   Event ID: {result.event_id}")
        
        # Test reading events
        print("\n4. Testing event reading...")
        read_result = calendar.get_events(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        print(f"   Found {len(read_result.events or [])} events")
        for event in (read_result.events or []):
            print(f"   - {event.summary} at {event.start_time}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calendar() 