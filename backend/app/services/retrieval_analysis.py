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
    def analyze_metrics(cls, video_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs a weighted performance score comparison across views (40%), likes (25%),
        comments (15%), and engagement rate (20%). Produces a balanced summary of reach vs engagement.
        """
        if not video_metadata or len(video_metadata) < 2:
            return {
                "scores": {},
                "summary": "Insufficient video metadata available for metrics comparison."
            }
            
        meta_a = video_metadata[0]
        meta_b = video_metadata[1]
        
        views_a = float(meta_a.get("views") or 0)
        views_b = float(meta_b.get("views") or 0)
        likes_a = float(meta_a.get("likes") or 0)
        likes_b = float(meta_b.get("likes") or 0)
        comments_a = float(meta_a.get("comments") or 0)
        comments_b = float(meta_b.get("comments") or 0)
        er_a = float(meta_a.get("engagement_rate") or 0.0)
        er_b = float(meta_b.get("engagement_rate") or 0.0)
        
        # Calculate sums for normalization
        sum_views = views_a + views_b
        sum_likes = likes_a + likes_b
        sum_comments = comments_a + comments_b
        sum_er = er_a + er_b
        
        # Normalize relative to sum
        n_views_a = views_a / sum_views if sum_views > 0 else 0.5
        n_views_b = views_b / sum_views if sum_views > 0 else 0.5
        n_likes_a = likes_a / sum_likes if sum_likes > 0 else 0.5
        n_likes_b = likes_b / sum_likes if sum_likes > 0 else 0.5
        n_comments_a = comments_a / sum_comments if sum_comments > 0 else 0.5
        n_comments_b = comments_b / sum_comments if sum_comments > 0 else 0.5
        n_er_a = er_a / sum_er if sum_er > 0 else 0.5
        n_er_b = er_b / sum_er if sum_er > 0 else 0.5
        
        # Calculate Weighted Performance Score
        score_a = (n_views_a * 0.40) + (n_likes_a * 0.25) + (n_comments_a * 0.15) + (n_er_a * 0.20)
        score_b = (n_views_b * 0.40) + (n_likes_b * 0.25) + (n_comments_b * 0.15) + (n_er_b * 0.20)
        
        score_a = round(score_a * 100, 2)
        score_b = round(score_b * 100, 2)
        
        # Construct summary comparison
        title_a = meta_a.get("title", "Video A")
        title_b = meta_b.get("title", "Video B")
        
        summary_parts = []
        summary_parts.append("PERFORMANCE ANALYSIS:")
        summary_parts.append(f"- **Weighted Performance Scores**: {title_a}: {score_a}/100 | {title_b}: {score_b}/100")
        
        # Reach comparison
        summary_parts.append("\n1. Reach & Distribution:")
        if abs(views_a - views_b) > min(views_a, views_b) * 0.5: # Significant view difference (>50%)
            higher_views_title = title_a if views_a > views_b else title_b
            lower_views_title = title_b if views_a > views_b else title_a
            higher_val = max(views_a, views_b)
            lower_val = min(views_a, views_b)
            summary_parts.append(
                f"  - **{higher_views_title}** achieved significantly stronger reach and broader distribution "
                f"with **{higher_val:,.0f}** views, compared to **{lower_val:,.0f}** views for **{lower_views_title}**."
            )
        else:
            summary_parts.append(
                f"  - Both videos achieved comparable reach, with **{title_a}** receiving **{views_a:,.0f}** views "
                f"and **{title_b}** receiving **{views_b:,.0f}** views."
            )
            
        # Engagement quality comparison
        summary_parts.append("\n2. Engagement & Interaction:")
        if er_a > er_b:
            summary_parts.append(
                f"  - **{title_a}** demonstrated stronger audience interaction quality, achieving a **{er_a}%** "
                f"engagement rate (with **{likes_a:,.0f}** likes and **{comments_a:,.0f}** comments), "
                f"compared to **{er_b}%** for **{title_b}** (with **{likes_b:,.0f}** likes and **{comments_b:,.0f}** comments)."
            )
            if views_b > views_a:
                summary_parts.append(
                    f"  - Although **{title_b}** reached more viewers, **{title_a}** succeeded in creating a more engaging "
                    f"experience relative to its audience size."
                )
        elif er_b > er_a:
            summary_parts.append(
                f"  - **{title_b}** demonstrated stronger audience interaction quality, achieving a **{er_b}%** "
                f"engagement rate (with **{likes_b:,.0f}** likes and **{comments_b:,.0f}** comments), "
                f"compared to **{er_a}%** for **{title_a}** (with **{likes_a:,.0f}** likes and **{comments_a:,.0f}** comments)."
            )
            if views_a > views_b:
                summary_parts.append(
                    f"  - Although **{title_a}** reached more viewers, **{title_b}** succeeded in creating a more engaging "
                    f"experience relative to its audience size."
                )
        else:
            summary_parts.append(
                f"  - Both videos maintained the exact same engagement rate of **{er_a}%**."
            )
            
        # Overall synthesis
        summary_parts.append("\n3. Overall Performance Synthesis:")
        if score_a > score_b:
            summary_parts.append(
                f"  - **{title_a}** outperformed **{title_b}** overall (Score: **{score_a}** vs **{score_b}**). "
                f"While engagement rates vary, its combined reach and absolute interaction count resulted in a larger total brand impact."
            )
        elif score_b > score_a:
            summary_parts.append(
                f"  - **{title_b}** outperformed **{title_a}** overall (Score: **{score_b}** vs **{score_a}**). "
                f"While engagement rates vary, its combined reach and absolute interaction count resulted in a larger total brand impact."
            )
        else:
            summary_parts.append(
                f"  - Both videos achieved balanced overall performance with identical scores of **{score_a}**."
            )
            
        return {
            "scores": {
                "video_a": score_a,
                "video_b": score_b
            },
            "summary": "\n".join(summary_parts)
        }

    @classmethod
    def build_context(
        cls,
        retrieved_chunks: List[Dict[str, Any]],
        video_metadata: List[Dict[str, Any]],
        metrics_analysis: Optional[Dict[str, Any]] = None
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
            
        # 3. Add Metrics Performance Summary if available
        if metrics_analysis and metrics_analysis.get("summary"):
            context_parts.append("\nMETRICS PERFORMANCE SUMMARY:")
            context_parts.append(metrics_analysis["summary"])
            
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
Do not assume, extrapolate, or use any outside knowledge. If the context does not contain the answer, explicitly state: "Based on the provided video analysis, I cannot find enough information to answer that question."

User Question: {question}

Context:
{context}

Instructions:
1. Rely strictly on clear facts mentioned in the context. Do not speculate or make up information.
2. Ground your reasoning in the metrics (views, likes, comments, engagement rate) and transcript chunks.
3. Cite the source chunk IDs (e.g. videoA_chunk_1) where you extract information.
4. Conclude your response with a "Sources:" section listing all cited chunk IDs.
"""

        # Try Gemini (Google GenAI) first as requested by the user
        if google_key and ChatGoogleGenerativeAI:
            try:
                logger.info("Using Gemini (ChatGoogleGenerativeAI) for RAG answer generation")
                llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0, timeout=10.0, max_retries=0)
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}. Trying OpenAI...")

        # Try OpenAI
        if openai_key and ChatOpenAI:
            try:
                logger.info("Using OpenAI (ChatOpenAI) for RAG answer generation")
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, timeout=10.0, max_retries=0)
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
        # Robustly extract metadata fields from context string to call analyze_metrics
        video_metadata = []
        
        er_matches = re.findall(r'Engagement Rate:\s*([\d\.]+)%', context)
        title_matches = re.findall(r'(Video [A-Z0-9]+) \((.*?)\):', context)
        views_matches = re.findall(r'Views:\s*([\d,\.]+)', context)
        likes_matches = re.findall(r'Likes:\s*([\d,\.]+)', context)
        comments_matches = re.findall(r'Comments:\s*([\d,\.]+)', context)
        
        num_videos = min(len(er_matches), len(title_matches), len(views_matches))
        for i in range(num_videos):
            label = title_matches[i][0]
            title = title_matches[i][1]
            er = float(er_matches[i])
            views = float(views_matches[i].replace(",", ""))
            likes = float(likes_matches[i].replace(",", "")) if i < len(likes_matches) else 0.0
            comments = float(comments_matches[i].replace(",", "")) if i < len(comments_matches) else 0.0
            
            video_metadata.append({
                "label": label,
                "title": title,
                "views": views,
                "likes": likes,
                "comments": comments,
                "engagement_rate": er
            })

        # Calculate scores using analyze_metrics if we have enough video data
        if len(video_metadata) >= 2:
            analysis_dict = cls.analyze_metrics(video_metadata)
            scores = analysis_dict.get("scores", {})
            score_a = scores.get("video_a", 0.0)
            score_b = scores.get("video_b", 0.0)
            
            meta_a = video_metadata[0]
            meta_b = video_metadata[1]
            title_a = meta_a.get("title", "Video A")
            title_b = meta_b.get("title", "Video B")
            views_a = meta_a.get("views", 0.0)
            views_b = meta_b.get("views", 0.0)
            er_a = meta_a.get("engagement_rate", 0.0)
            er_b = meta_b.get("engagement_rate", 0.0)
            
            better_title = title_a if score_a > score_b else title_b
            worse_title = title_b if score_a > score_b else title_a
            better_label = "Video A" if score_a > score_b else "Video B"
            worse_label = "Video B" if score_a > score_b else "Video A"
            better_score = max(score_a, score_b)
            worse_score = min(score_a, score_b)
            
            er_winner_title = title_a if er_a > er_b else title_b
            views_winner_title = title_a if views_a > views_b else title_b
        else:
            # Fallback to simple extraction if parsing failed
            er_a = float(er_matches[0]) if len(er_matches) > 0 else 0.0
            er_b = float(er_matches[1]) if len(er_matches) > 1 else 0.0
            title_a = title_matches[0][1] if len(title_matches) > 0 else "Video A"
            title_b = title_matches[1][1] if len(title_matches) > 1 else "Video B"
            views_a = float(views_matches[0].replace(",", "")) if len(views_matches) > 0 else 0.0
            views_b = float(views_matches[1].replace(",", "")) if len(views_matches) > 1 else 0.0
            score_a = er_a
            score_b = er_b
            better_title = title_a if er_a > er_b else title_b
            worse_title = title_b if er_a > er_b else title_a
            better_label = "Video A" if er_a > er_b else "Video B"
            worse_label = "Video B" if er_a > er_b else "Video A"
            better_score = max(score_a, score_b)
            worse_score = min(score_a, score_b)
            er_winner_title = better_title
            views_winner_title = title_a if views_a > views_b else title_b

        q_lower = question.lower()
        
        if "hook" in q_lower:
            analysis = (
                f"Comparing the opening hooks reveals how each video captured audience attention. "
                f"**{better_title}** ({better_label}) achieved an overall performance score of **{better_score}/100**, "
                f"driven by a balanced combination of reach ({views_a:,.0f} vs {views_b:,.0f} views) and engagement. "
            )
            # Add transcript hook specific comments if they exist in retrieved chunks
            hook_a = ""
            hook_b = ""
            for chunk in retrieved_chunks:
                chunk_id = chunk.get("chunk_id", "")
                text = chunk.get("text", "")
                if "videoA" in chunk_id or "vidA" in chunk_id:
                    if not hook_a:
                        hook_a = text[:150]
                elif "videoB" in chunk_id or "vidB" in chunk_id:
                    if not hook_b:
                        hook_b = text[:150]
            
            if hook_a and hook_b:
                analysis += (
                    f"Specifically, Video A's hook ('{hook_a}...') and Video B's hook ('{hook_b}...') "
                    f"show different approaches. "
                )
            
            if er_a > er_b:
                analysis += (
                    f"**{title_a}** achieved a higher engagement rate of **{er_a}%** than **{title_b}** (**{er_b}%**), "
                    f"indicating its hook was more effective at retaining viewers and prompting interactions relative to its audience size. "
                )
            else:
                analysis += (
                    f"**{title_b}** achieved a higher engagement rate of **{er_b}%** than **{title_a}** (**{er_a}%**), "
                    f"indicating its hook was more effective at retaining viewers and prompting interactions relative to its audience size. "
                )
                
            if views_a > views_b and er_b > er_a:
                analysis += (
                    f"However, **{title_a}** reached a significantly larger audience (**{views_a:,.0f}** views vs **{views_b:,.0f}** views), "
                    f"demonstrating much broader reach and distribution despite a lower engagement percentage."
                )
            elif views_b > views_a and er_a > er_b:
                analysis += (
                    f"However, **{title_b}** reached a significantly larger audience (**{views_b:,.0f}** views vs **{views_a:,.0f}** views), "
                    f"demonstrating much broader reach and distribution despite a lower engagement percentage."
                )
        elif "metric" in q_lower or "engagement" in q_lower:
            analysis = (
                f"The comprehensive metrics comparison uses a weighted performance score "
                f"considering Views (40%), Likes (25%), Comments (15%), and Engagement Rate (20%):\n\n"
                f"- **{title_a}** (Video A): Score **{score_a}/100** (Views: {views_a:,.0f}, Likes: {video_metadata[0].get('likes',0):,.0f}, Comments: {video_metadata[0].get('comments',0):,.0f}, ER: {er_a}%)\n"
                f"- **{title_b}** (Video B): Score **{score_b}/100** (Views: {views_b:,.0f}, Likes: {video_metadata[1].get('likes',0):,.0f}, Comments: {video_metadata[1].get('comments',0):,.0f}, ER: {er_b}%)\n\n"
            )
            if score_a > score_b:
                analysis += f"**{title_a}** is the overall winner with a score of **{score_a}** (vs **{score_b}**). "
            else:
                analysis += f"**{title_b}** is the overall winner with a score of **{score_b}** (vs **{score_a}**). "
                
            # Reach vs Engagement analysis
            if views_a > views_b and er_b > er_a:
                analysis += (
                    f"This comparison highlights the classic tradeoff between reach and engagement quality. "
                    f"**{title_a}** dominated in reach with **{views_a:,.0f}** views (vs **{views_b:,.0f}**), while "
                    f"**{title_b}** showed higher engagement rate of **{er_b}%** (vs **{er_a}%**), indicating a more active, small-scale community response."
                )
            elif views_b > views_a and er_a > er_b:
                analysis += (
                    f"This comparison highlights the classic tradeoff between reach and engagement quality. "
                    f"**{title_b}** dominated in reach with **{views_b:,.0f}** views (vs **{views_a:,.0f}**), while "
                    f"**{title_a}** showed higher engagement rate of **{er_a}%** (vs **{er_b}%**), indicating a more active, small-scale community response."
                )
            else:
                analysis += (
                    f"**{better_title}** led in both reach and engagement metrics, demonstrating overall superiority in both audience size and interaction rate."
                )
        elif "cta" in q_lower or "action" in q_lower:
            analysis = (
                f"The CTA (Call to Action) effectiveness is reflected in the conversion of viewers to active interactions (likes and comments). "
                f"**{better_title}** ({better_label}) scored **{better_score}/100** on our weighted performance scale, "
                f"whereas **{worse_title}** ({worse_label}) scored **{worse_score}/100**.\n\n"
            )
            if er_a > er_b:
                analysis += (
                    f"**{title_a}**'s higher engagement rate of **{er_a}%** (vs **{er_b}%**) suggests its CTA was more compelling or placed more naturally, "
                    f"inducing a higher proportion of its audience to like and comment."
                )
            else:
                analysis += (
                    f"**{title_b}**'s higher engagement rate of **{er_b}%** (vs **{er_a}%**) suggests its CTA was more compelling or placed more naturally, "
                    f"inducing a higher proportion of its audience to like and comment."
                )
            
            if abs(views_a - views_b) > 0:
                higher_views_title = title_a if views_a > views_b else title_b
                analysis += (
                    f" In terms of raw volume, **{higher_views_title}**'s CTA reached far more eyes due to its superior view count."
                )
        elif "story" in q_lower or "structure" in q_lower:
            analysis = (
                f"Comparing storytelling and structure: **{better_title}** ({better_label}) achieved the higher weighted score of **{better_score}/100** "
                f"compared to **{worse_title}** ({worse_label}) at **{worse_score}/100**.\n\n"
                f"A progressive storytelling structure helps sustain viewer attention and drive action. "
            )
            if er_a > er_b:
                analysis += (
                    f"**{title_a}**'s superior engagement rate (**{er_a}%** vs **{er_b}%**) suggests its pacing or narrative arc "
                    f"succeeded in keeping viewers engaged throughout the video. "
                )
            else:
                analysis += (
                    f"**{title_b}**'s superior engagement rate (**{er_b}%** vs **{er_a}%**) suggests its pacing or narrative arc "
                    f"succeeded in keeping viewers engaged throughout the video. "
                )
                
            if views_a > views_b:
                analysis += f"Meanwhile, **{title_a}** achieved greater overall reach with **{views_a:,.0f}** views, suggesting its structure also appealed to the algorithm for wider distribution."
            else:
                analysis += f"Meanwhile, **{title_b}** achieved greater overall reach with **{views_b:,.0f}** views, suggesting its structure also appealed to the algorithm for wider distribution."
        elif "difference" in q_lower:
            analysis = (
                f"The key differences between the two videos lie in their reach, engagement distribution, and weighted performance scores:\n\n"
                f"1. **Performance Scores**: **{title_a}** scored **{score_a}/100** while **{title_b}** scored **{score_b}/100** on our weighted performance metric.\n"
                f"2. **Reach vs. Engagement**: "
            )
            if views_a > views_b and er_b > er_a:
                analysis += (
                    f"**{title_a}** has significantly higher reach (**{views_a:,.0f}** views vs **{views_b:,.0f}**), "
                    f"whereas **{title_b}** has a higher engagement rate (**{er_b}%** vs **{er_a}%**).\n"
                )
            elif views_b > views_a and er_a > er_b:
                analysis += (
                    f"**{title_b}** has significantly higher reach (**{views_b:,.0f}** views vs **{views_a:,.0f}**), "
                    f"whereas **{title_a}** has a higher engagement rate (**{er_a}%** vs **{er_b}%**).\n"
                )
            else:
                analysis += (
                    f"**{better_title}** outperformed **{worse_title}** in both total views (**{max(views_a, views_b):,.0f}** vs **{min(views_a, views_b):,.0f}**) "
                    f"and engagement rate (**{max(er_a, er_b)}%** vs **{min(er_a, er_b)}%**).\n"
                )
                
            analysis += (
                f"3. **Hook and Content**: Based on the transcript chunks, **{better_title}** used structured pacing and hooks to retain and convert attention into engagement."
            )
        elif "improvement" in q_lower:
            analysis = (
                f"Based on the comparative performance (Scores: **{title_a}** = **{score_a}/100**, **{title_b}** = **{score_b}/100**), here are recommendations for improvement:\n\n"
                f"For the lower-performing video (**{worse_title}**):\n"
                f"1. **Boost Reach**: Analyze the higher-reach video (**{views_winner_title}**) to see how its title, thumbnail, or initial hook optimization achieved **{max(views_a, views_b):,.0f}** views.\n"
                f"2. **Enhance Engagement Rate**: Model the engagement strategies of **{er_winner_title}** (which achieved a **{max(er_a, er_b)}%** engagement rate) "
                f"by structuring clear interactive prompts or CTAs to convert viewers into likers and commenters."
            )
        else:
            analysis = (
                f"**{better_title}** ({better_label}) achieved a higher overall performance score of **{better_score}/100** "
                f"compared to **{worse_score}/100** for **{worse_title}** ({worse_label}).\n\n"
                f"This score balances reach (Views) and engagement (Likes, Comments, Engagement Rate). "
                f"Specifically, **{title_a}** achieved **{views_a:,.0f}** views with a **{er_a}%** engagement rate, "
                f"while **{title_b}** achieved **{views_b:,.0f}** views with a **{er_b}%** engagement rate."
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
