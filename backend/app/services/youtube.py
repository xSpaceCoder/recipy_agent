import subprocess
import json
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


def extract_youtube_info(url: str) -> str:
    logger.info(f"Extracting YouTube info for: {url}")

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--skip-download",
                "--write-auto-sub",
                "--sub-lang", "en,de",
                "--sub-format", "vtt",
                "--print", "%(title)s\n%(description)s",
                "--write-subs",
                "--output", "%(id)s",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=tempfile.gettempdir(),
        )

        logger.info(f"yt-dlp return code: {result.returncode}")
        logger.debug(f"yt-dlp stdout: {result.stdout[:500]}")
        if result.stderr:
            logger.warning(f"yt-dlp stderr: {result.stderr[:500]}")

        title_and_desc = result.stdout.strip()

        subtitle_text = ""
        temp_dir = tempfile.gettempdir()
        vtt_files = [f for f in os.listdir(temp_dir) if f.endswith(".vtt")]
        logger.info(f"Found {len(vtt_files)} .vtt files in temp dir")

        for f in vtt_files:
            filepath = os.path.join(temp_dir, f)
            try:
                subtitle_text = _parse_vtt(filepath)
                logger.info(f"Parsed subtitles from {f}: {len(subtitle_text)} chars")
            finally:
                os.remove(filepath)
            break

        parts = []
        if title_and_desc:
            parts.append(f"Title and Description:\n{title_and_desc}")
        if subtitle_text:
            parts.append(f"Subtitles/Transcript:\n{subtitle_text}")

        if not parts:
            logger.warning("No content from primary extraction, trying fallback")
            return _fallback_metadata(url)

        combined = "\n\n".join(parts)[:8000]
        logger.info(f"Final extracted content length: {len(combined)} chars")
        logger.debug(f"Content preview: {combined[:300]}")
        return combined

    except subprocess.TimeoutExpired:
        logger.error("yt-dlp timed out")
        return _fallback_metadata(url)
    except FileNotFoundError:
        logger.error("yt-dlp not found in PATH")
        return _fallback_metadata(url)


def _parse_vtt(filepath: str) -> str:
    lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("WEBVTT") or "-->" in line or line.isdigit():
                continue
            if line not in lines:
                lines.append(line)
    return " ".join(lines)


def _fallback_metadata(url: str) -> str:
    logger.info("Using fallback metadata extraction (--dump-json)")
    try:
        result = subprocess.run(
            ["yt-dlp", "--skip-download", "--dump-json", url],
            capture_output=True,
            text=True,
            timeout=20,
        )
        logger.info(f"Fallback return code: {result.returncode}")
        if result.stderr:
            logger.warning(f"Fallback stderr: {result.stderr[:300]}")

        if not result.stdout.strip():
            logger.error("Fallback returned empty stdout")
            return ""

        data = json.loads(result.stdout)
        parts = [
            f"Title: {data.get('title', '')}",
            f"Description: {data.get('description', '')}",
        ]
        combined = "\n".join(parts)[:8000]
        logger.info(f"Fallback content length: {len(combined)} chars")
        logger.debug(f"Fallback preview: {combined[:300]}")
        return combined
    except Exception as e:
        logger.error(f"Fallback failed: {e}")
        return ""
