---
name: audio-transcription
description: Transcribe audio and video files to text using Volcengine Doubao ASR Flash API. Use when converting audio recordings, podcasts, meetings, interviews, or videos to text. Supports local files (audio/video), URLs, and auto video-to-audio conversion via FFmpeg.
---

# Audio/Video Transcription - Volcengine Doubao ASR Flash

Transcribe audio and video files to text using the Volcengine large model ASR **Flash API** (synchronous mode).

## Quick Start

```python
import os
from scripts.transcribe import AudioTranscriber

transcriber = AudioTranscriber(
    appid=os.environ["VOLCENGINE_APP_ID"],
    token=os.environ["VOLCENGINE_ACCESS_TOKEN"]
)

# From URL
result = transcriber.transcribe(url="https://example.com/audio.mp3")

# From local audio file
result = transcriber.transcribe(file="./recording.mp3")

# From local video file (auto-converts to audio)
result = transcriber.transcribe(file="./video.mp4")

print(result["result"]["text"])
```

## CLI Usage

```bash
# Set credentials
export VOLCENGINE_APP_ID="your_app_id"
export VOLCENGINE_ACCESS_TOKEN="your_access_token"

# Transcribe from URL
python scripts/transcribe.py --url "https://example.com/audio.mp3"

# Transcribe from local audio file
python scripts/transcribe.py --file "./recording.mp3"

# Transcribe from local video file
python scripts/transcribe.py --file "./video.mp4"

# Text only output
python scripts/transcribe.py --file "./video.mp4" --text-only

# Save to file
python scripts/transcribe.py --file "./video.mp4" -o result.json
```

## Supported Formats

| Type | Formats |
|------|---------|
| **Audio** | mp3, wav, ogg, m4a, flac, aac |
| **Video** | mp4, mkv, avi, mov, wmv, flv, webm, ts, m4v |

## Features

| Feature | Description |
|---------|-------------|
| **Sync Mode** | Single request, immediate response |
| **URL Input** | Public accessible audio URL |
| **Local Audio** | Upload via Base64 encoding |
| **Local Video** | Auto-convert to audio via FFmpeg |
| **Temp Cleanup** | Auto-removes extracted audio files |

## Limits

| Item | Limit |
|------|-------|
| Audio duration | Max 2 hours |
| File size | Max 100MB |
| Upload stream | Recommended < 20MB |

## Requirements

```bash
# Python library
pip install requests

# FFmpeg (required for video files)
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
apt install ffmpeg
```

## Workflow

```
Video File (MP4/MKV/AVI...)
        ↓
  FFmpeg Extract Audio
        ↓
Audio File (MP3/WAV...)  ←  Or direct audio input
        ↓
   ASR API Request
        ↓
   Transcription Text
```

## References

| Topic | File |
|-------|------|
| API Details | [reference/api.md](reference/api.md) |
| Response Format | [reference/response.md](reference/response.md) |
| Examples | [examples/](examples/) |
| Transcribe Script | [scripts/transcribe.py](scripts/transcribe.py) |

## Credentials

Get from [Volcengine Console](https://console.volcengine.com/speech/app):
- `VOLCENGINE_APP_ID`: Application ID
- `VOLCENGINE_ACCESS_TOKEN`: Access Token
