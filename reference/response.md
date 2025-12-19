# Response Format - Flash Version

## Success Response Structure

```json
{
  "audio_info": {
    "duration": 125000
  },
  "result": {
    "text": "Full transcription text here.",
    "utterances": [
      {
        "text": "Sentence one.",
        "start_time": 0,
        "end_time": 2500,
        "words": [
          {
            "text": "Sentence",
            "start_time": 0,
            "end_time": 800,
            "confidence": 0.98
          },
          {
            "text": "one",
            "start_time": 850,
            "end_time": 1200,
            "confidence": 0.99
          }
        ]
      }
    ]
  }
}
```

## Response Fields

### Top Level

| Field | Type | Description |
|-------|------|-------------|
| `audio_info` | object | Audio metadata |
| `result` | object | Recognition result |

### audio_info object

| Field | Type | Description |
|-------|------|-------------|
| `duration` | int | Total duration in milliseconds |

### result object

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Complete transcription text |
| `utterances` | array | Sentence-level segments |

### utterance object

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Sentence text |
| `start_time` | int | Start time in milliseconds |
| `end_time` | int | End time in milliseconds |
| `words` | array | Word-level details |

### word object

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Word text |
| `start_time` | int | Start time in milliseconds |
| `end_time` | int | End time in milliseconds |
| `confidence` | float | Recognition confidence (0-1) |

## Response Headers

| Header | Description |
|--------|-------------|
| `X-Api-Status-Code` | Status code |
| `X-Api-Message` | Status message |
| `X-Tt-Logid` | Request log ID for debugging |

## Extracting Data

### Get plain text

```python
text = result["result"]["text"]
```

### Get duration

```python
duration_ms = result["audio_info"]["duration"]
duration_sec = duration_ms / 1000
print(f"Audio duration: {duration_sec:.1f} seconds")
```

### Get utterances with timestamps

```python
for utt in result["result"]["utterances"]:
    start_sec = utt["start_time"] / 1000
    end_sec = utt["end_time"] / 1000
    print(f"[{start_sec:.1f}s - {end_sec:.1f}s] {utt['text']}")
```

### Get word-level timing

```python
for utt in result["result"]["utterances"]:
    for word in utt.get("words", []):
        confidence = word.get("confidence", 0)
        print(f"{word['text']}: {word['start_time']}ms - {word['end_time']}ms (conf: {confidence:.2f})")
```

### Convert to SRT format

```python
def to_srt(result):
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

    return "\n".join(lines)

# Usage
srt_content = to_srt(result)
with open("output.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)
```

### Calculate average confidence

```python
def get_avg_confidence(result):
    confidences = []
    for utt in result["result"]["utterances"]:
        for word in utt.get("words", []):
            if "confidence" in word:
                confidences.append(word["confidence"])

    if confidences:
        return sum(confidences) / len(confidences)
    return None

avg_conf = get_avg_confidence(result)
print(f"Average confidence: {avg_conf:.2%}")
```
