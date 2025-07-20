# 🗓️ AI Family Calendar Agent

An intelligent calendar management system that uses AI to organize your family calendar through voice commands and text messages. Seamlessly integrates with Google Calendar for real-time synchronization.

## ✨ Features

- **🎤 Voice Commands**: Speak naturally to create, update, or check calendar events (supports multiple audio formats)
- **📝 Text Processing**: Send commands via text for quick calendar management
- **📱 SMS Integration**: Manage your calendar through SMS messages (Twilio integration)
- **🤖 AI-Powered**: Uses OpenAI's GPT and Whisper for natural language understanding
- **📅 Google Calendar Sync**: Real-time synchronization with your family Google Calendar
- **🌐 Web Interface**: Beautiful, responsive web interface for easy interaction
- **🔔 Smart Reminders**: Automatic reminder setup for all events
- **👨‍👩‍👧‍👦 Family-Friendly**: Designed for family calendar management

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Calendar API credentials
- OpenAI API key
- (Optional) Twilio account for SMS integration

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-playground
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Configure Google Calendar API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Add your credentials to the `.env` file

5. **Get OpenAI API Key**
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Generate an API key
   - Add it to your `.env` file

6. **Run the application**
   ```bash
   python main.py
   ```

7. **Access the web interface**
   - Open your browser to `http://localhost:8000`
   - Start managing your calendar with voice and text commands!

## 📋 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Calendar API Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Twilio Configuration (for SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Application Configuration
SECRET_KEY=your_secret_key_here
CALENDAR_ID=primary
```

### Google Calendar Setup

1. **Enable Google Calendar API**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Select your project
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API" and enable it

2. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file
   - Extract `client_id` and `client_secret` to your `.env` file

3. **Set Calendar ID**
   - For your primary calendar: `CALENDAR_ID=primary`
   - For a specific calendar: `CALENDAR_ID=calendar_id@group.calendar.google.com`

## 💬 Usage Examples

### Voice Commands

The system supports multiple audio formats including WAV, MP3, M4A, AAC, OGG, FLAC, and WMA. Audio files are automatically converted to WAV format before processing with OpenAI Whisper.

Try these natural language commands:

**Creating Events:**
- "Schedule a dentist appointment tomorrow at 3pm"
- "Add soccer practice on Tuesday at 4pm"
- "Book a dinner reservation for Saturday at 7pm"
- "Create a meeting with John on Friday at 2pm"

**Checking Calendar:**
- "What's on my calendar today?"
- "Show my events this week"
- "Do I have any meetings tomorrow?"
- "What's my schedule for Friday?"

**Managing Events:**
- "Cancel my dentist appointment"
- "Update the meeting time to 3pm"
- "Move the soccer practice to Wednesday"

### Text Commands

Send the same commands via text input in the web interface or through SMS.

### SMS Integration

If you have Twilio configured, you can text commands to your Twilio phone number:

```
Text: "Schedule doctor appointment tomorrow 2pm"
Response: "✅ Event 'doctor appointment' created successfully"

Text: "What's on my calendar today?"
Response: "📅 Found 2 events: • Team meeting - December 15 at 10:00 AM • Lunch with Sarah - December 15 at 12:00 PM"
```

## 🏗️ Architecture

The application is built with a modular architecture:

```
src/
├── config.py          # Configuration management
├── models.py          # Pydantic data models
├── voice_processor.py # Voice-to-text processing
├── nlp_processor.py   # Natural language understanding
├── google_calendar.py # Google Calendar integration
├── calendar_agent.py  # Main AI agent logic
└── api.py            # FastAPI web application

templates/
└── index.html        # Web interface

main.py               # Application entry point
```

### Key Components

1. **VoiceProcessor**: Handles speech-to-text conversion using OpenAI Whisper with automatic audio format conversion
2. **NLPProcessor**: Processes natural language commands using OpenAI GPT
3. **GoogleCalendarManager**: Manages Google Calendar operations
4. **CalendarAgent**: Orchestrates all components and provides the main interface
5. **FastAPI App**: Provides REST API and web interface

## 🔧 API Endpoints

### Web Interface
- `GET /` - Main web interface
- `GET /health` - Health check

### Calendar Operations
- `POST /api/text` - Process text commands
- `POST /api/voice` - Process voice commands (audio file upload)
- `POST /api/record` - Record and process voice from microphone
- `POST /api/sms` - Process SMS commands

### WebSocket
- `WS /ws` - Real-time communication for voice and text

### Twilio Integration
- `POST /webhook/twilio` - Twilio webhook for SMS processing

## 🛠️ Development

### Running in Development Mode

```bash
python main.py
```

The application will start with auto-reload enabled.

### Testing

```bash
# Test the API endpoints
curl -X POST "http://localhost:8000/api/text" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=What's on my calendar today?"
```

### Project Structure

```
ai-playground/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration
│   ├── models.py          # Data models
│   ├── voice_processor.py # Voice processing
│   ├── nlp_processor.py   # NLP processing
│   ├── google_calendar.py # Calendar integration
│   ├── calendar_agent.py  # Main agent
│   └── api.py            # FastAPI app
├── templates/             # Web templates
│   └── index.html        # Main interface
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
├── main.py              # Entry point
└── README.md            # This file
```

## 🔒 Security Considerations

- Store API keys securely in environment variables
- Use HTTPS in production
- Implement proper authentication for family members
- Regularly rotate API keys
- Monitor API usage and costs

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment
1. Set up a production server (AWS, Google Cloud, etc.)
2. Configure environment variables
3. Use a production WSGI server like Gunicorn
4. Set up reverse proxy (Nginx)
5. Configure SSL certificates

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the configuration in your `.env` file
2. Ensure all API keys are valid
3. Verify Google Calendar API is enabled
4. Check the application logs for error messages

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Calendar sharing between family members
- [ ] Advanced event templates
- [ ] Integration with other calendar providers
- [ ] Mobile app development
- [ ] Advanced reminder system
- [ ] Calendar analytics and insights

---

**Happy Calendar Management! 🗓️✨**
