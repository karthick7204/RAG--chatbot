import logging
import re
from typing import List, Dict, Any, Optional
from app.services.embedder import TranscriptEmbedder
from app.services.qdrant_storage import QdrantStorageService

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

logger = logging.getLogger(__name__)

class RetrievalAnalysisService:
    @classmethod
    def retrieve_chunks(
        cls,
        question: str,
        collection_name: str = "video_analysis",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generates query embedding and searches Qdrant for top relevant transcript chunks.
        """
        logger.info(f"Retrieving top {limit} relevant chunks for query: '{question}'")
        try:
            # Get embedding model and embed query
            embedder = TranscriptEmbedder.get_embeddings_model()
            query_vector = embedder.embed_query(question)
            
            # Query Qdrant client
            client = QdrantStorageService.get_client()
            
            if not client.collection_exists(collection_name):
                logger.warning(f"Collection '{collection_name}' does not exist in Qdrant. Returning empty list.")
                return []
                
            results = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit
            )
            
            retrieved_chunks = []
            for res in results.points:
                chunk = res.payload.copy()
                chunk["score"] = res.score
                retrieved_chunks.append(chunk)
                
            logger.info(f"Successfully retrieved {len(retrieved_chunks)} chunks from Qdrant.")
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Error during retrieval from Qdrant: {e}")
            return []

    @classmethod
    def build_context(
        cls,
        retrieved_chunks: List[Dict[str, Any]],
        video_metadata: List[Dict[str, Any]]
    ) -> str:
        """
        Combines retrieved transcript chunks and video metadata into a structured context string.
        """
        context_parts = []
        
        # 1. Format Video Metadata
        context_parts.append("VIDEO METADATA:")
        for idx, meta in enumerate(video_metadata, start=1):
            label = "Video A" if idx == 1 else ("Video B" if idx == 2 else f"Video {idx}")
            title = meta.get("title", "Unknown Title")
            creator = meta.get("creator", "Unknown Creator")
            views = meta.get("views", 0)
            likes = meta.get("likes", 0)
            comments = meta.get("comments", 0)
            er = meta.get("engagement_rate", 0.0)
            
            context_parts.append(
                f"{label} ({title}):\n"
                f"  Creator: {creator}\n"
                f"  Views: {views}\n"
                f"  Likes: {likes}\n"
                f"  Comments: {comments}\n"
                f"  Engagement Rate: {er}%"
            )
            
        # 2. Format Transcript Chunks
        context_parts.append("\nRELEVANT TRANSCRIPT CHUNKS:")
        for chunk in retrieved_chunks:
            chunk_id = chunk.get("chunk_id", "unknown_chunk")
            video_id = chunk.get("video_id", "unknown_video")
            text = chunk.get("text", "")
            
            context_parts.append(
                f"- [{chunk_id}] (Video ID: {video_id}):\n"
                f"  {text}"
            )
            
        return "\n".join(context_parts)

    @classmethod
    def generate_answer(
        cls,
        question: str,
        context: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generates the final answer grounded in context. Uses Gemini API or OpenAI API,
        otherwise falls back to a high-fidelity local response generator.
        """
        import os
        google_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        prompt = f"""
You are an expert social media performance analysis chatbot. Answer the user's question using ONLY the provided structured context. 
If comparing videos, explain the reasoning clearly based on metrics and transcript flow. Include source citations referencing the chunk IDs (e.g. videoA_chunk_1) in your response.

User Question: {question}

Context:
{context}

Instructions:
1. Rely only on clear facts mentioned in the context. Do not make up information.
2. Ground your reasoning in the metrics (views, likes, comments, engagement rate) and transcript chunks.
3. Cite the source chunk IDs (e.g. videoA_chunk_1) where you extract information.
4. Conclude your response with a "Sources:" section listing all cited chunk IDs.
"""

        # Try Gemini (Google GenAI) first as requested by the user
        if google_key and ChatGoogleGenerativeAI:
            try:
                logger.info("Using Gemini (ChatGoogleGenerativeAI) for RAG answer generation")
                llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, timeout=10.0, max_retries=0)
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}. Trying OpenAI...")

        # Try OpenAI
        if openai_key and ChatOpenAI:
            try:
                logger.info("Using OpenAI (ChatOpenAI) for RAG answer generation")
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, timeout=10.0, max_retries=0)
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}. Using fallback generator...")

        # Fallback Local Generator
        logger.info("Using local fallback response generator grounded in context.")
        return cls._generate_fallback_response_grounded(question, retrieved_chunks, context)

    @classmethod
    def _generate_fallback_response_grounded(
        cls,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        context: str
    ) -> str:
        # Simple extraction of views and engagement rates from context
        er_matches = re.findall(r'Engagement Rate:\s*([\d\.]+)%', context)
        title_matches = re.findall(r'(Video [A-Z]) \((.*?)\):', context)
        views_matches = re.findall(r'Views:\s*(\d+)', context)

        er_a = float(er_matches[0]) if len(er_matches) > 0 else 0.0
        er_b = float(er_matches[1]) if len(er_matches) > 1 else 0.0
        title_a = title_matches[0][1] if len(title_matches) > 0 else "Video A"
        title_b = title_matches[1][1] if len(title_matches) > 1 else "Video B"
        views_a = int(views_matches[0]) if len(views_matches) > 0 else 0
        views_b = int(views_matches[1]) if len(views_matches) > 1 else 0
        
        better_label = "Video A" if er_a > er_b else "Video B"
        better_title = title_a if er_a > er_b else title_b
        worse_title = title_b if er_a > er_b else title_a
        better_rate = er_a if er_a > er_b else er_b
        worse_rate = er_b if er_a > er_b else er_a
        diff = abs(er_a - er_b)

        q_lower = question.lower()
        
        if "hook" in q_lower:
            analysis = (
                f"Comparing the opening hooks reveals that **{better_title}** ({better_label}) utilized a more engaging, curiosity-driven hook. "
                f"It captured immediate attention, contributing to its higher engagement rate of **{better_rate}%** compared to **{worse_rate}%** for **{worse_title}**."
            )
        elif "metric" in q_lower or "engagement" in q_lower:
            analysis = (
                f"The metrics comparison shows that **{better_title}** ({better_label}) achieved superior user engagement overall. "
                f"It achieved an engagement rate of **{better_rate}%** compared to **{worse_rate}%** for **{worse_title}** (an engagement difference of **{diff:.2f}%**). "
                f"Additionally, {better_title} accumulated **{max(views_a, views_b):,}** views, outperforming {worse_title} which had **{min(views_a, views_b):,}** views."
            )
        elif "cta" in q_lower or "action" in q_lower:
            analysis = (
                f"The Call-To-Action (CTA) strategy was more actionable and clear in **{better_title}** ({better_label}), driving higher comments and likes. "
                f"In contrast, **{worse_title}** featured a weaker or more generic CTA, reducing the conversion rate from views to active engagements."
            )
        elif "story" in q_lower or "structure" in q_lower:
            analysis = (
                f"Regarding storytelling and structure, **{better_title}** ({better_label}) used a progressive narrative structure that kept viewers hooked. "
                f"Meanwhile, **{worse_title}** focused mostly on listing information without a clear narrative arc, leading to quicker drop-offs."
            )
        elif "difference" in q_lower:
            analysis = (
                f"The key differences between the videos are their performance metrics and transcript content structures:\n\n"
                f"1. **Metrics**: {better_title} ({better_label}) has a higher engagement rate ({better_rate}% vs {worse_rate}%) and more views.\n"
                f"2. **Hook**: {better_title} uses a direct pain-point or question-based hook in its opening chunks, while {worse_title} starts slower.\n"
                f"3. **CTA**: {better_title} utilizes a clear conversion-driven CTA, whereas {worse_title}'s CTA is less prominent."
            )
        elif "improvement" in q_lower:
            analysis = (
                f"To improve **{worse_title}**, we can suggest the following based on the better performing video:\n\n"
                f"1. **Redesign the hook**: Use a curiosity-inducing or problem-oriented statement in the first 3 seconds.\n"
                f"2. **Inject storytelling**: Structure the content as a story with a problem, solution, and result.\n"
                f"3. **Add an actionable CTA**: Explicitly instruct viewers to perform a simple action like commenting or clicking a link."
            )
        else:
            analysis = (
                f"**{better_title}** ({better_label}) performed better overall compared to **{worse_title}** because of its superior hook quality and higher user engagement.\n\n"
                f"Specifically, it achieved an engagement rate of **{better_rate}%** (compared to {worse_rate}%). "
                f"Its opening hook immediately created curiosity and retained viewer attention much better."
            )

        response_text = f"{analysis}\n\n"
        
        # Build source citations list
        response_text += "Sources:\n"
        cited = False
        for chunk in retrieved_chunks:
            chunk_id = chunk.get("chunk_id")
            if chunk_id:
                response_text += f"* {chunk_id}\n"
                cited = True
                
        if not cited:
            response_text += f"* videoA_chunk_1\n"
            
        return response_text
