from typing import TypedDict, List, Dict, Any, Optional
import logging
from langgraph.graph import StateGraph, END
from app.services.extractor import MetadataExtractor
from app.services.transcriber import Transcriber
from app.services.chunker import TranscriptChunker
from app.services.embedder import TranscriptEmbedder
from app.services.qdrant_storage import QdrantStorageService
from app.services.retrieval_analysis import RetrievalAnalysisService

logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    """
    Represents the state of the LangGraph indexing workflow.
    """
    url: str
    metadata: Optional[Dict[str, Any]]
    transcript: Optional[str]
    word_count: Optional[int]
    language: Optional[str]
    chunks: Optional[List[Dict[str, Any]]]
    storage_stats: Optional[Dict[str, Any]]


class QueryState(TypedDict):
    """
    Represents the state of the LangGraph query retrieval and analysis workflow.
    """
    question: str
    video_metadata: List[Dict[str, Any]]
    collection_name: Optional[str]
    retrieved_chunks: Optional[List[Dict[str, Any]]]
    metrics_analysis: Optional[Dict[str, Any]]
    context: Optional[str]
    response: Optional[str]



def metadata_extraction_node(state: GraphState) -> Dict[str, Any]:
    """
    Extracts and normalizes metadata for the video URL.
    """
    url = state.get("url")
    if not url:
        raise ValueError("URL is required in GraphState for metadata extraction.")
        
    logger.info(f"[LangGraph Node] Extracting metadata for URL: {url}")
    metadata = MetadataExtractor.extract_metadata(url)
    return {"metadata": metadata}


def transcript_extraction_node(state: GraphState) -> Dict[str, Any]:
    """
    Extracts the full text transcript of the video (YouTube captions or Whisper fallback).
    """
    url = state.get("url")
    metadata = state.get("metadata") or {}
    if not url:
        raise ValueError("URL is required in GraphState for transcript extraction.")
        
    logger.info(f"[LangGraph Node] Extracting transcript for URL: {url}")
    transcript_data = Transcriber.extract_transcript(url, metadata)
    return {
        "transcript": transcript_data.get("transcript"),
        "word_count": transcript_data.get("word_count", 0),
        "language": transcript_data.get("language")
    }


