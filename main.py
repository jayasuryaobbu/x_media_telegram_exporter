#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import subprocess
import shutil
import time
import random
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError

# ----------------------------
# USER SETTINGS (Edit these variables to run from PyCharm)
# ----------------------------
URLS = [
    # Add your URLs here, e.g.:
    # "https://x.com/SpaceX/status/123456789",
    "https://x.com/Baaba_Yaagaa/status/2004015769999626747",
]

MODE = "download"   # Options: "download" or "links"
OUT_DIR = Path("./x_downloads")

# Safety / Rate Limiting
# Time to wait (in seconds) between processing each URL to avoid getting blocked.
# X.com is strict; a delay of 10-30 seconds is recommended for batch processing.
MIN_DELAY = 10
MAX_DELAY = 30

# Debug Mode
DEBUG = True

# Cookie Settings
# ---------------------------------------------------------
# IMPORTANT: X (Twitter) often blocks anonymous access.
# ---------------------------------------------------------
# Option 1: Use cookies from your browser (e.g. Chrome, Safari, Firefox)
USE_BROWSER_COOKIES = True
BROWSER_NAME = "chrome"  # options: "chrome", "safari", "firefox", "edge"
BROWSER_PROFILE = None   # usually None is fine

# Option 2: Use a cookies.txt file (Netscape format)
USE_COOKIES_TXT = False
COOKIES_TXT_PATH = Path("./cookies.txt")

# Format selection for yt-dlp (Videos)
FORMAT = "bestvideo+bestaudio/best"
# ----------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _check_gallery_dl():
    """Checks if gallery-dl is installed and available in PATH."""
    if not shutil.which("gallery-dl"):
        logger.error("gallery-dl is not installed or not in PATH.")
        logger.info("Please install it via pip: pip install gallery-dl")
        return False
    return True


def _download_with_gallery_dl(url: str) -> bool:
    """
    Attempts to download images using gallery-dl.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Attempting to download images with gallery-dl: {url}")
    
    # Filename format: twitter_{user}_{id}_{num}.{extension}
    cmd = [
        "gallery-dl",
        "--directory", str(OUT_DIR.resolve()),
        "--filename", "twitter_{user}_{id}_{num}.{extension}",
        url
    ]

    # Add cookie arguments if configured
    if USE_BROWSER_COOKIES:
        cmd.extend(["--cookies-from-browser", BROWSER_NAME])
    elif USE_COOKIES_TXT:
        cmd.extend(["--cookies", str(COOKIES_TXT_PATH)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if "No suitable downloader found" in result.stderr:
                logger.warning("gallery-dl could not handle this URL.")
                return False
            logger.info("gallery-dl finished successfully.")
            if DEBUG:
                logger.info(result.stdout)
            return True
        else:
            logger.warning(f"gallery-dl failed with code {result.returncode}")
            if DEBUG:
                logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Failed to run gallery-dl: {e}")
        return False


def _make_ydl(download: bool) -> yt_dlp.YoutubeDL:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": FORMAT,
        "outtmpl": str(OUT_DIR / "twitter_video_%(uploader)s_%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "ignoreerrors": True,
        "quiet": not DEBUG,
        "no_warnings": not DEBUG,
        "verbose": DEBUG,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    if USE_BROWSER_COOKIES:
        ydl_opts["cookiesfrombrowser"] = (BROWSER_NAME,) if not BROWSER_PROFILE else (BROWSER_NAME, BROWSER_PROFILE)
    
    if USE_COOKIES_TXT:
        ydl_opts["cookiefile"] = str(COOKIES_TXT_PATH)

    if not download:
        ydl_opts["skip_download"] = True

    return yt_dlp.YoutubeDL(ydl_opts)


def main():
    if not URLS:
        logger.warning("No URLS provided in settings.")
        return

    if len(URLS) == 1 and "x.com/<user>/status/<id>" in URLS[0]:
        logger.warning("Placeholder URL detected. Please edit main.py and add real X/Twitter links.")
        return

    # Ensure output directory exists
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check for gallery-dl availability
    has_gallery_dl = _check_gallery_dl()

    logger.info(f"Starting in mode: {MODE}")
    
    if MODE == "download":
        ydl = _make_ydl(download=True)
        
        total_urls = len(URLS)
        for i, url in enumerate(URLS):
            logger.info(f"Processing [{i+1}/{total_urls}]: {url}")
            
            video_success = False
            try:
                # Try yt-dlp first (Best for Videos)
                ret_code = ydl.download([url])
                if ret_code == 0:
                    video_success = True
            except DownloadError as e:
                logger.warning(f"yt-dlp failed to find a video: {e}")
                video_success = False
            except Exception as e:
                logger.error(f"Unexpected yt-dlp error: {e}")
                video_success = False

            # If video download failed, or if we just want to be sure we got images too:
            if not video_success and has_gallery_dl:
                logger.info("Falling back to gallery-dl for potential images...")
                _download_with_gallery_dl(url)
            elif not video_success and not has_gallery_dl:
                logger.warning("Video download failed and gallery-dl is not available to try for images.")

            # Rate Limiting Delay (only if there are more items to process)
            if i < total_urls - 1:
                sleep_time = random.randint(MIN_DELAY, MAX_DELAY)
                logger.info(f"Sleeping for {sleep_time} seconds to avoid rate limits...")
                time.sleep(sleep_time)

        logger.info(f"Process finished. Check output directory: {OUT_DIR.resolve()}")
        return

    # MODE == "links"
    ydl = _make_ydl(download=False)
    all_items = []
    for i, u in enumerate(URLS):
        try:
            info = ydl.extract_info(u, download=False)
            if info:
                all_items.append(info)
        except Exception as e:
            logger.error(f"Failed to extract info for {u}: {e}")
        
        if i < len(URLS) - 1:
            time.sleep(random.randint(2, 5)) # Shorter delay for just link extraction

    print(json.dumps(all_items, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
