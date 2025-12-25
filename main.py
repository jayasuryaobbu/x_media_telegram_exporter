#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import yt_dlp

# ----------------------------
# USER SETTINGS (edit here)
# ----------------------------
URLS = [
    "https://x.com/<user>/status/<id>",
]

MODE = "download"   # "download" or "links"
OUT_DIR = Path("./x_downloads")

# If a tweet is public, cookies are usually not needed.
# For login/protected content, choose ONE:
USE_SAFARI_COOKIES = False
SAFARI_PROFILE = None  # usually None is fine; keep None unless you know you need a specific profile name/path

USE_COOKIES_TXT = False
COOKIES_TXT_PATH = Path("./cookies.txt")  # Netscape cookies.txt format if you export it

# Format selection:
# - For videos: try best video+audio, fallback to best
# - For images: yt-dlp will typically pick the best available image URL(s)
FORMAT = "bestvideo+bestaudio/best"
# ----------------------------


def _make_ydl(download: bool) -> yt_dlp.YoutubeDL:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": FORMAT,
        "noplaylist": True,
        "ignoreerrors": True,
        "quiet": True,

        # Output template only matters for download mode
        "outtmpl": str(OUT_DIR / "%(extractor)s_%(uploader)s_%(id)s_%(title).200B.%(ext)s"),
        "merge_output_format": "mp4",
    }

    if USE_SAFARI_COOKIES:
        # yt-dlp expects a tuple like (browser_name,) or (browser_name, profile)
        ydl_opts["cookiesfrombrowser"] = ("safari",) if not SAFARI_PROFILE else ("safari", SAFARI_PROFILE)

    if USE_COOKIES_TXT:
        ydl_opts["cookiefile"] = str(COOKIES_TXT_PATH)

    if not download:
        # Ensure yt-dlp doesn't write media files
        ydl_opts["skip_download"] = True

    return yt_dlp.YoutubeDL(ydl_opts)


def _collect_best_links(info: dict) -> list[dict]:
    """
    Returns a list of items like:
      {"id": "...", "title": "...", "page_url": "...", "links": [{"type":"video","url":"..."}, ...]}
    """
    def entry_to_links(e: dict) -> list[dict]:
        links = []

        # If yt-dlp selected formats (common for video), they appear here
        for rf in e.get("requested_formats") or []:
            u = rf.get("url")
            if u:
                links.append({"type": "video_or_audio_variant", "url": u})

        # Some extractors put a single selected format here
        if e.get("url"):
            links.append({"type": "direct", "url": e["url"]})

        # If formats exist, also pick a “best-looking” one (highest bitrate/resolution)
        fmts = e.get("formats") or []
        if fmts:
            def score(f):
                # Prefer higher bitrate, then resolution
                return (
                    (f.get("tbr") or 0),
                    (f.get("height") or 0),
                    (f.get("width") or 0),
                )
            best = max(fmts, key=score)
            if best.get("url"):
                links.append({"type": "best_format_guess", "url": best["url"]})

        # For image tweets, sometimes thumbnails carry the actual image URLs
        thumbs = e.get("thumbnails") or []
        if thumbs:
            def tscore(t):
                return ((t.get("width") or 0), (t.get("height") or 0))
            best_thumb = max(thumbs, key=tscore)
            if best_thumb.get("url"):
                links.append({"type": "best_thumbnail_guess", "url": best_thumb["url"]})

        # Deduplicate while preserving order
        seen = set()
        out = []
        for item in links:
            if item["url"] not in seen:
                seen.add(item["url"])
                out.append(item)
        return out

    # Tweets with multiple media may come as a playlist-like structure
    if info.get("_type") == "playlist" and info.get("entries"):
        items = []
        for e in info["entries"]:
            if not e:
                continue
            items.append({
                "id": e.get("id"),
                "title": e.get("title"),
                "page_url": e.get("webpage_url") or e.get("original_url"),
                "links": entry_to_links(e),
            })
        return items

    return [{
        "id": info.get("id"),
        "title": info.get("title"),
        "page_url": info.get("webpage_url") or info.get("original_url"),
        "links": entry_to_links(info),
    }]


def main():
    if MODE not in ("download", "links"):
        raise ValueError("MODE must be 'download' or 'links'")

    if MODE == "download":
        ydl = _make_ydl(download=True)
        ydl.download(URLS)
        print(f"Downloaded into: {OUT_DIR.resolve()}")
        return

    # MODE == "links"
    ydl = _make_ydl(download=False)
    all_items = []
    for u in URLS:
        info = ydl.extract_info(u, download=False)
        if not info:
            continue
        all_items.extend(_collect_best_links(info))

    print(json.dumps(all_items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
