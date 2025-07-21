#!/usr/bin/env python3
"""
Test calendar context for time-related queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calendar_agent import CalendarAgent

def test_calendar_context():
    print("🔍 Testing Calendar Context Detection")
    print("=" * 50)
    
    # Create calendar agent
    agent = CalendarAgent()
    
    # Test queries that should trigger calendar context
    test_queries = [
        "What's on my calendar tomorrow?",
        "When is my swim date with Callie?",
        "What do I have tomorrow?",
        "Do I have any appointments?",
        "What's my schedule like?",
        "When is my next meeting?",
        "What am I doing tomorrow?",
        "Got anything planned?",
        "What's happening tomorrow?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        
        # Start a new conversation
        conversation_id = agent.start_conversation()
        
        try:
            response = agent.process_conversational_text(
                text=query,
                conversation_id=conversation_id,
                voice="alloy",
                model="tts-1"
            )
            
            print(f"✅ Response: '{response.message[:100]}...'")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_calendar_context() 