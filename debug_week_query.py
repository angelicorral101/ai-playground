#!/usr/bin/env python3
"""
Debug script to test week query date parsing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calendar_agent import CalendarAgent
from src.google_calendar import GoogleCalendarManager
from datetime import datetime, timedelta

def debug_week_query():
    """Debug the week query functionality"""
    
    print("Debugging Week Query...")
    print("=" * 50)
    
    try:
        agent = CalendarAgent()
        
        # Test the date parsing directly
        print("\n1. Testing date parsing:")
        test_queries = ["this week", "next week", "today", "tomorrow"]
        
        for query in test_queries:
            date_range = agent._parse_date_query(query)
            if date_range:
                start_date, end_date = date_range
                print(f"   '{query}' → {start_date} to {end_date}")
            else:
                print(f"   '{query}' → No date range found")
        
        # Test calendar manager directly with this week's date range
        print("\n2. Testing calendar manager with this week:")
        calendar = GoogleCalendarManager()
        
        # Get this week's date range
        now = datetime.now()
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"   This week: {monday} to {sunday}")
        
        # Test getting events for this week
        response = calendar.get_events_all_calendars(start_date=monday, end_date=sunday)
        print(f"   Calendar response: {response.success}")
        print(f"   Message: {response.message}")
        print(f"   Events found: {len(response.events or [])}")
        
        if response.events:
            for i, event in enumerate(response.events[:5]):
                print(f"     {i+1}. {event.summary} - {event.start_time}")
        
        # Test with a broader date range
        print("\n3. Testing with broader date range (next 30 days):")
        broad_start = datetime.now()
        broad_end = broad_start + timedelta(days=30)
        broad_response = calendar.get_events_all_calendars(start_date=broad_start, end_date=broad_end)
        print(f"   Calendar response: {broad_response.success}")
        print(f"   Message: {broad_response.message}")
        print(f"   Events found: {len(broad_response.events or [])}")
        
        if broad_response.events:
            for i, event in enumerate(broad_response.events[:5]):
                print(f"     {i+1}. {event.summary} - {event.start_time}")
        
        # Test the full agent pipeline
        print("\n4. Testing full agent pipeline:")
        from src.models import TextInput
        test_query = "What's my schedule for the week?"
        agent_response = agent.process_text_command(TextInput(message=test_query))
        print(f"   Query: '{test_query}'")
        print(f"   Success: {agent_response.success}")
        print(f"   Message: {agent_response.message}")
        
        if agent_response.calendar_response and agent_response.calendar_response.events:
            print(f"   Events found: {len(agent_response.calendar_response.events)}")
            for i, event in enumerate(agent_response.calendar_response.events[:3]):
                print(f"     {i+1}. {event.summary} - {event.start_time}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_week_query() 