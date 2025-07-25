import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from .config import Config
import openai
from openai import OpenAI

@dataclass
class Message:
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    message_type: str = 'text'  # 'text', 'voice', 'system'

@dataclass
class Conversation:
    id: str
    user_id: Optional[str]
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    context: Dict[str, Any]  # Store conversation context like calendar events, user preferences, etc.

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.system_prompt = """You are an AI assistant that helps manage a family calendar through natural conversation. 

Your capabilities include:
- Creating, updating, and checking calendar events
- Answering questions about schedules and appointments
- Providing helpful suggestions and reminders
- Engaging in natural conversation while staying focused on calendar management

Key guidelines:
1. Be conversational and friendly, but professional
2. When users ask about their calendar, provide helpful information
3. If users want to create events, help them with the details
4. Remember context from previous messages in the conversation
5. Ask clarifying questions when needed
6. Provide actionable responses and suggestions

Current date and time context will be provided in each message."""
    
    def create_conversation(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation"""
        import uuid
        conversation_id = str(uuid.uuid4())
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            context={}
        )
        
        # Add system message
        system_message = Message(
            role='system',
            content=self.system_prompt,
            timestamp=datetime.now(),
            message_type='system'
        )
        conversation.messages.append(system_message)
        
        self.conversations[conversation_id] = conversation
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str, message_type: str = 'text') -> bool:
        """Add a message to a conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        return True
    
    def get_conversation_history(self, conversation_id: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for OpenAI API"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        # Get the last N messages (excluding system message)
        recent_messages = conversation.messages[-max_messages:]
        
        # Convert to OpenAI format
        openai_messages = []
        for msg in recent_messages:
            openai_messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        return openai_messages
    
    def add_context(self, conversation_id: str, key: str, value: Any) -> bool:
        """Add context information to a conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.context[key] = value
        conversation.updated_at = datetime.now()
        return True
    
    def get_context(self, conversation_id: str, key: str) -> Optional[Any]:
        """Get context information from a conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        return conversation.context.get(key)
    
    def generate_response(self, conversation_id: str, user_message: str, calendar_context: Optional[Dict] = None) -> str:
        """Generate a conversational response using OpenAI"""
        try:
            print(f"🔍 Generating response for conversation: {conversation_id}")
            print(f"📝 User message: '{user_message}'")
            print(f"📅 Calendar context: {calendar_context}")
            
            # Get conversation history
            messages = self.get_conversation_history(conversation_id)
            print(f"📚 Found {len(messages)} existing messages")
            
            # Add current user message
            messages.append({
                'role': 'user',
                'content': user_message
            })
            
            # Add calendar context if available
            if calendar_context:
                # Convert datetime objects to strings for JSON serialization
                serializable_context = {}
                for key, value in calendar_context.items():
                    if key == 'query_date_range' and value:
                        start_date, end_date = value
                        serializable_context[key] = {
                            'start_date': start_date.isoformat() if start_date else None,
                            'end_date': end_date.isoformat() if end_date else None
                        }
                    elif key == 'events':
                        serializable_context[key] = value  # Already serializable
                    else:
                        serializable_context[key] = value
                
                context_message = f"\n\nCalendar Context: {json.dumps(serializable_context, indent=2)}"
                messages.append({
                    'role': 'system',
                    'content': context_message
                })
                print(f"📅 Added calendar context")
            
            # Add current date/time context with explicit tomorrow/week/month calculation
            from datetime import timedelta
            current_time = datetime.now()
            tomorrow = current_time + timedelta(days=1)

            # Check for month context in calendar_context
            month_context = None
            if calendar_context and 'query_date_range' in calendar_context and calendar_context['query_date_range']:
                qdr = calendar_context['query_date_range']
                # If it's a month (range >= 27 days), set month_context
                if isinstance(qdr, (list, tuple)) and len(qdr) == 2:
                    start, end = qdr
                    if hasattr(start, 'isoformat') and hasattr(end, 'isoformat') and (end - start).days >= 27:
                        month_context = (start, end)

            if month_context:
                # Use month context for system message
                start, end = month_context
                time_context = f"""
Current month: {start.strftime('%B %d, %Y')} to {end.strftime('%B %d, %Y')}
IMPORTANT: All queries refer to this month range.
"""
            else:
                time_context = f"""
Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Today: {current_time.strftime('%A, %B %d, %Y')}
Tomorrow: {tomorrow.strftime('%A, %B %d, %Y')}

IMPORTANT: When the user asks about \"tomorrow\", they are referring to {tomorrow.strftime('%A, %B %d, %Y')}.
"""
            messages.append({
                'role': 'system',
                'content': time_context
            })
            print(f"⏰ Added time context: Today={current_time.strftime('%A, %B %d, %Y')}, Tomorrow={tomorrow.strftime('%A, %B %d, %Y')}")
            
            print(f"🤖 Calling OpenAI API with {len(messages)} messages...")
            
            # Call OpenAI API
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            assistant_response = response.choices[0].message.content.strip()
            print(f"✅ OpenAI response: '{assistant_response}'")
            
            # Add assistant response to conversation
            self.add_message(conversation_id, 'assistant', assistant_response, 'text')
            
            return assistant_response
            
        except Exception as e:
            print(f"❌ Error generating conversational response: {e}")
            import traceback
            print(f"📚 Full traceback:")
            traceback.print_exc()
            return "I'm sorry, I'm having trouble processing your request right now. Please try again."
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def list_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List conversations for a user"""
        conversations = []
        for conv in self.conversations.values():
            if user_id is None or conv.user_id == user_id:
                conversations.append({
                    'id': conv.id,
                    'user_id': conv.user_id,
                    'created_at': conv.created_at.isoformat(),
                    'updated_at': conv.updated_at.isoformat(),
                    'message_count': len(conv.messages)
                })
        return conversations 