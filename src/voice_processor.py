import speech_recognition as sr
import io
import wave
import tempfile
import os
from typing import Optional
import openai
from .config import Config
from .models import VoiceInput

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Remove deprecated openai.api_key assignment
    
    def process_audio_file(self, audio_data: bytes, format: str = "wav") -> Optional[str]:
        """
        Process audio file and convert to text using OpenAI Whisper API
        """
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Use OpenAI Whisper API for transcription
            openai.api_key = Config.OPENAI_API_KEY
            with open(temp_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return str(transcript)
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return None
    
    def record_from_microphone(self, duration: int = 5) -> Optional[str]:
        """
        Record audio from microphone and convert to text
        """
        try:
            with sr.Microphone() as source:
                print("Listening... Speak now!")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                
                # Convert to text using OpenAI Whisper
                audio_data = audio.get_wav_data()
                return self.process_audio_file(audio_data, "wav")
                
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period")
            return None
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None
    
    def process_voice_input(self, voice_input: VoiceInput) -> Optional[str]:
        """
        Process voice input and return transcribed text
        """
        return self.process_audio_file(voice_input.audio_data, voice_input.format) 