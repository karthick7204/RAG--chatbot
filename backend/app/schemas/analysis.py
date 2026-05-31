from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CompareRequest(BaseModel):
    youtube_url: str = Field(..., description="The YouTube video URL")
    instagram_url: str = Field(..., description="The Instagram Reel URL")

class VideoMetadataRequest(BaseModel):

    url: str = Field(..., description="The YouTube or Instagram Reel URL")

class VideoMetadataResponse(BaseModel):
    platform: str = Field(..., description="The platform, either 'youtube' or 'instagram'")
    video_id: str = Field(..., description="The unique identifier of the video")
    title: str = Field(..., description="The title of the video")
    creator: str = Field(..., description="The name of the video creator")
    followers: Optional[int] = Field(0, description="The subscriber/follower count of the creator")
    views: Optional[int] = Field(0, description="Total views")
    likes: Optional[int] = Field(0, description="Total likes")
    comments: Optional[int] = Field(0, description="Total comments")
    duration: Optional[int] = Field(0, description="Duration in seconds")
    upload_date: Optional[str] = Field(None, description="The upload date (YYYY-MM-DD)")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags associated with the video")
    description: Optional[str] = Field(None, description="Video description or caption")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    engagement_rate: Optional[float] = Field(0.0, description="Calculated engagement rate percentage")
    transcript: Optional[str] = Field(None, description="The cleaned full transcript of the video")
    word_count: Optional[int] = Field(0, description="Total word count of the transcript")
    language: Optional[str] = Field(None, description="Detected or fetched language code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "platform": "youtube",
                "video_id": "abc12345",
                "title": "AI-Powered Video Performance Analysis Assistant Tutorial",
                "creator": "TechGuru",
                "followers": 150000,
                "views": 25000,
                "likes": 1200,
                "comments": 150,
                "duration": 345,
                "upload_date": "2026-05-15",
                "hashtags": ["#AI", "#FastAPI", "#NextJS"],
                "description": "Learn how to build an AI agent for video analysis.",
                "thumbnail": "https://img.youtube.com/vi/abc12345/0.jpg",
                "engagement_rate": 5.4,
                "transcript": "Welcome back to another video. Today we are talking about creating highly engaging short form videos...",
                "word_count": 14,
                "language": "en"
            }
        }
    }

class ChatRequest(BaseModel):
    message: str = Field(..., description="The chat message / question")
    video_metadata: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional metadata list of videos being compared")

