#!/usr/bin/env python3
"""
Simple test to check OpenAI client initialization
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from openai import OpenAI  # type: ignore

def test_openai_client():
    """Test OpenAI client initialization"""
    
    print("Testing OpenAI client initialization...")
    
    try:
        # Test 1: Basic initialization
        print("1. Testing basic OpenAI client...")
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        print("✅ Basic client created successfully")
        
        # Test 2: Simple API call
        print("2. Testing simple API call...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Say hello"}
            ],
            max_tokens=10
        )
        
        content = response.choices[0].message.content
        print(f"✅ API call successful: {content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_openai_client() 