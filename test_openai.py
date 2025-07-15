#!/usr/bin/env python3
"""
Simple test script to see what OpenAI is returning
"""

import requests
import json

def test_openai_response():
    """Test the OpenAI API through our web interface"""
    
    # Test data
    test_commands = [
        "Schedule a meeting tomorrow at 3pm",
        "What's on my calendar today?",
        "Add a dentist appointment next Friday at 2pm"
    ]
    
    for command in test_commands:
        print(f"\n{'='*50}")
        print(f"Testing command: '{command}'")
        print(f"{'='*50}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/text",
                data={"message": command},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_openai_response() 