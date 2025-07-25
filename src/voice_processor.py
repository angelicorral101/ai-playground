import speech_recognition as sr
import io
import wave
import tempfile
import os
from typing import Optional
import openai  # Updated import for v0.28.1
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from .config import Config
from .models import VoiceInput
from openai import OpenAI

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Remove deprecated openai.api_key assignment
    
    def convert_to_wav(self, audio_data: bytes, input_format: str = "wav") -> bytes:
        """
        Convert audio data to WAV format
        """
        try:
            print(f"🔄 Converting {len(audio_data)} bytes from {input_format} to WAV...")
            
            # If already WAV, return as is
            if input_format.lower() == "wav":
                print("✅ Already WAV format, returning as-is")
                return audio_data
            
            # Create a temporary file for the input audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_format}") as temp_input:
                temp_input.write(audio_data)
                temp_input_path = temp_input.name
                print(f"📁 Created temp file: {temp_input_path}")
            
            # Load audio using pydub
            print(f"🎵 Loading audio with pydub...")
            audio = AudioSegment.from_file(temp_input_path, format=input_format)
            print(f"✅ Audio loaded: {len(audio)}ms duration")
            
            # Export as WAV
            print("🔄 Exporting to WAV...")
            wav_data = io.BytesIO()
            audio.export(wav_data, format="wav")
            wav_bytes = wav_data.getvalue()
            print(f"✅ WAV export complete: {len(wav_bytes)} bytes")
            
            # Clean up temporary file
            os.unlink(temp_input_path)
            print(f"🗑️  Cleaned up temp file: {temp_input_path}")
            
            return wav_bytes
            
        except CouldntDecodeError as e:
            print(f"❌ Error decoding audio format {input_format}: {e}")
            raise ValueError(f"Unsupported audio format: {input_format}")
        except Exception as e:
            print(f"❌ Error converting audio to WAV: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def detect_audio_format(self, audio_data: bytes, filename: str = "") -> str:
        """
        Detect audio format from file extension or data
        """
        print(f"🔍 Detecting audio format: {len(audio_data)} bytes, filename: '{filename}'")
        
        # Try to detect from filename first
        if filename:
            ext = filename.lower().split('.')[-1] if '.' in filename else ""
            print(f"📄 File extension from filename: '{ext}'")
            if ext in ['wav', 'mp3', 'm4a', 'aac', 'ogg', 'flac', 'wma']:
                print(f"✅ Detected format from filename: {ext}")
                return ext
        
        # Try to detect from file signature (magic bytes)
        if len(audio_data) >= 4:
            signature = audio_data[:4]
            print(f"🔍 File signature: {signature.hex()}")
            
            # WAV signature
            if signature == b'RIFF':
                print("✅ Detected WAV from signature")
                return 'wav'
            # MP3 signature
            elif audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
                print("✅ Detected MP3 from signature")
                return 'mp3'
            # M4A signature
            elif signature == b'ftyp':
                print("✅ Detected M4A from signature")
                return 'm4a'
            # OGG signature
            elif signature == b'OggS':
                print("✅ Detected OGG from signature")
                return 'ogg'
            # FLAC signature
            elif signature == b'fLaC':
                print("✅ Detected FLAC from signature")
                return 'flac'
        else:
            print(f"⚠️  File too small for signature detection: {len(audio_data)} bytes")
        
        # Default to WAV if we can't detect
        print("⚠️  Could not detect format, defaulting to WAV")
        return 'wav'
    
    def process_audio_file(self, audio_data: bytes, format: str = "wav") -> Optional[str]:
        """
        Process audio file and convert to text using OpenAI Whisper API
        """
        try:
            print(f"🔍 Processing audio: {len(audio_data)} bytes, format: {format}")
            
            # Check if audio data is empty
            if len(audio_data) == 0:
                print("❌ Error: Empty audio data received")
                return None
            
            # Convert audio to WAV format if needed
            wav_data = self.convert_to_wav(audio_data, format)
            print(f"✅ Converted to WAV: {len(wav_data)} bytes")
            
            # Create a temporary file to store the WAV audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(wav_data)
                temp_file_path = temp_file.name
            
            # Use OpenAI Whisper API for transcription
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            with open(temp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            print(f"🎤 Transcription result: '{transcript}'")
            return str(transcript)
            
        except Exception as e:
            print(f"❌ Error processing audio: {e}")
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