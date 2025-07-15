from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class InputType(str, Enum):
    VOICE = "voice"
    TEXT = "text"
    SMS = "sms"

class CalendarAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    LIST = "list"

class CalendarEvent(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminders: Optional[Dict[str, Any]] = None
    calendar_id: Optional[str] = None  # Calendar ID to create the event on

class ProcessedCommand(BaseModel):
    action: CalendarAction
    event: Optional[CalendarEvent] = None
    query: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    raw_input: str
    input_type: InputType
    additional_events: Optional[List[Dict[str, Any]]] = None  # Additional events data for multiple event creation

class VoiceInput(BaseModel):
    audio_data: bytes
    format: str = "wav"

class TextInput(BaseModel):
    message: str
    user_id: Optional[str] = None

class SMSInput(BaseModel):
    from_number: str
    message: str
    timestamp: datetime

class CalendarResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[str] = None
    events: Optional[List[CalendarEvent]] = None
    error: Optional[str] = None
    calendars: Optional[List[Dict[str, Any]]] = None

class AgentResponse(BaseModel):
    success: bool
    message: str
    calendar_response: Optional[CalendarResponse] = None
    confidence: float
    suggestions: Optional[List[str]] = None 