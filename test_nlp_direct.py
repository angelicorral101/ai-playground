#!/usr/bin/env python3
"""
Direct test of the NLP processor to see OpenAI responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.nlp_processor import NLPProcessor
from src.models import InputType

def test_nlp_direct():
    """Test the NLP processor directly"""
    
    processor = NLPProcessor()
    
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
            result = processor.process_text(command, InputType.TEXT)
            print(f"✅ Success!")
            print(f"Action: {result.action}")
            print(f"Event: {result.event}")
            print(f"Query: {result.query}")
            print(f"Confidence: {result.confidence}")
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_nlp_direct() 