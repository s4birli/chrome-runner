from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
import os

from schemas import VideoInfo, VideoRequest, DownloadRequest, DownloadResult
from services.youtube import YouTubeService
from config import settings

router = APIRouter(prefix=settings.API_V1_STR, tags=["youtube"])

@router.post("/info", response_model=VideoInfo)
async def get_video_info(request: VideoRequest):
    """
    Get information about a YouTube video
    """
    try:
        video_info = await YouTubeService.get_video_info(request.url)
        return video_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")

@router.post("/download", response_model=DownloadResult)
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks, req: Request):
    """
    Download a YouTube video with the specified format
    """
    try:
        # Download the video
        download_result = await YouTubeService.download(
            url=request.url,
            format_id=request.format_id,
            audio_only=request.audio_only
        )
        
        # Create download URL
        base_url = str(req.base_url).rstrip('/')
        download_url = f"{base_url}{settings.API_V1_STR}/file/{download_result['relative_path']}"
        download_result['download_url'] = download_url
        
        return download_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")

@router.get("/file/{file_path:path}")
async def serve_file(file_path: str, req: Request):
    """
    Serve a downloaded file
    """
    try:
        # Construct absolute path from relative path
        full_path = os.path.join(settings.DOWNLOAD_PATH, file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        # Get file information
        file_info = {
            'name': os.path.basename(full_path),
            'content_type': 'video/mp4' if full_path.endswith('.mp4') else 'audio/mpeg' if full_path.endswith('.mp3') else 'application/octet-stream'
        }
        
        # Set headers for download
        headers = {
            "Content-Disposition": f"attachment; filename=\"{file_info['name']}\"",
        }
        
        # Return file response
        return FileResponse(
            path=full_path,
            media_type=file_info['content_type'],
            headers=headers,
            filename=file_info['name']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}") 