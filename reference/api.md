# API Reference - Flash (Turbo) Version

## Endpoint

```
POST https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash
```

**Mode**: Synchronous - single request returns result immediately.

## Authentication Headers

| Header | Description | Required |
|--------|-------------|----------|
| `X-Api-App-Key` | Application ID from console | Yes |
| `X-Api-Access-Key` | Access Token from console | Yes |
| `X-Api-Resource-Id` | `volc.bigasr.auc_turbo` | Yes |
| `X-Api-Request-Id` | UUID format request ID | Yes |
| `X-Api-Sequence` | Fixed value: `-1` | Yes |

## Request Body

### Option 1: URL Input

```json
{
  "user": {
    "uid": "user_identifier"
  },
  "audio": {
    "url": "https://example.com/audio.mp3"
  },
  "request": {
    "model_name": "bigmodel"
  }
}
```

### Option 2: Base64 Input (Local File)

```json
{
  "user": {
    "uid": "user_identifier"
  },
  "audio": {
    "data": "BASE64_ENCODED_AUDIO_DATA"
  },
  "request": {
    "model_name": "bigmodel"
  }
}
```

## Request Parameters

### audio object

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Public accessible audio URL (use this OR data) |
| `data` | string | Base64 encoded audio content (use this OR url) |

### request object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model_name` | string | - | Fixed: `bigmodel` (required) |

## Limits

| Item | Limit |
|------|-------|
| Audio duration | Max 2 hours |
| File size | Max 100MB |
| Upload stream | Recommended < 20MB |

## Supported Formats

### Audio (Direct)
mp3, wav, ogg, m4a, flac, aac

### Video (Auto-convert via FFmpeg)
mp4, mkv, avi, mov, wmv, flv, webm, ts, m4v

## Video Processing

Video files are automatically converted to audio using FFmpeg before transcription.

### Conversion Process

```
Video File → FFmpeg → Temp Audio (MP3, 16kHz, Mono) → API → Result
```

### FFmpeg Command Used

```bash
ffmpeg -i video.mp4 -vn -acodec libmp3lame -ar 16000 -ac 1 -y output.mp3
```

### FFmpeg Installation

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux (Debian/Ubuntu)
apt install ffmpeg

# Linux (RHEL/CentOS)
yum install ffmpeg
```

### Video Transcription Example

```python
from scripts.transcribe import AudioTranscriber

transcriber = AudioTranscriber(appid, token)

# Video file is auto-converted to audio
result = transcriber.transcribe(file="./video.mp4")
print(result["result"]["text"])
```

## Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| `20000000` | Success | Process result |
| `20000003` | Silent audio | Check audio content |
| `45000001` | Invalid parameter | Check request format |
| `45000151` | Invalid audio format | Check audio file |
| `55000031` | Server overload | Retry later |

## Code Template

```python
import base64
import json
import os
import uuid
import requests

API_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
RESOURCE_ID = "volc.bigasr.auc_turbo"


def transcribe_url(audio_url: str) -> dict:
    """Transcribe audio from URL"""
    appid = os.environ["VOLCENGINE_APP_ID"]
    token = os.environ["VOLCENGINE_ACCESS_TOKEN"]

    headers = {
        "X-Api-App-Key": appid,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": RESOURCE_ID,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "X-Api-Sequence": "-1"
    }

    body = {
        "user": {"uid": "user"},
        "audio": {"url": audio_url},
        "request": {"model_name": "bigmodel"}
    }

    resp = requests.post(API_URL, json=body, headers=headers)

    if resp.headers.get("X-Api-Status-Code") != "20000000":
        raise Exception(f"API error: {resp.headers.get('X-Api-Status-Code')} - {resp.headers.get('X-Api-Message')}")

    return resp.json()


def transcribe_file(file_path: str) -> dict:
    """Transcribe audio from local file"""
    appid = os.environ["VOLCENGINE_APP_ID"]
    token = os.environ["VOLCENGINE_ACCESS_TOKEN"]

    # Read and encode file
    with open(file_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "X-Api-App-Key": appid,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": RESOURCE_ID,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "X-Api-Sequence": "-1"
    }

    body = {
        "user": {"uid": "user"},
        "audio": {"data": audio_data},
        "request": {"model_name": "bigmodel"}
    }

    resp = requests.post(API_URL, json=body, headers=headers)

    if resp.headers.get("X-Api-Status-Code") != "20000000":
        raise Exception(f"API error: {resp.headers.get('X-Api-Status-Code')} - {resp.headers.get('X-Api-Message')}")

    return resp.json()


# Usage
result = transcribe_url("https://example.com/audio.mp3")
# or
result = transcribe_file("./local_audio.mp3")

print(result["result"]["text"])
```

## Error Handling

```python
try:
    result = transcribe_file("audio.mp3")
except FileNotFoundError:
    print("Audio file not found")
except requests.exceptions.Timeout:
    print("Request timeout - file may be too large")
except requests.exceptions.ConnectionError:
    print("Connection error - check network")
except Exception as e:
    print(f"Transcription failed: {e}")
```

## Differences from Standard Version

| Feature | Standard | Flash (Turbo) |
|---------|----------|---------------|
| Mode | Async (submit + poll) | **Sync (single request)** |
| Endpoint | `/submit` + `/query` | **`/recognize/flash`** |
| Resource ID | `volc.bigasr.auc` | **`volc.bigasr.auc_turbo`** |
| Local file | URL only | **URL + Base64** |
| Emotion detection | Supported | Not supported |
| Gender detection | Supported | Not supported |
| Speaker diarization | Supported | Limited |
