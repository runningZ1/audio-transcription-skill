# Audio Transcription Skill

English | [简体中文](README.md)

A Claude Code Skill for transcribing audio and video files to text using Volcengine Doubao ASR Flash API.

## Features

- **Multi-format Support** - Audio (MP3, WAV, OGG, M4A, FLAC, AAC) and Video (MP4, MKV, AVI, MOV, WMV, FLV, WebM)
- **Flexible Input** - Support URL and local file upload
- **Auto Video Conversion** - Automatically extract audio from video files via FFmpeg
- **Synchronous Mode** - Fast single-request transcription using Flash API
- **Word-level Timestamps** - Get precise timing for each word
- **CLI & Python API** - Use via command line or import as module

## Requirements

- Python 3.7+
- [requests](https://pypi.org/project/requests/) library
- [FFmpeg](https://ffmpeg.org/) (required for video files)
- Volcengine Account with ASR service enabled

### Install Dependencies

```bash
# Python library
pip install requests

# FFmpeg (for video processing)
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux (Debian/Ubuntu)
apt install ffmpeg
```

## Configuration

### Get API Credentials

1. Visit [Volcengine Console](https://console.volcengine.com/speech/app)
2. Create an application or use existing one
3. Get your **App ID** and **Access Token**

### Set Environment Variables

```bash
# Linux/macOS
export VOLCENGINE_APP_ID="your_app_id"
export VOLCENGINE_ACCESS_TOKEN="your_access_token"

# Windows PowerShell
$env:VOLCENGINE_APP_ID="your_app_id"
$env:VOLCENGINE_ACCESS_TOKEN="your_access_token"

# Windows CMD
set VOLCENGINE_APP_ID=your_app_id
set VOLCENGINE_ACCESS_TOKEN=your_access_token
```

Or copy the example file and edit:

```bash
cp scripts/.env.example .env
# Edit .env with your credentials
```

## Usage

### Command Line

```bash
# Transcribe from URL
python scripts/transcribe.py --url "https://example.com/audio.mp3"

# Transcribe local audio file
python scripts/transcribe.py --file "./recording.mp3"

# Transcribe local video file
python scripts/transcribe.py --file "./video.mp4"

# Output text only
python scripts/transcribe.py --file "./audio.mp3" --text-only

# Save to file
python scripts/transcribe.py --file "./video.mp4" -o result.json

# With explicit credentials
python scripts/transcribe.py --file "./audio.mp3" --appid YOUR_ID --token YOUR_TOKEN
```

### Python API

```python
import os
from scripts.transcribe import AudioTranscriber, get_text, get_duration

# Initialize
transcriber = AudioTranscriber(
    appid=os.environ["VOLCENGINE_APP_ID"],
    token=os.environ["VOLCENGINE_ACCESS_TOKEN"]
)

# Transcribe from URL
result = transcriber.transcribe(url="https://example.com/audio.mp3")

# Transcribe local audio file
result = transcriber.transcribe(file="./recording.mp3")

# Transcribe local video file (auto-converts to audio)
result = transcriber.transcribe(file="./video.mp4")

# Get results
print(get_text(result))  # Full text
print(f"Duration: {get_duration(result):.1f}s")
```

## Supported Formats

| Type | Formats |
|------|---------|
| Audio | mp3, wav, ogg, m4a, flac, aac |
| Video | mp4, mkv, avi, mov, wmv, flv, webm, ts, m4v |

## Limits

| Item | Limit |
|------|-------|
| Audio duration | Max 2 hours |
| File size | Max 100MB |
| Recommended upload | < 20MB |

## Response Format

```json
{
  "audio_info": {
    "duration": 5230
  },
  "result": {
    "text": "Full transcription text here.",
    "utterances": [
      {
        "text": "Sentence one.",
        "start_time": 0,
        "end_time": 1500,
        "words": [
          {
            "text": "Sentence",
            "start_time": 0,
            "end_time": 800,
            "confidence": 0.98
          }
        ]
      }
    ]
  }
}
```

## Project Structure

```
audio-transcription-skill/
├── SKILL.md              # Claude Code Skill definition
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── reference/
│   ├── api.md            # API documentation
│   └── response.md       # Response format documentation
├── scripts/
│   ├── transcribe.py     # Main transcription script
│   └── .env.example      # Environment variables template
└── examples/
    ├── basic.md          # Basic usage examples
    └── advanced.md       # Advanced usage examples
```

## Error Handling

```python
from scripts.transcribe import (
    AudioTranscriber,
    TranscriptionError,
    FFmpegNotFoundError
)

try:
    result = transcriber.transcribe(file="./video.mp4")
except FileNotFoundError:
    print("File not found")
except FFmpegNotFoundError:
    print("FFmpeg not installed - required for video files")
except TranscriptionError as e:
    print(f"API error [{e.code}]: {e.message}")
```

## API Reference

See [reference/api.md](reference/api.md) for detailed API documentation.

## License

MIT License

## Acknowledgments

- [Volcengine Doubao ASR](https://www.volcengine.com/docs/6561/1631584) - Speech recognition API
- [FFmpeg](https://ffmpeg.org/) - Audio/video processing
