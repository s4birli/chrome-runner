import os
from pathlib import Path

class Settings:
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent

    # Download settings
    DOWNLOAD_PATH = os.path.join(BASE_DIR, "downloads")
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    # Cookie settings
    COOKIE_FILE = os.path.join(BASE_DIR, "cookies.txt")

    # File settings
    FILE_EXPIRY_SECONDS = 3600  # 1 hour
    MAX_RESOLUTION = "1080p"  # Maximum video resolution to allow

    # API settings
    API_V1_STR = "/api/v1"

settings = Settings() 