#!/usr/bin/env python3
"""
AI Family Calendar Agent
A voice and text-powered calendar management system that integrates with Google Calendar.
"""

import uvicorn
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api import app
from src.config import Config

def main():
    """Main entry point for the application"""
    try:
        # Validate configuration
        Config.validate()
        print("🚀 Starting AI Family Calendar Agent...")
        print("📅 Connected to Google Calendar")
        print("🎤 Voice commands enabled")
        print("📱 SMS integration ready")
        print("🌐 Web interface available at http://localhost:8000")
        
        # Start the server
        uvicorn.run(
            "src.api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your environment variables in the .env file")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Family Calendar Agent...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 