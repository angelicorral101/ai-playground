from fastapi import FastAPI, File, UploadFile, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import json
import asyncio
from datetime import datetime
from typing import Optional

from .calendar_agent import CalendarAgent
from .models import VoiceInput, TextInput, SMSInput, AgentResponse
from .config import Config

app = FastAPI(title="AI Family Calendar Agent", version="1.0.0")

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
                voice_input = VoiceInput(audio_data=audio_data.encode())
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