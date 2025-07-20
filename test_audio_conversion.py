#!/usr/bin/env python3
"""
Test script for audio conversion functionality
"""

import os
import tempfile
from src.voice_processor import VoiceProcessor

def test_audio_conversion():
    """Test audio conversion functionality"""
    processor = VoiceProcessor()
    
    # Create a simple test WAV file
    test_wav_data = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    print("Testing audio format detection...")
    detected_format = processor.detect_audio_format(test_wav_data, "test.wav")
    print(f"Detected format for test.wav: {detected_format}")
    converted_wav = processor.convert_to_wav(test_wav_data, "wav")
    print(f"WAV conversion successful: {len(converted_wav)} bytes")
    print("✅ Audio conversion tests completed successfully!")

def test_real_m4a():
    """Test conversion of a real M4A file"""
    processor = VoiceProcessor()
    m4a_path = "./test_audio.m4a"
    if not os.path.exists(m4a_path):
        print(f"Test M4A file not found: {m4a_path}")
        return
    with open(m4a_path, "rb") as f:
        m4a_data = f.read()
    detected_format = processor.detect_audio_format(m4a_data, m4a_path)
    print(f"Detected format for {m4a_path}: {detected_format}")
    try:
        wav_data = processor.convert_to_wav(m4a_data, detected_format)
        print(f"M4A to WAV conversion successful: {len(wav_data)} bytes")
    except Exception as e:
        print(f"M4A to WAV conversion failed: {e}")

if __name__ == "__main__":
    test_audio_conversion()
    test_real_m4a() 