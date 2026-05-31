from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)

class TranscriptChunker:
    @classmethod
    def chunk_transcript(
        cls,
        transcript: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Splits the full transcript text into overlapping chunks and attaches video metadata to each.
        
        Args:
            transcript (str): The full transcript text.
            metadata (Dict[str, Any]): The video metadata dictionary.
            chunk_size (int): Max size of each text chunk. Defaults to 1000.
            chunk_overlap (int): Overlap size between adjacent chunks. Defaults to 200.
            
        Returns:
            List[Dict[str, Any]]: A list of chunk payloads, each containing chunk_id, chunk_index,
                                  text, video_id, and other metadata fields.
        """
        if not transcript:
            logger.warning("Empty transcript received for chunking.")
            return []
            
        # Get video ID
        video_id = metadata.get("video_id", "unknown_video")
        
        # Initialize text splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Split text
        text_chunks = splitter.split_text(transcript)
        logger.info(f"Split transcript into {len(text_chunks)} chunks using size={chunk_size}, overlap={chunk_overlap}")
        
        chunks = []
        for i, text in enumerate(text_chunks, start=1):
            chunk_id = f"{video_id}_chunk_{i}"
            
            # Create a flat dictionary containing chunk metadata and video metadata
            chunk_payload = {
                "chunk_id": chunk_id,
                "video_id": video_id,
                "chunk_index": i,
                "text": text
            }
            
            # Attach all other video metadata fields to the chunk
            for key, val in metadata.items():
                if key != "video_id":  # Avoid duplicate keys
                    chunk_payload[key] = val
                    
            chunks.append(chunk_payload)
            
        return chunks
