import requests

API_URL = "http://localhost:8000/api/voice"
AUDIO_FILE = "test_audio.m4a"

with open(AUDIO_FILE, "rb") as f:
    files = {"file": (AUDIO_FILE, f, "audio/m4a")}
    print(f"Uploading {AUDIO_FILE} to {API_URL}...")
    response = requests.post(API_URL, files=files)

print("Status code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Raw response:", response.text) 