from typing import List, Dict, Optional
from pydantic import BaseModel, validator
import re

class VideoFormat(BaseModel):
    """Format of a YouTube video"""
    format_id: str
    ext: str
    resolution: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    filesize: Optional[int] = None
    tbr: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    format_note: Optional[str] = None
    audio_only: bool = False

class VideoInfo(BaseModel):
    """YouTube video information"""
    id: str
    title: str
    url: str
    webpage_url: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    formats: List[VideoFormat] = []

class VideoRequest(BaseModel):
    """Request to fetch video information or download"""
    url: str
    
    @validator('url')
    def validate_youtube_url(cls, v):
        if not re.match(r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([^\s&]+)', v):
            if re.match(r'^[0-9A-Za-z_-]{11}$', v):
                # Valid YouTube ID, convert to URL
                return f"https://www.youtube.com/watch?v={v}"
            raise ValueError('Invalid YouTube URL or ID')
        return v

class DownloadRequest(VideoRequest):
    """Request to download a video"""
    format_id: Optional[str] = None
    audio_only: bool = False

class DownloadResult(BaseModel):
    """Result of a download operation"""
    id: str
    title: str
    file_path: str
    relative_path: str
    file_size: int
    download_time: float
    format: str
    expiry_time: int
    audio_only: bool
    download_url: Optional[str] = None 