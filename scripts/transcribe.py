#!/usr/bin/env python3
"""
Volcengine Doubao ASR Flash - Audio/Video Transcription Tool

Transcribe audio/video files using the Flash (Turbo) API with synchronous processing.
Supports URL, local audio files, and video files (auto-converts to audio).

Usage:
    # From URL
    python transcribe.py --url "https://example.com/audio.mp3"

    # From local audio file
    python transcribe.py --file "./recording.mp3"

    # From local video file (auto-converts to audio)
    python transcribe.py --file "./video.mp4"

Environment variables:
    VOLCENGINE_APP_ID: Application ID from Volcengine Console
    VOLCENGINE_ACCESS_TOKEN: Access Token from Volcengine Console

Requirements:
    - requests: pip install requests
    - python-dotenv (optional): pip install python-dotenv
    - FFmpeg: Required for video file processing (https://ffmpeg.org)

Configuration:
    Create a .env file with your credentials (recommended):
        VOLCENGINE_APP_ID=your_app_id
        VOLCENGINE_ACCESS_TOKEN=your_access_token

    Place .env in one of these locations:
        - Script directory (audio-transcription-skill/.env)
        - User config directory (~/.volc-asr/.env)
        - Current working directory (.env)
"""

import argparse
import base64
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Tuple, Union

try:
    import requests
    import urllib3
    # Disable SSL warnings for proxy environments
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API Configuration
API_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
RESOURCE_ID = "volc.bigasr.auc_turbo"

# Limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
RECOMMENDED_SIZE = 20 * 1024 * 1024  # 20MB

# Status codes
STATUS_SUCCESS = "20000000"
STATUS_SILENT = "20000003"

# Supported formats
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".ts", ".m4v"}

# .env file names
DOTENV_FILES = [".env", ".env.local"]


def load_env_files():
    """
    Load .env files from multiple locations with priority.
    Files loaded later override values from earlier files.

    Search order (first to last):
        1. Script directory
        2. User home directory (~/.volc-asr/.env)
        3. Current working directory
        4. Parent directories (up to root)
    """
    if not DOTENV_AVAILABLE:
        return

    # Paths to search for .env files
    search_paths = []

    # 1. Script directory
    script_dir = Path(__file__).parent.parent
    search_paths.append(script_dir)

    # 2. User config directory
    user_config_dir = Path.home() / ".volc-asr"
    search_paths.append(user_config_dir)

    # 3. Current working directory and parents
    cwd = Path.cwd()
    search_paths.append(cwd)

    # Add parent directories
    for parent in cwd.parents:
        search_paths.append(parent)
        # Stop at reasonable depth (e.g., git root or drive root)
        if (parent / ".git").exists() or parent.parent == parent:
            break

    # Load .env files from search paths
    loaded_files = []
    for base_path in search_paths:
        for env_file in DOTENV_FILES:
            env_path = base_path / env_file
            if env_path.exists() and str(env_path) not in loaded_files:
                load_dotenv(env_path, override=False)
                loaded_files.append(str(env_path))
                logger.debug(f"Loaded environment from: {env_path}")

    if loaded_files:
        logger.info(f"Loaded {len(loaded_files)} .env file(s)")


class TranscriptionError(Exception):
    """Transcription API error"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class FFmpegNotFoundError(Exception):
    """FFmpeg not installed error"""
    pass


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available"""
    return shutil.which("ffmpeg") is not None


def get_file_type(file_path: Path) -> str:
    """
    Determine file type based on extension

    Returns:
        'audio', 'video', or 'unknown'
    """
    ext = file_path.suffix.lower()
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def extract_audio_from_video(
    video_path: Path,
    output_format: str = "mp3",
    output_path: Optional[Path] = None
) -> Path:
    """
    Extract audio track from video file using FFmpeg

    Args:
        video_path: Path to video file
        output_format: Output audio format (default: mp3)
        output_path: Optional output path (default: temp file)

    Returns:
        Path to extracted audio file

    Raises:
        FFmpegNotFoundError: If FFmpeg is not installed
        RuntimeError: If extraction fails
    """
    if not check_ffmpeg():
        raise FFmpegNotFoundError(
            "FFmpeg is required for video processing. "
            "Install from https://ffmpeg.org or via package manager:\n"
            "  - Windows: winget install ffmpeg\n"
            "  - macOS: brew install ffmpeg\n"
            "  - Linux: apt install ffmpeg"
        )

    if output_path is None:
        # Create temp file
        temp_dir = tempfile.gettempdir()
        output_path = Path(temp_dir) / f"audio_{uuid.uuid4().hex[:8]}.{output_format}"

    logger.info(f"Extracting audio from video: {video_path}")

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "libmp3lame" if output_format == "mp3" else "pcm_s16le",
        "-ar", "16000",  # Sample rate
        "-ac", "1",  # Mono
        "-y",  # Overwrite
        str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr}")

        if not output_path.exists():
            raise RuntimeError("Audio extraction failed: output file not created")

        logger.info(f"Audio extracted to: {output_path}")
        return output_path

    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg timeout: video file may be too large")


