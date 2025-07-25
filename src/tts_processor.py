import io
import tempfile
import os
from typing import Optional, Tuple
from .config import Config
import openai
from openai import OpenAI

class TTSProcessor:
    def __init__(self):
        self.default_voice = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
        self.default_model = "tts-1"  # Options: tts-1, tts-1-hd
    
    def text_to_speech(self, text: str, voice: str = None, model: str = None) -> Optional[bytes]:
        """
        Convert text to speech using OpenAI TTS API
        Returns audio data as bytes
        """
        try:
            if not text.strip():
                print("❌ TTS Error: Empty text provided")
                return None
            
            voice = voice or self.default_voice
            model = model or self.default_model
            
            print(f"🎤 Converting text to speech: {len(text)} characters")
            print(f"🔊 Voice: {voice}, Model: {model}")
            
            # Call OpenAI TTS API
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            
            # Get audio data
            audio_data = response.content
            print(f"✅ TTS conversion successful: {len(audio_data)} bytes")
            
            return audio_data
            
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return None
    
    def text_to_speech_file(self, text: str, output_path: str, voice: str = None, model: str = None) -> bool:
        """
        Convert text to speech and save to file
        """
        try:
            audio_data = self.text_to_speech(text, voice, model)
            if audio_data is None:
                return False
            
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            print(f"✅ TTS file saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ TTS file save error: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices"""
        return [
            {"id": "alloy", "name": "Alloy", "description": "Balanced, clear voice"},
            {"id": "echo", "name": "Echo", "description": "Warm, friendly voice"},
            {"id": "fable", "name": "Fable", "description": "Narrative, storytelling voice"},
            {"id": "onyx", "name": "Onyx", "description": "Deep, authoritative voice"},
            {"id": "nova", "name": "Nova", "description": "Bright, energetic voice"},
            {"id": "shimmer", "name": "Shimmer", "description": "Soft, gentle voice"}
        ]
    
    def get_available_models(self) -> list:
        """Get list of available TTS models"""
        return [
            {"id": "tts-1", "name": "TTS-1", "description": "Standard quality, faster"},
            {"id": "tts-1-hd", "name": "TTS-1-HD", "description": "High definition, slower"}
        ]
    
    def validate_voice(self, voice: str) -> bool:
        """Validate if a voice is supported"""
        available_voices = [v["id"] for v in self.get_available_voices()]
        return voice in available_voices
    
    def validate_model(self, model: str) -> bool:
        """Validate if a model is supported"""
        available_models = [m["id"] for m in self.get_available_models()]
        return model in available_models 