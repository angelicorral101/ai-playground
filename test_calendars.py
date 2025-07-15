#!/usr/bin/env python3
"""
Test script to list available calendars and test calendar selection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.google_calendar import GoogleCalendarManager
from src.nlp_processor import NLPProcessor
from src.models import InputType

def test_calendars():
    """Test calendar listing and selection"""
    
    print("Testing Calendar Functionality...")
    
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
        
        # Test NLP processing with calendar selection
        print("\n2. Testing NLP with calendar selection:")
        processor = NLPProcessor()
        
        test_commands = [
            "Schedule an event tomorrow for 'Amelie's Art Camp' at 9am-12 noon",
            "Schedule an event tomorrow for 'Amelie's Art Camp' at 9am-12 noon, put it on my Shared Family calendar",
            "Schedule a meeting tomorrow at 2pm on my work calendar",
            "Add a dentist appointment next Friday at 2pm on the family calendar"
        ]
        
        for command in test_commands:
            print(f"\nTesting: '{command}'")
            result = processor.process_text(command, InputType.TEXT)
            print(f"Calendar ID: {result.event.calendar_id if result.event else 'None'}")
            print(f"Summary: {result.event.summary if result.event else 'None'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calendars() 