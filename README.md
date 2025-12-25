# X Media Telegram Exporter

A simple Python script to download media (videos, images) from X (formerly Twitter) or extract direct media links using `yt-dlp`.

## Prerequisites

- Python 3.8+
- `yt-dlp` (installed via requirements)
- `ffmpeg` (optional, but recommended for merging video+audio streams)

## Installation

1. Clone the repository.
2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage (PyCharm / IDE)

This script is designed to be run directly from your IDE (like PyCharm or VS Code).

1. Open `main.py`.
2. Edit the **USER SETTINGS** section at the top of the file:
   - **URLS**: Add the list of X/Twitter URLs you want to process.
   - **MODE**: Set to `"download"` to save files locally, or `"links"` to just print the media URLs.
   - **OUT_DIR**: Change the download folder if needed.
3. Run the script (Right-click `main.py` -> Run).

### Example Configuration

```python
URLS = [
    "https://x.com/SpaceX/status/1800000000000000000",
]
MODE = "download"
```

## Authentication (Fixing "Video not found" errors)

X (Twitter) often blocks anonymous downloads. To fix this, you need to provide your cookies.

### Option 1: Direct Browser Access (Easiest)
1. Log in to X.com on Chrome, Firefox, or Safari.
2. In `main.py`, set:
   ```python
   USE_BROWSER_COOKIES = True
   BROWSER_NAME = "chrome"  # or "safari", "firefox"
   ```
   *Note: On macOS, Safari cookies are encrypted and hard to access for external tools. Chrome or Firefox is recommended.*

### Option 2: Using `cookies.txt` (If Option 1 fails)
If you must use Safari or if the direct method fails, you can manually export cookies.

1. **Install a Browser Extension**:
   - **Chrome/Firefox**: Install "Get cookies.txt LOCALLY" (or similar).
   - **Safari**: Safari makes this difficult. It is **highly recommended** to just log in to X on Chrome or Firefox temporarily to export the cookies.
2. **Export**:
   - Go to x.com.
   - Click the extension icon and export as "Netscape HTTP Cookie File".
   - Save the file as `cookies.txt` in this project folder.
3. **Configure**:
   - In `main.py`, set:
     ```python
     USE_COOKIES_TXT = True
     COOKIES_TXT_PATH = Path("./cookies.txt")
     ```
