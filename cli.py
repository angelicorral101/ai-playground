#!/usr/bin/env python3
"""
Command Line Interface for AI Family Calendar Agent
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.calendar_agent import CalendarAgent
from src.config import Config

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🗓️  AI Family Calendar Agent - CLI Mode")
    print("=" * 60)
    print("Type 'help' for commands, 'quit' to exit")
    print("=" * 60)

def print_help():
    """Print help information"""
    print("\n📋 Available Commands:")
    print("  text <command>     - Process text command")
    print("  voice              - Record and process voice command")
    print("  list               - List upcoming events")
    print("  search <query>     - Search for events")
    print("  help               - Show this help")
    print("  quit               - Exit the application")
    print("\n💡 Example Commands:")
    print("  text Schedule a meeting tomorrow at 2pm")
    print("  text What's on my calendar today?")
    print("  text Add dentist appointment on Friday at 3pm")
    print("  search meeting")
    print("  voice")

async def main():
    """Main CLI function"""
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated successfully")
        
        # Initialize the agent
        agent = CalendarAgent()
        print("🤖 AI Calendar Agent initialized")
        
        print_banner()
        
        while True:
            try:
                # Get user input
                user_input = input("\n🎯 Enter command: ").strip()
                
                if not user_input:
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == 'quit' or command == 'exit':
                    print("👋 Goodbye!")
                    break
                
                elif command == 'help':
                    print_help()
                
                elif command == 'text':
                    if not args:
                        print("❌ Please provide a text command")
                        print("Example: text Schedule a meeting tomorrow at 2pm")
                        continue
                    
                    print(f"📝 Processing: {args}")
                    from src.models import TextInput
                    response = agent.process_text_command(TextInput(message=args))
                    print(f"🤖 Response: {response.message}")
                    
                    if response.suggestions:
                        print("💡 Suggestions:")
                        for suggestion in response.suggestions:
                            print(f"   • {suggestion}")
                
                elif command == 'voice':
                    print("🎤 Recording voice command... (5 seconds)")
                    print("   Speak now!")
                    
                    response = agent.record_and_process(duration=5)
                    print(f"🤖 Response: {response.message}")
                    
                    if response.suggestions:
                        print("💡 Suggestions:")
                        for suggestion in response.suggestions:
                            print(f"   • {suggestion}")
                
                elif command == 'list':
                    print("📅 Fetching upcoming events...")
                    from src.models import TextInput
                    response = agent.process_text_command(TextInput(message="Show my events this week"))
                    print(f"🤖 Response: {response.message}")
                
                elif command == 'search':
                    if not args:
                        print("❌ Please provide a search query")
                        print("Example: search meeting")
                        continue
                    
                    print(f"🔍 Searching for: {args}")
                    from src.models import TextInput
                    response = agent.process_text_command(TextInput(message=f"Find events about {args}"))
                    print(f"🤖 Response: {response.message}")
                
                else:
                    # Treat as text command
                    print(f"📝 Processing: {user_input}")
                    from src.models import TextInput
                    response = agent.process_text_command(TextInput(message=user_input))
                    print(f"🤖 Response: {response.message}")
                    
                    if response.suggestions:
                        print("💡 Suggestions:")
                        for suggestion in response.suggestions:
                            print(f"   • {suggestion}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("💡 Try 'help' for available commands")
    
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your environment variables in the .env file")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 