from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.schemas.analysis import CompareRequest, ChatRequest, VideoMetadataResponse
from app.services.pipeline import indexing_pipeline, query_pipeline
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session cache for the latest analyzed video pair
LATEST_ANALYZED_VIDEOS = []

@router.post("/analyze")
def analyze_videos(payload: CompareRequest):
    """
    Extract and index metadata and transcripts for both a YouTube video and an Instagram Reel.
    Stores chunks in Qdrant, generates embeddings, and caches the result for future chat questions.
    """
    try:
        logger.info(f"Received compare/analyze request. YouTube: {payload.youtube_url} | Instagram: {payload.instagram_url}")
        
        # 1. Run YouTube Indexing Pipeline
        logger.info(f"Running indexing pipeline for YouTube URL: {payload.youtube_url}")
        state_a = indexing_pipeline.invoke({"url": payload.youtube_url})
        metadata_a = state_a.get("metadata")
        if not metadata_a:
            raise ValueError(f"Failed to retrieve metadata for YouTube URL: {payload.youtube_url}")
            
        # 2. Run Instagram Indexing Pipeline
        logger.info(f"Running indexing pipeline for Instagram URL: {payload.instagram_url}")
        state_b = indexing_pipeline.invoke({"url": payload.instagram_url})
        metadata_b = state_b.get("metadata")
        if not metadata_b:
            raise ValueError(f"Failed to retrieve metadata for Instagram Reel URL: {payload.instagram_url}")
            
        # 3. Update LATEST_ANALYZED_VIDEOS session cache
        global LATEST_ANALYZED_VIDEOS
        LATEST_ANALYZED_VIDEOS = [metadata_a, metadata_b]
        logger.info("Successfully analyzed both videos and updated session cache.")
        
        return LATEST_ANALYZED_VIDEOS
        
    except ValueError as e:
        logger.error(f"Validation error during video analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during compare/analyze processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the video URLs: {str(e)}"
        )

@router.post("/chat")
def chat(payload: ChatRequest):
    """
    Accepts questions from the user about the analyzed videos.
    Invokes the retriever, comparisons, and answers LangGraph workflow, returning a streaming text response.
    """
    message = payload.message
    video_metadata = payload.video_metadata or LATEST_ANALYZED_VIDEOS
    
    if not video_metadata or len(video_metadata) < 2:
        logger.warning("Chat request made but no videos are currently in cache.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No analyzed videos found. Please analyze a YouTube video and an Instagram Reel first before asking questions."
        )
        
    try:
        logger.info(f"Invoking retrieval & analysis query pipeline for message: '{message}'")
        final_state = query_pipeline.invoke({
            "question": message,
            "video_metadata": video_metadata
        })
        response_text = final_state.get("response") or "No response was generated."
        
        # Word-by-word streaming generator for immediate responsiveness
        def event_generator():
            words = response_text.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield chunk
                time.sleep(0.015)  # 15ms delay per word for a fluid, natural flow
                
        return StreamingResponse(event_generator(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error in chat workflow execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )
