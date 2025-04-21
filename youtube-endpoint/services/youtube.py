import os
import asyncio
import re
import time
import logging
from typing import Dict, List, Optional, Any

import yt_dlp

from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeService:
    """
    Service for handling YouTube video operations:
    - Extracting video information
    - Downloading videos in specified quality
    - Processing audio/video streams
    """
    
    @staticmethod
    def _get_yt_dlp_options(options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get default yt-dlp options with any additional options merged
        """
        # Default options
        default_options = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': settings.COOKIE_FILE if os.path.exists(settings.COOKIE_FILE) and os.path.getsize(settings.COOKIE_FILE) > 0 else None,
        }
        
        # Remove None values
        if default_options.get('cookiefile') is None:
            default_options.pop('cookiefile', None)
        
        # Merge with provided options
        if options:
            default_options.update(options)
            
        return default_options
    
    @classmethod
    async def get_video_info(cls, url: str) -> Dict:
        """
        Get detailed information about a YouTube video
        """
        try:
            # If just a video ID was passed, convert to full URL
            if re.match(r'^[0-9A-Za-z_-]{11}$', url):
                url = f"https://www.youtube.com/watch?v={url}"
                
            video_id = cls._extract_video_id(url)
            logger.info(f"Fetching info for video: {video_id}")
        except ValueError as e:
            logger.error(f"Invalid YouTube URL: {url}")
            raise ValueError(f"Invalid YouTube URL: {url}")
            
        # Set up yt-dlp options for info extraction
        info_options = cls._get_yt_dlp_options({
            'skip_download': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
        })
        
        try:
            # Extract video information
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(info_options) as ydl:
                info = await loop.run_in_executor(None, ydl.extract_info, url, False)
                
            if not info:
                logger.warning(f"Could not fetch info for video: {url}")
                raise ValueError(f"Could not fetch info for video: {url}")
                
            # Format response
            video_info = {
                'id': info.get('id'),
                'title': info.get('title', 'Unknown Title'),
                'url': url,
                'webpage_url': info.get('webpage_url', url),
                'description': info.get('description', ''),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'upload_date': info.get('upload_date', ''),
                'formats': cls._parse_formats(info.get('formats', [])),
            }
            
            logger.info(f"Successfully fetched info for video: {video_id}")
            return video_info
            
        except Exception as e:
            logger.error(f"Error fetching video info: {str(e)}")
            raise ValueError(f"Failed to get video information: {str(e)}")
                
    @classmethod
    def _parse_formats(cls, formats: List[Dict]) -> List[Dict]:
        """
        Parse and normalize video format information
        """
        if not formats:
            return []
        
        max_height = int(settings.MAX_RESOLUTION.rstrip('p'))
        
        # Filter formats based on maximum resolution
        filtered_formats = []
        for fmt in formats:
            if not fmt:
                continue
                
            # Skip formats without video if not audio-only
            if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                # Include only if it's an audio format
                audio_format = {
                    'format_id': fmt.get('format_id', ''),
                    'ext': fmt.get('ext', ''),
                    'format_note': 'Audio only',
                    'filesize': fmt.get('filesize', 0) or fmt.get('filesize_approx', 0),
                    'tbr': fmt.get('tbr', 0),
                    'acodec': fmt.get('acodec', ''),
                    'audio_only': True,
                }
                filtered_formats.append(audio_format)
            elif fmt.get('height', 0) and fmt.get('height', 0) <= max_height:
                # Include as a video format
                video_format = {
                    'format_id': fmt.get('format_id', ''),
                    'ext': fmt.get('ext', ''),
                    'resolution': fmt.get('resolution', 'unknown'),
                    'width': fmt.get('width', 0),
                    'height': fmt.get('height', 0),
                    'fps': fmt.get('fps', 0),
                    'filesize': fmt.get('filesize', 0) or fmt.get('filesize_approx', 0),
                    'tbr': fmt.get('tbr', 0),
                    'vcodec': fmt.get('vcodec', ''),
                    'acodec': fmt.get('acodec', ''),
                    'format_note': fmt.get('format_note', ''),
                    'audio_only': False,
                }
                filtered_formats.append(video_format)
            
        # Sort by height (resolution) in descending order
        filtered_formats.sort(key=lambda x: (0 if x.get('audio_only', False) else x.get('height', 0)), reverse=True)
        
        # Remove duplicate resolutions, keeping the best quality
        seen_resolutions = set()
        unique_formats = []
        
        for fmt in filtered_formats:
            # For audio-only formats
            if fmt.get('audio_only', False):
                if 'audio_only' not in seen_resolutions:
                    seen_resolutions.add('audio_only')
                    unique_formats.append(fmt)
                continue
                
            # For video formats
            height = fmt.get('height', 0)
            if height and height not in seen_resolutions:
                seen_resolutions.add(height)
                unique_formats.append(fmt)
                
        return unique_formats
    
    @classmethod
    async def download(cls, url: str, format_id: str = None, audio_only: bool = False) -> Dict:
        """
        Download a YouTube video
        """
        try:
            # If just a video ID was passed, convert to full URL
            if re.match(r'^[0-9A-Za-z_-]{11}$', url):
                url = f"https://www.youtube.com/watch?v={url}"
            
            video_id = cls._extract_video_id(url)
            logger.info(f"Starting download for video: {video_id}")
            
            # Create a unique directory for this download
            download_id = f"{video_id}_{int(time.time())}"
            output_path = os.path.join(settings.DOWNLOAD_PATH, download_id)
            os.makedirs(output_path, exist_ok=True)
                
            # Get video info to determine best format if not specified
            video_info = await cls.get_video_info(url)
            
            # Use video title as filename, removing invalid characters
            filename = re.sub(r'[^\w\s-]', '', video_info['title'])
            filename = re.sub(r'[-\s]+', '-', filename).strip('-_')
            
            # Setup download options
            download_options = cls._get_yt_dlp_options({
                'outtmpl': os.path.join(output_path, f"{filename}.%(ext)s"),
            })
            
            # If audio only, get best audio
            if audio_only:
                download_options['format'] = 'bestaudio/best'
                download_options['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            # If format ID specified, use it
            elif format_id:
                download_options['format'] = format_id
            else:
                # Otherwise use best format with height <= max resolution
                max_height = int(settings.MAX_RESOLUTION.rstrip('p'))
                download_options['format'] = f'bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]'
            
            # Download the video
            loop = asyncio.get_event_loop()
            
            download_start_time = time.time()
            
            with yt_dlp.YoutubeDL(download_options) as ydl:
                download_info = await loop.run_in_executor(None, ydl.extract_info, url, False)
            
            download_time = time.time() - download_start_time
            
            # Find the downloaded file
            downloaded_file = None
            expected_extensions = ['mp3'] if audio_only else ['mp4', 'webm', 'mkv']
            
            for ext in expected_extensions:
                potential_file = os.path.join(output_path, f"{filename}.{ext}")
                if os.path.exists(potential_file):
                    downloaded_file = potential_file
                    break
            
            if not downloaded_file:
                logger.error(f"Could not find downloaded file for video: {video_id}")
                raise ValueError(f"Download failed: Could not find downloaded file")
            
            file_size = os.path.getsize(downloaded_file)
            relative_path = os.path.relpath(downloaded_file, settings.DOWNLOAD_PATH)
            
            logger.info(f"Successfully downloaded video {video_id} to {downloaded_file} ({file_size} bytes in {download_time:.1f}s)")
            
            return {
                'id': video_id,
                'title': video_info['title'],
                'file_path': downloaded_file,
                'relative_path': relative_path,
                'file_size': file_size,
                'download_time': download_time,
                'format': format_id or download_options['format'],
                'expiry_time': int(time.time()) + settings.FILE_EXPIRY_SECONDS,
                'audio_only': audio_only
            }
            
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise ValueError(f"Failed to download video: {str(e)}")
    
    @classmethod
    def _extract_video_id(cls, url: str) -> str:
        """
        Extract the video ID from a YouTube URL
        """
        # Default regex pattern to extract YouTube video ID
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        raise ValueError(f"Could not extract video ID from URL: {url}") 