#!/usr/bin/env python3
"""
Test script for conversational voice functionality
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_conversational_voice():
    """Test the conversational voice functionality"""
    print("🎤 Testing Conversational Voice API")
    print("=" * 50)
    
    # 1. Start a new conversation
    print("1. Starting new conversation...")
    response = requests.post(f"{API_BASE}/api/conversation/start")
    if response.status_code == 200:
        data = response.json()
        conversation_id = data['conversation_id']
        print(f"✅ Conversation started: {conversation_id}")
    else:
        print(f"❌ Failed to start conversation: {response.text}")
        return
    
    # 2. Test text-based conversation
    print("\n2. Testing text-based conversation...")
    test_messages = [
        "Hello! How are you today?",
        "What's on my calendar tomorrow?",
        "Can you help me schedule a meeting?",
        "Thank you for your help!"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Message {i}: '{message}'")
        
        response = requests.post(
            f"{API_BASE}/api/conversation/text",
            data={
                'conversation_id': conversation_id,
                'message': message,
                'voice': 'alloy',
                'model': 'tts-1'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ AI Response: '{data['message']}'")
            if data.get('audio_response'):
                print(f"   🎤 Audio response: {len(data['audio_response'])} bytes")
            else:
                print("   ⚠️  No audio response")
        else:
            print(f"   ❌ Error: {response.text}")
    
    # 3. Get conversation history
    print("\n3. Getting conversation history...")
    response = requests.get(f"{API_BASE}/api/conversation/{conversation_id}/history")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Conversation history: {len(data['history'])} messages")
        for msg in data['history']:
            print(f"   {msg['role']}: {msg['content'][:50]}...")
    else:
        print(f"❌ Failed to get history: {response.text}")
    
    # 4. Test TTS voices
    print("\n4. Testing available TTS voices...")
    response = requests.get(f"{API_BASE}/api/tts/voices")
    if response.status_code == 200:
        data = response.json()
        print("✅ Available voices:")
        for voice in data['voices']:
            print(f"   - {voice['name']} ({voice['id']}): {voice['description']}")
    else:
        print(f"❌ Failed to get voices: {response.text}")
    
    # 5. Test TTS models
    print("\n5. Testing available TTS models...")
    response = requests.get(f"{API_BASE}/api/tts/models")
    if response.status_code == 200:
        data = response.json()
        print("✅ Available models:")
        for model in data['models']:
            print(f"   - {model['name']} ({model['id']}): {model['description']}")
    else:
        print(f"❌ Failed to get models: {response.text}")
    
    # 6. List conversations
    print("\n6. Listing conversations...")
    response = requests.get(f"{API_BASE}/api/conversations")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {len(data['conversations'])} conversations")
        for conv in data['conversations']:
            print(f"   - {conv['id']}: {conv['message_count']} messages")
    else:
        print(f"❌ Failed to list conversations: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎤 Conversational Voice Test Completed!")
    print("=" * 50)

def test_voice_file_upload():
    """Test voice file upload for conversational voice"""
    print("\n🎤 Testing Voice File Upload for Conversation")
    print("=" * 50)
    
    # Start conversation
    response = requests.post(f"{API_BASE}/api/conversation/start")
    if response.status_code != 200:
        print("❌ Failed to start conversation")
        return
    
    conversation_id = response.json()['conversation_id']
    print(f"✅ Conversation started: {conversation_id}")
    
    # Test with the existing audio file
    try:
        with open("test_audio.m4a", "rb") as f:
            audio_data = f.read()
        
        print(f"📁 Uploading audio file: {len(audio_data)} bytes")
        
        headers = {
            'X-Conversation-ID': conversation_id,
            'X-Filename': 'test_audio.m4a',
            'X-Voice': 'alloy',
            'X-Model': 'tts-1'
        }
        
        response = requests.post(
            f"{API_BASE}/api/conversation/voice",
            headers=headers,
            data=audio_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Voice processed successfully!")
            print(f"📝 AI Response: '{data['message']}'")
            if data.get('audio_response'):
                print(f"🎤 Audio response: {len(data['audio_response'])} bytes")
            else:
                print("⚠️  No audio response")
        else:
            print(f"❌ Voice processing failed: {response.text}")
            
    except FileNotFoundError:
        print("⚠️  test_audio.m4a not found, skipping voice file test")
    except Exception as e:
        print(f"❌ Error testing voice file: {e}")

if __name__ == "__main__":
    test_conversational_voice()
    test_voice_file_upload() 