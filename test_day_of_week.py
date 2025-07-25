#!/usr/bin/env python3
"""
Test day of the week calculations
"""

from datetime import datetime, timedelta

def test_day_of_week():
    print("🔍 Testing Day of Week Calculations")
    print("=" * 50)
    
    # Current date
    current_time = datetime.now()
    print(f"📅 Current date: {current_time.strftime('%A, %B %d, %Y')}")
    
    # Test next few days
    for i in range(1, 8):
        future_date = current_time + timedelta(days=i)
        print(f"📅 +{i} day: {future_date.strftime('%A, %B %d, %Y')}")
    
    # Specifically test July 23, 2025
    july_23 = datetime(2025, 7, 23)
    print(f"\n🎯 July 23, 2025: {july_23.strftime('%A, %B %d, %Y')}")
    
    # Test the time context that gets sent to AI
    print(f"\n⏰ Time context sent to AI:")
    tomorrow = current_time + timedelta(days=1)
    time_context = f"""
Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Today: {current_time.strftime('%A, %B %d, %Y')}
Tomorrow: {tomorrow.strftime('%A, %B %d, %Y')}

IMPORTANT: When the user asks about "tomorrow", they are referring to {tomorrow.strftime('%A, %B %d, %Y')}.
"""
    print(time_context)

    # Test weekday queries
    print("\n🎯 Testing weekday queries:")
    queries = [
        "Wednesday",
        "on Wednesday",
        "next Wednesday",
        "wednesday schedule",
        "what's on my calendar on Wednesday?"
    ]
    from src.calendar_agent import CalendarAgent
    agent = CalendarAgent()
    for q in queries:
        result = agent._parse_date_query(q)
        if result:
            start, end = result
            print(f"Query: '{q}' => {start.strftime('%A, %B %d, %Y')} to {end.strftime('%A, %B %d, %Y')}")
        else:
            print(f"Query: '{q}' => No date found")

if __name__ == "__main__":
    test_day_of_week() 