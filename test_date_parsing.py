#!/usr/bin/env python3
"""
Test script to debug date parsing in conversational voice
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calendar_agent import CalendarAgent
from src.conversation_manager import ConversationManager

def test_date_parsing():
    print("🔍 Testing Date Parsing")
    print("=" * 50)
    
    # Create calendar agent
    agent = CalendarAgent()
    
    # Test queries
    test_queries = [
        "What's on my calendar tomorrow?",
        "Show me tomorrow's events",
        "What do I have tomorrow?",
        "Calendar for tomorrow",
        "What's on my calendar today?",
        "Show me this week's events"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        date_range = agent._parse_date_query(query)
        if date_range:
            start_date, end_date = date_range
            print(f"✅ Date range: {start_date} to {end_date}")
        else:
            print("❌ No date range found")
    
    # Test conversation manager date context
    print(f"\n📅 Testing Conversation Manager Date Context")
    print("=" * 50)
    
    conv_manager = ConversationManager()
    conv_id = conv_manager.create_conversation()
    
    # Test the date context that gets sent to OpenAI
    from datetime import datetime, timedelta
    current_time = datetime.now()
    tomorrow = current_time + timedelta(days=1)
    
    time_context = f"""
Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Today: {current_time.strftime('%A, %B %d, %Y')}
Tomorrow: {tomorrow.strftime('%A, %B %d, %Y')}

IMPORTANT: When the user asks about "tomorrow", they are referring to {tomorrow.strftime('%A, %B %d, %Y')}.
"""
    print(f"📅 Time context that gets sent to AI:")
    print(time_context)

if __name__ == "__main__":
    test_date_parsing() 