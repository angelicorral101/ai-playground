#!/usr/bin/env python3
"""
Test script to verify week query functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calendar_agent import CalendarAgent
from src.models import TextInput

def test_week_query():
    """Test week query functionality"""
    
    print("Testing Week Query Functionality...")
    print("=" * 50)
    
    try:
        agent = CalendarAgent()
        
        test_queries = [
            "What's my schedule for the week?",
            "Show me my events this week",
            "What do I have planned this week?",
            "What's on my calendar today?",
            "What's on my calendar tomorrow?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: '{query}'")
            print("-" * 40)
            
            try:
                response = agent.process_text_command(TextInput(message=query))
                print(f"✅ Success: {response.success}")
                print(f"📝 Message: {response.message}")
                
                if response.calendar_response and response.calendar_response.events:
                    print(f"📅 Found {len(response.calendar_response.events)} events")
                    for i, event in enumerate(response.calendar_response.events[:3]):  # Show first 3
                        print(f"   {i+1}. {event.summary} - {event.start_time.strftime('%B %d at %I:%M %p')}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_week_query() 