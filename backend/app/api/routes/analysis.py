from fastapi import APIRouter, HTTPException, status
from app.schemas.analysis import VideoMetadataRequest, VideoMetadataResponse
from app.services.extractor import MetadataExtractor
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze", response_model=VideoMetadataResponse)
def analyze_video(payload: VideoMetadataRequest):
    """
    Extract and normalize metadata for a YouTube or Instagram Reel URL.
    Runs immediately and returns structured JSON of video properties.
    """
    try:
        logger.info(f"Received metadata extraction request for URL: {payload.url}")
        metadata = MetadataExtractor.extract_metadata(payload.url)
        return metadata
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during video metadata extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the video URL: {str(e)}"
        )
