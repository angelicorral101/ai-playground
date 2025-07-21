#!/usr/bin/env python3
"""
Direct test of calendar agent method
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calendar_agent import CalendarAgent

def test_direct_call():
    print("🔍 Testing Direct Calendar Agent Call")
    print("=" * 50)
    
    # Create calendar agent
    agent = CalendarAgent()
    
    # Start a conversation
    conversation_id = agent.start_conversation()
    print(f"✅ Conversation started: {conversation_id}")
    
    # Test the method directly
    print(f"\n📝 Testing process_conversational_text directly...")
    
    try:
        response = agent.process_conversational_text(
            text="What's on my calendar tomorrow?",
            conversation_id=conversation_id,
            voice="alloy",
            model="tts-1"
        )
        
        print(f"✅ Response received")
        print(f"📝 Success: {response.success}")
        print(f"📝 Message: '{response.message}'")
        print(f"🎤 Audio: {'Yes' if response.audio_response else 'No'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_call() 