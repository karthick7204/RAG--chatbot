import logging
from typing import List, Dict, Any, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings

logger = logging.getLogger(__name__)

class QdrantStorageService:
    _client_instance: Optional[QdrantClient] = None

    @classmethod
    def get_client(cls) -> QdrantClient:
        """
        Initializes and returns a singleton QdrantClient with graceful fallback.
        """
        if cls._client_instance is not None:
            return cls._client_instance

        try:
            if settings.QDRANT_LOCATION:
                logger.info(f"Connecting to Qdrant at location: {settings.QDRANT_LOCATION}")
                cls._client_instance = QdrantClient(location=settings.QDRANT_LOCATION)
            elif settings.QDRANT_HOST:
                logger.info(f"Connecting to Qdrant host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
                cls._client_instance = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=5.0
                )
                # Verify connection
                cls._client_instance.get_collections()
            elif settings.QDRANT_PATH:
                logger.info(f"Using local persistent Qdrant at path: {settings.QDRANT_PATH}")
                cls._client_instance = QdrantClient(path=settings.QDRANT_PATH)
            else:
                raise ValueError("No configuration provided.")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant using primary config: {e}. Falling back to local persistent storage.")
            try:
                cls._client_instance = QdrantClient(path="qdrant_db")
            except Exception as fallback_err:
                logger.error(f"Failed to fallback to local persistent Qdrant: {fallback_err}. Falling back to in-memory.")
                cls._client_instance = QdrantClient(location=":memory:")

        return cls._client_instance

    @classmethod
    def store_chunks(
        cls,
        chunks: List[Dict[str, Any]],
        collection_name: str = "video_analysis"
    ) -> Dict[str, Any]:
        """
        Stores transcript chunks in a Qdrant collection.
        Automatically creates the collection if it doesn't exist.
        Avoids duplicates, uses batch insertion, and returns statistics.
        
        Args:
            chunks (List[Dict[str, Any]]): The list of embedded chunks.
            collection_name (str): The name of the collection. Defaults to 'video_analysis'.
            
        Returns:
            Dict[str, Any]: Statistics of the storage operation.
        """
        if not chunks:
            logger.warning("No chunks provided to store in Qdrant.")
            return {
                "collection": collection_name,
                "stored_chunks": 0,
                "status": "success"
            }

        try:
            client = cls.get_client()
            
            # Find vector size dynamically from the first chunk with a valid embedding
            vector_size = None
            for chunk in chunks:
                if chunk.get("embedding"):
                    vector_size = len(chunk["embedding"])
                    break
            
            if vector_size is None:
                raise ValueError("No valid embeddings found in the chunks to determine vector size.")

            # Check if collection exists
            exists = False
            try:
                exists = client.collection_exists(collection_name)
            except Exception as collection_err:
                logger.warning(f"Could not check collection existence: {collection_err}. Attempting creation directly.")

            if not exists:
                logger.info(f"Creating Qdrant collection '{collection_name}' with vector size {vector_size}")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )

            # Build Qdrant points
            points = []
            stored_count = 0
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id")
                embedding = chunk.get("embedding")
                
                if not chunk_id or not embedding:
                    logger.warning(f"Skipping chunk due to missing chunk_id or embedding: {chunk}")
                    continue

                # Generate a deterministic UUID from chunk_id
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
                
                # Payload: all keys except the embedding vector itself
                payload = {k: v for k, v in chunk.items() if k != "embedding"}
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
                stored_count += 1

            if points:
                logger.info(f"Batch upserting {len(points)} points into collection '{collection_name}'")
                client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                logger.info(f"Successfully stored {len(points)} chunks in collection '{collection_name}'")
                
            return {
                "collection": collection_name,
                "stored_chunks": stored_count,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to store chunks in Qdrant: {e}")
            return {
                "collection": collection_name,
                "stored_chunks": 0,
                "status": f"failed: {str(e)}"
            }
