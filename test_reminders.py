#!/usr/bin/env python3
"""
Test script to test reminder/notification functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.nlp_processor import NLPProcessor
from src.models import InputType

def test_reminders():
    """Test reminder/notification parsing"""
    
    print("Testing Reminder/Notification Functionality...")
    
    try:
        processor = NLPProcessor()
        
        test_commands = [
            "Schedule an event tomorrow for 'Amelie's Art Camp' at 9am-12 noon, put it on my Shared Family calendar",
            "Schedule an event tomorrow for 'Amelie's Art Camp' at 9am-12 noon, put it on my Shared Family calendar, alert 1 hour before",
            "Schedule an event tomorrow for 'Amelie's Art Camp' at 9am-12 noon, put it on my Shared Family calendar, notify 30 minutes before event start",
            "Schedule a meeting tomorrow at 2pm, remind me 2 hours before",
            "Add a dentist appointment next Friday at 2pm, email reminder 1 day before",
            "Schedule a family dinner next Saturday at 6pm, alert 15 minutes before and 1 hour before"
        ]
        
        for command in test_commands:
            print(f"\n{'='*60}")
            print(f"Testing: '{command}'")
            print(f"{'='*60}")
            
            result = processor.process_text(command, InputType.TEXT)
            
            if result.event:
                print(f"Summary: {result.event.summary}")
                print(f"Calendar ID: {result.event.calendar_id}")
                print(f"Start time: {result.event.start_time}")
                print(f"End time: {result.event.end_time}")
                print(f"Reminders: {result.event.reminders}")
            else:
                print("No event created")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reminders() 