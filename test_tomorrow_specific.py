#!/usr/bin/env python3
"""
Test script specifically for tomorrow query debugging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_tomorrow_query():
    print("🔍 Testing Tomorrow Query Specifically")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Start a new conversation
    print("1. Starting new conversation...")
    response = requests.post(f"{base_url}/api/conversation/start")
    if response.status_code == 200:
        conversation_id = response.json()["conversation_id"]
        print(f"✅ Conversation started: {conversation_id}")
    else:
        print(f"❌ Failed to start conversation: {response.status_code}")
        return
    
    # Test tomorrow query
    print("\n2. Testing 'What's on my calendar tomorrow?' query...")
    
    payload = {
        "conversation_id": conversation_id,
        "message": "What's on my calendar tomorrow?",
        "voice": "alloy",
        "model": "tts-1"
    }
    
    response = requests.post(
        f"{base_url}/api/conversation/text",
        data=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response received")
        print(f"📝 AI Response: '{result.get('message', 'No message')}'")
        print(f"🎤 Audio response: {'Yes' if result.get('audio_response') else 'No'}")
        
        # Get conversation history to see what happened
        print("\n3. Getting conversation history...")
        history_response = requests.get(f"{base_url}/api/conversation/{conversation_id}/history")
        if history_response.status_code == 200:
            history_data = history_response.json()
            history = history_data.get("history", [])
            print(f"✅ Found {len(history)} messages:")
            for i, msg in enumerate(history[-4:], 1):  # Show last 4 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
                print(f"   {i}. {role}: {content}")
        else:
            print(f"❌ Failed to get history: {history_response.status_code}")
            print(f"Response: {history_response.text}")
    else:
        print(f"❌ Failed to process text: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_tomorrow_query() 