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
        
        # Extract video IDs
        from app.services.extractor import MetadataExtractor
        from app.services.qdrant_storage import QdrantStorageService
        
        id_yt = ""
        id_insta = ""
        
        try:
            if "youtube.com" in payload.youtube_url or "youtu.be" in payload.youtube_url:
                id_yt = MetadataExtractor.extract_youtube_id(payload.youtube_url)
        except Exception as e:
            logger.warning(f"Could not parse YouTube ID from URL: {e}")
            
        try:
            if "instagram.com" in payload.instagram_url:
                id_insta = MetadataExtractor.extract_instagram_shortcode(payload.instagram_url)
        except Exception as e:
            logger.warning(f"Could not parse Instagram shortcode from URL: {e}")
            
        # Check cache
        metadata_a = QdrantStorageService.check_video_exists(id_yt) if id_yt else None
        metadata_b = QdrantStorageService.check_video_exists(id_insta) if id_insta else None
        
        # Only run indexing pipeline for videos not found in cache
        tasks_to_run = {}
        if not metadata_a:
            logger.info(f"YouTube video {id_yt} not in cache. Indexing...")
            tasks_to_run["youtube"] = payload.youtube_url
        else:
            logger.info(f"YouTube video {id_yt} found in Qdrant cache.")
            
        if not metadata_b:
            logger.info(f"Instagram Reel {id_insta} not in cache. Indexing...")
            tasks_to_run["instagram"] = payload.instagram_url
        else:
            logger.info(f"Instagram Reel {id_insta} found in Qdrant cache.")
            
        if tasks_to_run:
            from concurrent.futures import ThreadPoolExecutor
            logger.info(f"Running indexing pipelines in parallel for {list(tasks_to_run.keys())}")
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {}
                for key, url in tasks_to_run.items():
                    futures[key] = executor.submit(indexing_pipeline.invoke, {"url": url})
                
                if "youtube" in futures:
                    state_a = futures["youtube"].result()
                    metadata_a = state_a.get("metadata")
                    if not metadata_a:
                        raise ValueError(f"Failed to retrieve metadata for YouTube URL: {payload.youtube_url}")
                        
                if "instagram" in futures:
                    state_b = futures["instagram"].result()
                    metadata_b = state_b.get("metadata")
                    if not metadata_b:
                        raise ValueError(f"Failed to retrieve metadata for Instagram Reel URL: {payload.instagram_url}")
            
        # 3. Update LATEST_ANALYZED_VIDEOS session cache
        global LATEST_ANALYZED_VIDEOS
        LATEST_ANALYZED_VIDEOS = [metadata_a, metadata_b]
        logger.info("Successfully analyzed both videos concurrently and updated session cache.")
        
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
