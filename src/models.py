from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from dataclasses import dataclass
from sqlalchemy import create_engine, Column, String, Boolean, Date, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class ChoreDB(Base):
    __tablename__ = 'chores'
    id = Column(String, primary_key=True)
    description = Column(String, nullable=False)
    assigned_to = Column(String, default="")
    completed = Column(Boolean, default=False)
    date = Column(String, nullable=False)  # Store as YYYY-MM-DD

class UserDB(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('email', name='uq_user_email'),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# SQLite setup
engine = create_engine('sqlite:///chores.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

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
    id: Optional[str] = None  # Google Calendar event ID
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
    audio_response: Optional[bytes] = None  # Audio data for voice responses
    queried_date: Optional[Any] = None  # ISO string or list of ISO strings for UI rendering
    queried_view: Optional[str] = None  # e.g. 'week', 'day', etc. for UI rendering 

class ChoresAction(str, Enum):
    QUERY = "query"
    ASSIGN = "assign"
    COMPLETE = "complete"
    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"

@dataclass
class ChoresCommand:
    action: ChoresAction
    chore_description: str = ""
    assignee: str = ""
    raw_input: str = ""

@dataclass
class Chore:
    id: str
    description: str
    assigned_to: str = ""
    completed: bool = False
    date: str = ""  # YYYY-MM-DD 