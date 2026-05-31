from typing import List, Dict, Any, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging

logger = logging.getLogger(__name__)

class TranscriptEmbedder:
    _embeddings_instance: Optional[HuggingFaceEmbeddings] = None

    @classmethod
    def get_embeddings_model(cls) -> HuggingFaceEmbeddings:
        """
        Loads the HuggingFace bge-small-en-v1.5 embedding model.
        Uses class-level caching to avoid reloading the model.
        """
        if cls._embeddings_instance is None:
            import torch
            logger.info("Setting PyTorch CPU thread limit to 2 to optimize inference and reduce overhead.")
            try:
                torch.set_num_threads(2)
            except Exception as torch_err:
                logger.warning(f"Could not set PyTorch thread limit: {torch_err}")
                
            logger.info("Initializing HuggingFaceEmbeddings model: BAAI/bge-small-en-v1.5")
            cls._embeddings_instance = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                model_kwargs={"device": "cpu"}
            )
        return cls._embeddings_instance

    @classmethod
    def embed_chunks(cls, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates vector embeddings for every transcript chunk.
        Preserves all chunk metadata and order, and attaches the embedding under 'embedding' key.
        
        Args:
            chunks (List[Dict[str, Any]]): The list of chunks.
            
        Returns:
            List[Dict[str, Any]]: List of chunks with 'embedding' field added.
        """
        if not chunks:
            logger.warning("Empty chunk list received for embedding generation.")
            return []

        try:
            texts = [chunk["text"] for chunk in chunks]
            logger.info(f"Generating embeddings for {len(chunks)} chunks in batch.")
            
            model = cls.get_embeddings_model()
            embeddings = model.embed_documents(texts)
            
            # Map embeddings back to chunks
            enriched_chunks = []
            for chunk, emb in zip(chunks, embeddings):
                enriched_chunk = chunk.copy()
                enriched_chunk["embedding"] = emb
                enriched_chunks.append(enriched_chunk)
                
            logger.info(f"Successfully generated embeddings for {len(enriched_chunks)} chunks.")
            return enriched_chunks
            
        except Exception as e:
            logger.error(f"Error during batch embedding generation: {e}")
            logger.info("Attempting fallback to individual chunk embedding...")
            
            try:
                model = cls.get_embeddings_model()
            except Exception as model_err:
                logger.error(f"Could not load embedding model: {model_err}")
                # Return chunks without embeddings if model load fails entirely
                for chunk in chunks:
                    if "embedding" not in chunk:
                        chunk["embedding"] = None
                return chunks
                
            enriched_chunks = []
            for chunk in chunks:
                enriched_chunk = chunk.copy()
                try:
                    emb = model.embed_query(chunk["text"])
                    enriched_chunk["embedding"] = emb
                except Exception as individual_err:
                    logger.error(f"Failed to embed chunk {chunk.get('chunk_id')}: {individual_err}")
                    enriched_chunk["embedding"] = None
                enriched_chunks.append(enriched_chunk)
                
            return enriched_chunks
