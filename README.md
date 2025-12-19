# 音频转录 Skill

[English](README_EN.md) | 简体中文

基于火山引擎豆包语音识别 Flash API 的 Claude Code Skill，支持将音频和视频文件转录为文字。

## 功能特性

- **多格式支持** - 音频（MP3、WAV、OGG、M4A、FLAC、AAC）和视频（MP4、MKV、AVI、MOV、WMV、FLV、WebM）
- **灵活输入** - 支持 URL 链接和本地文件上传
- **视频自动转换** - 通过 FFmpeg 自动从视频中提取音轨
- **同步模式** - 使用 Flash API 快速单次请求转录
- **词级时间戳** - 获取每个词的精确时间信息
- **命令行与 Python API** - 支持命令行使用或作为模块导入

## 环境要求

- Python 3.7+
- [requests](https://pypi.org/project/requests/) 库
- [FFmpeg](https://ffmpeg.org/)（处理视频文件时需要）
- 火山引擎账号并开通语音识别服务

### 安装依赖

```bash
# Python 库
pip install requests

# FFmpeg（用于视频处理）
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux (Debian/Ubuntu)
apt install ffmpeg
```

## 配置

### 获取 API 凭证

1. 访问 [火山引擎控制台](https://console.volcengine.com/speech/app)
2. 创建应用或使用已有应用
3. 获取 **App ID** 和 **Access Token**

### 设置环境变量

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

或者复制示例文件并编辑：

```bash
cp scripts/.env.example .env
# 编辑 .env 填入真实凭证
```

## 使用方法

### 命令行

```bash
# 从 URL 转录
python scripts/transcribe.py --url "https://example.com/audio.mp3"

# 转录本地音频文件
python scripts/transcribe.py --file "./recording.mp3"

# 转录本地视频文件
python scripts/transcribe.py --file "./video.mp4"

# 仅输出文字
python scripts/transcribe.py --file "./audio.mp3" --text-only

# 保存到文件
python scripts/transcribe.py --file "./video.mp4" -o result.json

# 指定凭证
python scripts/transcribe.py --file "./audio.mp3" --appid YOUR_ID --token YOUR_TOKEN
```

### Python API

```python
import os
from scripts.transcribe import AudioTranscriber, get_text, get_duration

# 初始化
transcriber = AudioTranscriber(
    appid=os.environ["VOLCENGINE_APP_ID"],
    token=os.environ["VOLCENGINE_ACCESS_TOKEN"]
)

# 从 URL 转录
result = transcriber.transcribe(url="https://example.com/audio.mp3")

# 转录本地音频文件
result = transcriber.transcribe(file="./recording.mp3")

# 转录本地视频文件（自动转换为音频）
result = transcriber.transcribe(file="./video.mp4")

# 获取结果
print(get_text(result))  # 完整文字
print(f"时长: {get_duration(result):.1f}秒")
```

## 支持的格式

| 类型 | 格式 |
|------|------|
| 音频 | mp3, wav, ogg, m4a, flac, aac |
| 视频 | mp4, mkv, avi, mov, wmv, flv, webm, ts, m4v |

## 限制

| 项目 | 限制 |
|------|------|
| 音频时长 | 最长 2 小时 |
| 文件大小 | 最大 100MB |
| 建议上传大小 | < 20MB |

## 响应格式

```json
{
  "audio_info": {
    "duration": 5230
  },
  "result": {
    "text": "完整的转录文字在这里。",
    "utterances": [
      {
        "text": "第一句话。",
        "start_time": 0,
        "end_time": 1500,
        "words": [
          {
            "text": "第一",
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

## 项目结构

```
audio-transcription-skill/
├── SKILL.md              # Claude Code Skill 定义
├── README.md             # 中文文档（本文件）
├── README_EN.md          # 英文文档
├── .gitignore            # Git 忽略规则
├── reference/
│   ├── api.md            # API 文档
│   └── response.md       # 响应格式文档
├── scripts/
│   ├── transcribe.py     # 主转录脚本
│   └── .env.example      # 环境变量模板
└── examples/
    ├── basic.md          # 基础使用示例
    └── advanced.md       # 高级使用示例
```

## 错误处理

```python
from scripts.transcribe import (
    AudioTranscriber,
    TranscriptionError,
    FFmpegNotFoundError
)

try:
    result = transcriber.transcribe(file="./video.mp4")
except FileNotFoundError:
    print("文件未找到")
except FFmpegNotFoundError:
    print("FFmpeg 未安装 - 处理视频文件时需要")
except TranscriptionError as e:
    print(f"API 错误 [{e.code}]: {e.message}")
```

## API 参考

详细 API 文档请参阅 [reference/api.md](reference/api.md)。

## 许可证

MIT License

## 致谢

- [火山引擎豆包语音识别](https://www.volcengine.com/docs/6561/1631584) - 语音识别 API
- [FFmpeg](https://ffmpeg.org/) - 音视频处理
