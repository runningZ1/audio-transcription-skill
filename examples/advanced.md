# Advanced Examples - Flash API

## Video Transcription

### Basic Video Transcription

```python
from scripts.transcribe import AudioTranscriber

transcriber = AudioTranscriber(appid, token)

# Auto-detects video and extracts audio
result = transcriber.transcribe(file="./video.mp4")
print(result["result"]["text"])
```

### Batch Video Processing

```python
from pathlib import Path
from scripts.transcribe import AudioTranscriber, FFmpegNotFoundError

def batch_transcribe_videos(input_dir, output_dir, appid, token):
    """Transcribe all videos in a directory"""
    transcriber = AudioTranscriber(appid, token)
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
    results = []

    for file in input_path.iterdir():
        if file.suffix.lower() not in video_extensions:
            continue

        print(f"Processing: {file.name}")
        try:
            result = transcriber.transcribe(file=str(file))
            text = result.get("result", {}).get("text", "")

            # Save transcript
            output_file = output_path / f"{file.stem}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

            results.append({"file": file.name, "status": "success"})
        except Exception as e:
            results.append({"file": file.name, "status": "error", "error": str(e)})

    return results

# Usage
results = batch_transcribe_videos("./videos", "./transcripts", appid, token)
```

### Video with Subtitles Export

```python
from scripts.transcribe import AudioTranscriber

def video_to_srt(video_path, output_srt):
    """Transcribe video and generate SRT subtitles"""
    transcriber = AudioTranscriber(appid, token)
    result = transcriber.transcribe(file=video_path)

    def format_time(ms):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, utt in enumerate(result["result"]["utterances"], 1):
        start = format_time(utt["start_time"])
        end = format_time(utt["end_time"])
        lines.extend([str(i), f"{start} --> {end}", utt["text"], ""])

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"SRT saved: {output_srt}")

# Usage
video_to_srt("./movie.mp4", "./movie.srt")
```

## Generate SRT Subtitles

```python
from scripts.transcribe import AudioTranscriber

def generate_srt(result, output_path):
    """Convert transcription to SRT subtitle format"""
    def format_time(ms):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    utterances = result.get("result", {}).get("utterances", [])

    for i, utt in enumerate(utterances, 1):
        start = format_time(utt["start_time"])
        end = format_time(utt["end_time"])
        lines.extend([str(i), f"{start} --> {end}", utt["text"], ""])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"SRT saved to: {output_path}")

# Usage
transcriber = AudioTranscriber(appid, token)
result = transcriber.transcribe(file="./video.mp3")
generate_srt(result, "subtitles.srt")
```

## Batch Processing Multiple Files

```python
import os
from pathlib import Path
from scripts.transcribe import AudioTranscriber, TranscriptionError

def batch_transcribe(input_dir, output_dir, appid, token):
    """Transcribe all audio files in a directory"""
    transcriber = AudioTranscriber(appid, token)
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    audio_extensions = {".mp3", ".wav", ".ogg", ".m4a"}
    results = []

    for file in input_path.iterdir():
        if file.suffix.lower() not in audio_extensions:
            continue

        print(f"Processing: {file.name}")
        try:
            result = transcriber.transcribe(file=str(file))
            text = result.get("result", {}).get("text", "")

            # Save transcript
            output_file = output_path / f"{file.stem}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

            results.append({"file": file.name, "status": "success", "chars": len(text)})
        except TranscriptionError as e:
            results.append({"file": file.name, "status": "error", "error": str(e)})
        except Exception as e:
            results.append({"file": file.name, "status": "error", "error": str(e)})

    return results

# Usage
results = batch_transcribe(
    input_dir="./recordings",
    output_dir="./transcripts",
    appid=os.environ["VOLCENGINE_APP_ID"],
    token=os.environ["VOLCENGINE_ACCESS_TOKEN"]
)

for r in results:
    print(f"{r['file']}: {r['status']}")
```

