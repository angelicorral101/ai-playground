from fastapi import FastAPI, File, UploadFile, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from datetime import datetime
from typing import Optional

from .calendar_agent import CalendarAgent
from .models import VoiceInput, TextInput, SMSInput, AgentResponse
from .config import Config

app = FastAPI(title="AI Family Calendar Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the calendar agent
agent = CalendarAgent()

# Templates for web interface
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    try:
        Config.validate()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your environment variables")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/text")
async def process_text_command(message: str = Form(...), user_id: Optional[str] = Form(None)):
    """Process text command"""
    try:
        text_input = TextInput(message=message, user_id=user_id)
        response = agent.process_text_command(text_input)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events")
async def get_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 50
):
    """Get calendar events within a date range"""
    try:
        from datetime import datetime
        from dateutil import parser
        
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = parser.parse(start_date)
            except:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = parser.parse(end_date)
            except:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Get events from calendar manager
        calendar_response = agent.calendar_manager.get_events_all_calendars(
            start_date=start_dt,
            end_date=end_dt,
            max_results=max_results
        )
        
        if not calendar_response.success:
            raise HTTPException(status_code=500, detail=calendar_response.error or "Failed to retrieve events")
        
        return {
            "success": True,
            "events": [
                {
                    "id": getattr(event, 'id', None),
                    "summary": event.summary,
                    "description": event.description,
                    "start_time": event.start_time.isoformat() if event.start_time else None,
                    "end_time": event.end_time.isoformat() if event.end_time else None,
                    "location": event.location,
                    "attendees": event.attendees or [],
                    "calendar_id": getattr(event, 'calendar_id', None)
                }
                for event in (calendar_response.events or [])
            ],
            "message": calendar_response.message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sms")
async def process_sms_command(
    from_number: str = Form(...),
    message: str = Form(...),
    timestamp: Optional[str] = Form(None)
):
    """Process SMS command (for Twilio webhook)"""
    try:
        if timestamp:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        else:
            parsed_timestamp = datetime.now()
        
        sms_input = SMSInput(
            from_number=from_number,
            message=message,
            timestamp=parsed_timestamp
        )
        
        response = agent.process_sms_command(sms_input)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/record")
async def record_and_process(duration: int = Form(5)):
    """Record voice from microphone and process"""
    try:
        response = agent.record_and_process(duration)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice")
async def process_voice_file(request: Request):
    """Process uploaded voice file"""
    try:
        print("=" * 50)
        print("🎤 VOICE API REQUEST RECEIVED")
        print("=" * 50)
        
        # Get the filename from headers
        filename = request.headers.get('X-Filename', 'voice_command.m4a')
        content_type = request.headers.get('Content-Type', 'audio/mp4')
        
        print(f"📁 Filename from header: {filename}")
        print(f"📁 Content-Type: {content_type}")
        
        # Read the binary data directly
        audio_data = await request.body()
        print(f"📁 Read binary data: {len(audio_data)} bytes")
        
        # Log first few bytes for debugging
        if len(audio_data) > 0:
            print(f"🔍 First 50 bytes: {audio_data[:50]}")
            print(f"🔍 File signature: {audio_data[:4].hex()}")
        else:
            print("⚠️  WARNING: Binary data is empty!")
        
        # Check if file is empty
        if len(audio_data) == 0:
            print("❌ ERROR: Empty audio file received")
            raise HTTPException(status_code=400, detail="Empty audio file received")
        
        print(f"✅ Binary data has {len(audio_data)} bytes")
        
        # Detect audio format from filename
        format = agent.voice_processor.detect_audio_format(audio_data, filename)
        print(f"🎵 Detected format: {format}")
        
        # Create VoiceInput object with detected format
        voice_input = VoiceInput(audio_data=audio_data, format=format)
        print(f"📦 Created VoiceInput object: {len(voice_input.audio_data)} bytes, format: {voice_input.format}")
        
        # Process the voice command
        print("🔄 Processing voice command...")
        response = agent.process_voice_command(voice_input)
        print(f"✅ Voice command processed: {response.success}")
        print(f"📝 Response message: {response.message}")
        
        print("=" * 50)
        print("🎤 VOICE API REQUEST COMPLETED")
        print("=" * 50)
        
        return response
        
    except HTTPException as he:
        print(f"❌ HTTP Exception: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        print(f"❌ Unexpected API Error: {type(e).__name__}: {e}")
        import traceback
        print(f"📚 Full traceback:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time communication
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "text":
                text_input = TextInput(message=message_data["message"])
                response = agent.process_text_command(text_input)
                await manager.send_personal_message(
                    json.dumps(response.dict()), 
                    websocket
                )
            
            elif message_data.get("type") == "voice":
                # Handle voice data from WebSocket
                audio_data = message_data["audio_data"]
                format = message_data.get("format", "wav")  # Get format from message or default to wav
                voice_input = VoiceInput(audio_data=audio_data.encode(), format=format)
                response = agent.process_voice_command(voice_input)
                await manager.send_personal_message(
                    json.dumps(response.dict()), 
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Twilio webhook endpoint
@app.post("/webhook/twilio")
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """Twilio webhook for SMS processing"""
    try:
        sms_input = SMSInput(
            from_number=From,
            message=Body,
            timestamp=datetime.now()
        )
        
        response = agent.process_sms_command(sms_input)
        
        # Return TwiML response for SMS
        return {
            "response": response.message,
            "success": response.success
        }
        
    except Exception as e:
        return {
            "response": f"Error processing SMS: {str(e)}",
            "success": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 