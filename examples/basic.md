# Basic Examples - Flash API

## CLI Usage

### From URL

```bash
# Basic transcription from URL
python scripts/transcribe.py --url "https://example.com/audio.mp3"

# With text-only output
python scripts/transcribe.py --url "https://example.com/audio.mp3" --text-only

# Save to file
python scripts/transcribe.py --url "https://example.com/audio.mp3" -o transcript.json
```

### From Local Audio File

```bash
# Transcribe local audio file
python scripts/transcribe.py --file "./recording.mp3"

# With text-only output
python scripts/transcribe.py --file "./meeting.wav" --text-only

# Save result to file
python scripts/transcribe.py --file "./audio.mp3" -o result.json
```

### From Local Video File

```bash
# Transcribe video file (requires FFmpeg)
python scripts/transcribe.py --file "./video.mp4"

# Various video formats
python scripts/transcribe.py --file "./movie.mkv"
python scripts/transcribe.py --file "./clip.avi"
python scripts/transcribe.py --file "./recording.mov"

# Keep temporary audio file
python scripts/transcribe.py --file "./video.mp4" --keep-temp

# With explicit credentials
python scripts/transcribe.py \
  --file "./video.mp4" \
  --appid "YOUR_APP_ID" \
  --token "YOUR_ACCESS_TOKEN"
```

## Python Usage

### Basic Transcription

```python
import os
from scripts.transcribe import AudioTranscriber, get_text, get_duration

# Initialize
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

# Get text
print(get_text(result))

# Get duration
print(f"Duration: {get_duration(result):.1f} seconds")
```

### With Error Handling

```python
from scripts.transcribe import (
    AudioTranscriber,
    TranscriptionError,
    FFmpegNotFoundError
)

transcriber = AudioTranscriber(appid, token)

try:
    result = transcriber.transcribe(file="./video.mp4")
    print(result["result"]["text"])
except FileNotFoundError:
    print("File not found")
except FFmpegNotFoundError:
    print("FFmpeg not installed - required for video files")
except TranscriptionError as e:
    print(f"API error [{e.code}]: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Supported Formats

### Audio (Direct)
- mp3, wav, ogg, m4a, flac, aac

### Video (Auto-convert)
- mp4, mkv, avi, mov, wmv, flv, webm, ts, m4v

## Expected Output

### JSON Output (default)

```json
{
  "audio_info": {
    "duration": 5230
  },
  "result": {
    "text": "Hello everyone. Welcome to today's meeting.",
    "utterances": [
      {
        "text": "Hello everyone.",
        "start_time": 0,
        "end_time": 1500,
        "words": [
          {"text": "Hello", "start_time": 0, "end_time": 600, "confidence": 0.98},
          {"text": "everyone", "start_time": 650, "end_time": 1500, "confidence": 0.99}
        ]
      }
    ]
  }
}
```

### Text Only Output

```
Hello everyone. Welcome to today's meeting.
```

## Environment Setup

```bash
# Set credentials (Linux/macOS)
export VOLCENGINE_APP_ID="your_app_id"
export VOLCENGINE_ACCESS_TOKEN="your_access_token"

# Set credentials (Windows PowerShell)
$env:VOLCENGINE_APP_ID="your_app_id"
$env:VOLCENGINE_ACCESS_TOKEN="your_access_token"

# Set credentials (Windows CMD)
set VOLCENGINE_APP_ID=your_app_id
set VOLCENGINE_ACCESS_TOKEN=your_access_token
```

## FFmpeg Installation

Required for video file processing:

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux (Debian/Ubuntu)
apt install ffmpeg
```
