#!/usr/bin/env python3
"""
Test script to check LLM output for week-based queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.nlp_processor import NLPProcessor
from src.models import InputType

def test_llm_output():
    """Test LLM output for various queries"""
    
    processor = NLPProcessor()
    
    test_queries = [
        "What's my schedule for the week?",
        "Show me my events this week",
        "What do I have planned this week?",
        "What's on my calendar tomorrow?",
        "Schedule a meeting tomorrow at 2pm"
    ]
    
    print("Testing LLM Output...")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("-" * 40)
        
        try:
            result = processor.process_text(query, InputType.TEXT)
            
            print(f"✅ Action: {result.action}")
            print(f"📅 Event Summary: {result.event.summary if result.event else 'None'}")
            print(f"📅 Start Time: {result.event.start_time if result.event else 'None'}")
            print(f"📅 End Time: {result.event.end_time if result.event else 'None'}")
            print(f"🔍 Query: '{result.query}'")
            print(f"🎯 Confidence: {result.confidence}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_llm_output() 