class AudioTranscriber:
    """Audio/Video transcriber using Volcengine Doubao ASR Flash API"""

    def __init__(self, appid: str, token: str):
        """
        Initialize transcriber

        Args:
            appid: Volcengine Application ID
            token: Volcengine Access Token
        """
        self.appid = appid
        self.token = token
        self._temp_files = []  # Track temp files for cleanup

    def __del__(self):
        """Cleanup temp files"""
        self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        """Remove temporary files"""
        for temp_file in self._temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        self._temp_files = []

    def transcribe(
        self,
        url: Optional[str] = None,
        file: Optional[Union[str, Path]] = None,
        timeout: float = 300.0,
        keep_temp: bool = False
    ) -> dict:
        """
        Transcribe audio/video from URL or local file

        Args:
            url: Public accessible audio URL
            file: Path to local audio or video file
            timeout: Request timeout in seconds (default: 300s for large files)
            keep_temp: Keep temporary audio file after transcription (default: False)

        Returns:
            dict: Transcription result

        Raises:
            ValueError: If neither url nor file is provided
            FileNotFoundError: If local file doesn't exist
            FFmpegNotFoundError: If video file provided but FFmpeg not installed
            TranscriptionError: If API returns error
        """
        if not url and not file:
            raise ValueError("Either 'url' or 'file' must be provided")

        if url and file:
            raise ValueError("Provide either 'url' or 'file', not both")

        try:
            if file:
                return self._transcribe_file(file, timeout)
            else:
                return self._transcribe_url(url, timeout)
        finally:
            if not keep_temp:
                self._cleanup_temp_files()

    def _transcribe_url(self, url: str, timeout: float) -> dict:
        """Transcribe from URL"""
        logger.info(f"Transcribing from URL: {url}")

        body = {
            "user": {"uid": "user"},
            "audio": {"url": url},
            "request": {"model_name": "bigmodel"}
        }

        return self._call_api(body, timeout)

    def _transcribe_file(self, file_path: Union[str, Path], timeout: float) -> dict:
        """Transcribe from local file (audio or video)"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file_type = get_file_type(path)

        if file_type == "video":
            # Extract audio from video
            logger.info(f"Detected video file: {path.suffix}")
            audio_path = extract_audio_from_video(path)
            self._temp_files.append(audio_path)
            path = audio_path
        elif file_type == "unknown":
            logger.warning(f"Unknown file type: {path.suffix}, attempting as audio")

        file_size = path.stat().st_size
        logger.info(f"Transcribing file: {path} ({file_size / 1024 / 1024:.1f}MB)")

        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size / 1024 / 1024:.1f}MB (max: 100MB)")

        if file_size > RECOMMENDED_SIZE:
            logger.warning(f"File larger than recommended 20MB, upload may be slow")

        # Read and encode file
        with open(path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")

        body = {
            "user": {"uid": "user"},
            "audio": {"data": audio_data},
            "request": {"model_name": "bigmodel"}
        }

        return self._call_api(body, timeout)

    def _call_api(self, body: dict, timeout: float) -> dict:
        """Make API call"""
        request_id = str(uuid.uuid4())

        headers = {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.token,
            "X-Api-Resource-Id": RESOURCE_ID,
            "X-Api-Request-Id": request_id,
            "X-Api-Sequence": "-1",
            "Content-Type": "application/json"
        }

        logger.info(f"Sending request (ID: {request_id})")

        response = requests.post(
            API_URL,
            json=body,
            headers=headers,
            timeout=timeout,
            verify=False  # Disable SSL verification for proxy environments
        )

        status_code = response.headers.get("X-Api-Status-Code", "")
        message = response.headers.get("X-Api-Message", "Unknown error")
        log_id = response.headers.get("X-Tt-Logid", "")

        logger.info(f"Response: {status_code} - {message} (LogId: {log_id})")

        if status_code == STATUS_SUCCESS:
            return response.json()
        elif status_code == STATUS_SILENT:
            logger.warning("Audio appears to be silent")
            return response.json()
        else:
            raise TranscriptionError(status_code, message)


def get_text(result: dict) -> str:
    """Extract plain text from result"""
    return result.get("result", {}).get("text", "")


def get_duration(result: dict) -> float:
    """Get audio duration in seconds"""
    ms = result.get("audio_info", {}).get("duration", 0)
    return ms / 1000


def main():
    # Load .env files first
    load_env_files()

    parser = argparse.ArgumentParser(
        description="Volcengine Doubao ASR Flash - Audio/Video Transcription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Transcribe from URL
    python transcribe.py --url "https://example.com/audio.mp3"

    # Transcribe from local audio file
    python transcribe.py --file "./recording.mp3"

    # Transcribe from local video file (requires FFmpeg)
    python transcribe.py --file "./video.mp4"

    # Output text only
    python transcribe.py --file "./audio.mp3" --text-only

    # Save to file
    python transcribe.py --file "./video.mp4" -o result.json

    # With explicit credentials
    python transcribe.py --file "./audio.mp3" --appid YOUR_ID --token YOUR_TOKEN

Credentials (priority: CLI args > .env file > environment variables):
    1. Create a .env file in one of these locations:
       - Script directory: audio-transcription-skill/.env
       - User config: ~/.volc-asr/.env
       - Project root: .env (current directory)

    2. Add your credentials to .env:
       VOLCENGINE_APP_ID=your_app_id
       VOLCENGINE_ACCESS_TOKEN=your_access_token

    3. Or use environment variables:
       export VOLCENGINE_APP_ID='your_app_id'
       export VOLCENGINE_ACCESS_TOKEN='your_token'

Supported formats:
    Audio: mp3, wav, ogg, m4a, flac, aac
    Video: mp4, mkv, avi, mov, wmv, flv, webm, ts, m4v (requires FFmpeg)
        """
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url", help="Audio file URL")
    input_group.add_argument("--file", "-f", help="Local audio or video file path")

    parser.add_argument("--appid", help="Volcengine App ID (overrides .env and env vars)")
    parser.add_argument("--token", help="Volcengine Access Token (overrides .env and env vars)")
    parser.add_argument("--text-only", action="store_true", help="Output text only")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--timeout", type=float, default=300.0, help="Request timeout in seconds (default: 300)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary audio file (for video input)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-env", action="store_true", help="Skip loading .env files")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get credentials (priority: CLI args > .env > environment variables)
    appid = args.appid or os.environ.get("VOLCENGINE_APP_ID")
    token = args.token or os.environ.get("VOLCENGINE_ACCESS_TOKEN")

    if not appid or not token:
        print("Error: API credentials required")
        print("\nPlease provide credentials in one of these ways:")
        print("  1. Create a .env file with:")
        print("     VOLCENGINE_APP_ID=your_app_id")
        print("     VOLCENGINE_ACCESS_TOKEN=your_access_token")
        print("     Place it in: script dir, ~/.volc-asr/, or current directory")
        print("  2. Set environment variables:")
        print("     export VOLCENGINE_APP_ID='your_app_id'")
        print("     export VOLCENGINE_ACCESS_TOKEN='your_token'")
        print("  3. Use CLI arguments:")
        print("     --appid YOUR_ID --token YOUR_TOKEN")
        print("\nNote: python-dotenv is recommended for .env support")
        print("      Install with: pip install python-dotenv")
        sys.exit(1)

    # Check FFmpeg for video files
    if args.file:
        file_path = Path(args.file)
        if file_path.suffix.lower() in VIDEO_EXTENSIONS and not check_ffmpeg():
            print("Error: FFmpeg is required for video file processing")
            print("Install FFmpeg from https://ffmpeg.org or via package manager:")
            print("  - Windows: winget install ffmpeg")
            print("  - macOS: brew install ffmpeg")
            print("  - Linux: apt install ffmpeg")
            sys.exit(1)

    # Create transcriber
    transcriber = AudioTranscriber(appid, token)

    try:
        # Run transcription
        result = transcriber.transcribe(
            url=args.url,
            file=args.file,
            timeout=args.timeout,
            keep_temp=args.keep_temp
        )

        # Format output
        if args.text_only:
            output = get_text(result)
        else:
            output = json.dumps(result, ensure_ascii=False, indent=2)

        # Write or print
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            logger.info(f"Result saved to: {args.output}")
        else:
            print(output)

        # Log summary
        duration = get_duration(result)
        text_len = len(get_text(result))
        logger.info(f"Duration: {duration:.1f}s, Text length: {text_len} chars")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except FFmpegNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except TranscriptionError as e:
        logger.error(f"Transcription failed: {e}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        logger.error("Request timeout - try increasing --timeout for large files")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