## Generate Meeting Minutes

```python
from scripts.transcribe import AudioTranscriber, get_text, get_duration

def generate_minutes(result, title="Meeting"):
    """Generate meeting minutes from transcription"""
    text = get_text(result)
    duration = get_duration(result)
    utterances = result.get("result", {}).get("utterances", [])

    minutes = f"""# {title}

**Duration**: {duration / 60:.1f} minutes
**Sentences**: {len(utterances)}

## Full Transcript

{text}

## Timeline

"""
    for utt in utterances:
        start_sec = utt["start_time"] / 1000
        minutes += f"- [{start_sec:.1f}s] {utt['text']}\n"

    return minutes

# Usage
transcriber = AudioTranscriber(appid, token)
result = transcriber.transcribe(file="./meeting.mp3")
minutes = generate_minutes(result, title="Team Sync - Dec 19")

with open("minutes.md", "w", encoding="utf-8") as f:
    f.write(minutes)
```

## Confidence Analysis

```python
def analyze_confidence(result):
    """Analyze word-level confidence scores"""
    low_confidence_words = []
    all_confidences = []

    for utt in result.get("result", {}).get("utterances", []):
        for word in utt.get("words", []):
            conf = word.get("confidence", 1.0)
            all_confidences.append(conf)

            if conf < 0.8:
                low_confidence_words.append({
                    "word": word["text"],
                    "confidence": conf,
                    "time": word["start_time"] / 1000
                })

    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

    return {
        "average_confidence": avg_confidence,
        "total_words": len(all_confidences),
        "low_confidence_count": len(low_confidence_words),
        "low_confidence_words": low_confidence_words
    }

# Usage
result = transcriber.transcribe(file="./audio.mp3")
analysis = analyze_confidence(result)

print(f"Average confidence: {analysis['average_confidence']:.2%}")
print(f"Low confidence words: {analysis['low_confidence_count']}")

for w in analysis["low_confidence_words"]:
    print(f"  [{w['time']:.1f}s] '{w['word']}' ({w['confidence']:.2%})")
```

## Large File Handling

```python
import os
from scripts.transcribe import AudioTranscriber

def transcribe_large_file(file_path, appid, token):
    """Handle large files with extended timeout"""
    file_size_mb = os.path.getsize(file_path) / 1024 / 1024

    # Estimate timeout: ~30s per MB + base 60s
    timeout = 60 + (file_size_mb * 30)
    timeout = min(timeout, 600)  # Cap at 10 minutes

    print(f"File size: {file_size_mb:.1f}MB")
    print(f"Timeout: {timeout:.0f}s")

    transcriber = AudioTranscriber(appid, token)
    return transcriber.transcribe(file=file_path, timeout=timeout)

# Usage
result = transcribe_large_file(
    "./large_recording.mp3",
    appid=os.environ["VOLCENGINE_APP_ID"],
    token=os.environ["VOLCENGINE_ACCESS_TOKEN"]
)
```

## Export to Multiple Formats

```python
import json
from scripts.transcribe import AudioTranscriber, get_text

def export_all_formats(result, base_name):
    """Export transcription to multiple formats"""
    text = get_text(result)
    utterances = result.get("result", {}).get("utterances", [])

    # Plain text
    with open(f"{base_name}.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # JSON (full result)
    with open(f"{base_name}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # SRT subtitles
    def format_time(ms):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    srt_lines = []
    for i, utt in enumerate(utterances, 1):
        srt_lines.extend([
            str(i),
            f"{format_time(utt['start_time'])} --> {format_time(utt['end_time'])}",
            utt["text"],
            ""
        ])

    with open(f"{base_name}.srt", "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"Exported: {base_name}.txt, {base_name}.json, {base_name}.srt")

# Usage
transcriber = AudioTranscriber(appid, token)
result = transcriber.transcribe(file="./audio.mp3")
export_all_formats(result, "output")
```