def chunking_node(state: GraphState) -> Dict[str, Any]:
    """
    Splits the video transcript into overlapping chunks using the RecursiveCharacterTextSplitter
    and enriches each chunk with the video metadata.
    """
    transcript = state.get("transcript") or ""
    metadata = state.get("metadata") or {}
    
    logger.info(f"[LangGraph Node] Chunking transcript (size=1000, overlap=200)")
    chunks = TranscriptChunker.chunk_transcript(
        transcript=transcript,
        metadata=metadata,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    return {"chunks": chunks}


def embedding_generation_node(state: GraphState) -> Dict[str, Any]:
    """
    Generates vector embeddings for every transcript chunk and attaches them.
    Preserves all chunk metadata.
    """
    chunks = state.get("chunks") or []
    if not chunks:
        logger.warning("[LangGraph Node] No chunks found in GraphState to generate embeddings.")
        return {"chunks": []}
        
    logger.info(f"[LangGraph Node] Generating embeddings for {len(chunks)} chunks.")
    enriched_chunks = TranscriptEmbedder.embed_chunks(chunks)
    return {"chunks": enriched_chunks}


def qdrant_storage_node(state: GraphState) -> Dict[str, Any]:
    """
    Stores embedding-enriched chunks in the Qdrant vector database.
    """
    chunks = state.get("chunks") or []
    if not chunks:
        logger.warning("[LangGraph Node] No chunks found in GraphState to store in Qdrant.")
        return {
            "storage_stats": {
                "collection": "video_analysis",
                "stored_chunks": 0,
                "status": "success"
            }
        }
        
    logger.info(f"[LangGraph Node] Storing {len(chunks)} chunks in Qdrant.")
    stats = QdrantStorageService.store_chunks(chunks)
    return {"storage_stats": stats}
# ==========================================
# Graph Compilations
# ==========================================

# 1. Compile Indexing Pipeline
indexing_workflow = StateGraph(GraphState)
indexing_workflow.add_node("metadata_extraction", metadata_extraction_node)
indexing_workflow.add_node("transcript_extraction", transcript_extraction_node)
indexing_workflow.add_node("chunking", chunking_node)
indexing_workflow.add_node("embedding_generation", embedding_generation_node)
indexing_workflow.add_node("qdrant_storage", qdrant_storage_node)

indexing_workflow.set_entry_point("metadata_extraction")
indexing_workflow.add_edge("metadata_extraction", "transcript_extraction")
indexing_workflow.add_edge("transcript_extraction", "chunking")
indexing_workflow.add_edge("chunking", "embedding_generation")
indexing_workflow.add_edge("embedding_generation", "qdrant_storage")
indexing_workflow.add_edge("qdrant_storage", END)

indexing_pipeline = indexing_workflow.compile()


# ==========================================
# Retrieval & Analysis Phase Nodes
# ==========================================

def retriever_node(state: QueryState) -> Dict[str, Any]:
    """
    Retrieves top 5 relevant transcript chunks from Qdrant vector database.
    """
    question = state.get("question")
    collection_name = state.get("collection_name") or "video_analysis"
    
    logger.info(f"[LangGraph Node] Running Retriever Node for question: '{question}'")
    chunks = RetrievalAnalysisService.retrieve_chunks(question, collection_name=collection_name, limit=5)
    return {"retrieved_chunks": chunks}


def metrics_analysis_node(state: QueryState) -> Dict[str, Any]:
    """
    Calculates weighted performance scores and reach/engagement summaries.
    """
    video_metadata = state.get("video_metadata") or []
    logger.info(f"[LangGraph Node] Running Metrics Analysis Node for {len(video_metadata)} videos.")
    analysis = RetrievalAnalysisService.analyze_metrics(video_metadata)
    return {"metrics_analysis": analysis}


def comparison_node(state: QueryState) -> Dict[str, Any]:
    """
    Combines retrieved transcript chunks, video metadata, and metrics analysis into a unified context.
    """
    retrieved_chunks = state.get("retrieved_chunks") or []
    video_metadata = state.get("video_metadata") or []
    metrics_analysis = state.get("metrics_analysis") or {}
    
    logger.info(f"[LangGraph Node] Running Comparison Node (context builder) with {len(retrieved_chunks)} chunks.")
    context = RetrievalAnalysisService.build_context(retrieved_chunks, video_metadata, metrics_analysis)
    return {"context": context}


def context_builder_node(state: QueryState) -> Dict[str, Any]:
    """
    Wrapper node for backward compatibility in tests. Runs metrics_analysis and comparison nodes.
    """
    metrics_res = metrics_analysis_node(state)
    combined_state = {**state, **metrics_res}
    return comparison_node(combined_state)


def answer_generation_node(state: QueryState) -> Dict[str, Any]:
    """
    Generates the final answer using Gemini, OpenAI, or local fallback based on context.
    """
    question = state.get("question")
    context = state.get("context") or ""
    retrieved_chunks = state.get("retrieved_chunks") or []
    
    logger.info("[LangGraph Node] Running Answer Generation Node.")
    response = RetrievalAnalysisService.generate_answer(
        question=question,
        context=context,
        retrieved_chunks=retrieved_chunks
    )
    return {"response": response}


# 2. Compile Query Pipeline (Retrieval & Analysis)
query_workflow = StateGraph(QueryState)
query_workflow.add_node("retriever", retriever_node)
query_workflow.add_node("metrics_analysis", metrics_analysis_node)
query_workflow.add_node("comparison", comparison_node)
query_workflow.add_node("answer_generation", answer_generation_node)

query_workflow.set_entry_point("retriever")
query_workflow.add_edge("retriever", "metrics_analysis")
query_workflow.add_edge("metrics_analysis", "comparison")
query_workflow.add_edge("comparison", "answer_generation")
query_workflow.add_edge("answer_generation", END)

query_pipeline = query_workflow.compile()

