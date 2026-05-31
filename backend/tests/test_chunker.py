import unittest
from app.core.config import settings
# Force in-memory Qdrant for testing
settings.QDRANT_LOCATION = ":memory:"

from app.services.chunker import TranscriptChunker
from app.services.embedder import TranscriptEmbedder
from app.services.qdrant_storage import QdrantStorageService
from app.services.pipeline import (
    chunking_node,
    embedding_generation_node,
    qdrant_storage_node,
    retriever_node,
    answer_generation_node,
    GraphState,
    QueryState,
    query_pipeline
)
from app.services.retrieval_analysis import RetrievalAnalysisService


class TestChunker(unittest.TestCase):
    def setUp(self):
        # Clean client instance to ensure config overrides take effect
        QdrantStorageService._client_instance = None

    def test_chunker_basic(self):
        # Sample transcript and metadata
        transcript = (
            "This is a long transcript that needs to be split into chunks. "
            "We want to make sure that the character text splitter correctly splits "
            "this text into smaller pieces with overlap. "
            "Let's write enough text to verify that the chunking logic works, "
            "and that it attaches all the necessary metadata to each chunk. "
            "This is another sentence to add some length to our transcript. "
            "We are testing the chunker service which uses LangChain's RecursiveCharacterTextSplitter."
        )
        metadata = {
            "video_id": "test_video_123",
            "title": "Test Video Title",
            "creator": "Test Creator",
            "platform": "youtube"
        }
        
        # Test direct chunker call
        chunks = TranscriptChunker.chunk_transcript(
            transcript=transcript,
            metadata=metadata,
            chunk_size=100,  # Small chunk size to force multiple chunks
            chunk_overlap=20
        )
        
        # Verify chunks list is not empty
        self.assertTrue(len(chunks) > 1)
        
        # Verify chunk structure
        for i, chunk in enumerate(chunks, start=1):
            self.assertEqual(chunk["chunk_id"], f"test_video_123_chunk_{i}")
            self.assertEqual(chunk["video_id"], "test_video_123")
            self.assertEqual(chunk["chunk_index"], i)
            self.assertTrue("text" in chunk)
            self.assertEqual(chunk["title"], "Test Video Title")
            self.assertEqual(chunk["creator"], "Test Creator")
            self.assertEqual(chunk["platform"], "youtube")
            
    def test_chunking_node(self):
        transcript = "A short transcript for testing the node."
        metadata = {
            "video_id": "node_video_abc",
            "title": "Node Video"
        }
        
        state: GraphState = {
            "url": "https://youtube.com/watch?v=node_video_abc",
            "metadata": metadata,
            "transcript": transcript,
            "word_count": len(transcript.split()),
            "language": "en",
            "chunks": None,
            "storage_stats": None
        }
        
        result = chunking_node(state)
        
        # Verify results returned by node
        self.assertIn("chunks", result)
        chunks = result["chunks"]
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_id"], "node_video_abc_chunk_1")
        self.assertEqual(chunks[0]["video_id"], "node_video_abc")
        self.assertEqual(chunks[0]["chunk_index"], 1)
        self.assertEqual(chunks[0]["text"], transcript)
        self.assertEqual(chunks[0]["title"], "Node Video")

    def test_embedder_basic(self):
        chunks = [
            {
                "chunk_id": "videoA_chunk_1",
                "video_id": "videoA",
                "chunk_index": 1,
                "text": "This is the first chunk content for testing embedding generation."
            },
            {
                "chunk_id": "videoA_chunk_2",
                "video_id": "videoA",
                "chunk_index": 2,
                "text": "This is the second chunk content with metadata preservation test."
            }
        ]
        
        enriched_chunks = TranscriptEmbedder.embed_chunks(chunks)
        
        # Verify number of chunks and order is preserved
        self.assertEqual(len(enriched_chunks), 2)
        self.assertEqual(enriched_chunks[0]["chunk_id"], "videoA_chunk_1")
        self.assertEqual(enriched_chunks[1]["chunk_id"], "videoA_chunk_2")
        
        # Verify embeddings are generated and attached
        self.assertIn("embedding", enriched_chunks[0])
        self.assertIn("embedding", enriched_chunks[1])
        
        # Verify embedding type and length (bge-small-en-v1.5 has 384 dimensions)
        self.assertIsInstance(enriched_chunks[0]["embedding"], list)
        self.assertEqual(len(enriched_chunks[0]["embedding"]), 384)
        
        # Verify metadata is preserved
        self.assertEqual(enriched_chunks[0]["text"], "This is the first chunk content for testing embedding generation.")
        self.assertEqual(enriched_chunks[1]["text"], "This is the second chunk content with metadata preservation test.")

    def test_embedding_generation_node(self):
        chunks = [
            {
                "chunk_id": "videoB_chunk_1",
                "video_id": "videoB",
                "chunk_index": 1,
                "text": "LangGraph Embedding Generation Node test text."
            }
        ]
        
        state: GraphState = {
            "url": "https://youtube.com/watch?v=videoB",
            "metadata": {"video_id": "videoB"},
            "transcript": "LangGraph Embedding Generation Node test text.",
            "word_count": 6,
            "language": "en",
            "chunks": chunks,
            "storage_stats": None
        }
        
        result = embedding_generation_node(state)
        
        # Verify result contains the embedding-enriched chunks
        self.assertIn("chunks", result)
        enriched_chunks = result["chunks"]
        self.assertEqual(len(enriched_chunks), 1)
        self.assertEqual(enriched_chunks[0]["chunk_id"], "videoB_chunk_1")
        self.assertIn("embedding", enriched_chunks[0])
        self.assertEqual(len(enriched_chunks[0]["embedding"]), 384)
        
    def test_embedder_failure_handling(self):
        # Passing an invalid input to simulate error
        chunks = [
            {
                "chunk_id": "error_chunk",
                # missing text field to cause embed_documents or embed_query to raise exception
            }
        ]
        
        # Should not raise exception, should handle gracefully
        enriched_chunks = TranscriptEmbedder.embed_chunks(chunks)
        self.assertEqual(len(enriched_chunks), 1)
        self.assertIn("embedding", enriched_chunks[0])
        self.assertIsNone(enriched_chunks[0]["embedding"])

    def test_qdrant_storage_basic(self):
        chunks = [
            {
                "chunk_id": "videoQ_chunk_1",
                "video_id": "videoQ",
                "chunk_index": 1,
                "text": "Qdrant storage service unit test chunk.",
                "embedding": [0.1] * 384,
                "title": "Qdrant Unit Test",
                "creator": "Tester",
                "platform": "youtube",
                "engagement_rate": 3.14
            }
        ]
        
        collection_name = "test_video_analysis"
        stats = QdrantStorageService.store_chunks(chunks, collection_name=collection_name)
        
        # Verify stats output structure
        self.assertEqual(stats["collection"], collection_name)
        self.assertEqual(stats["stored_chunks"], 1)
        self.assertEqual(stats["status"], "success")
        
        # Fetch client and check that collection contains the point with correct metadata
        client = QdrantStorageService.get_client()
        self.assertTrue(client.collection_exists(collection_name))
        
        # Retrieve points (deterministic UUID format based on chunk_id)
        import uuid
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "videoQ_chunk_1"))
        records = client.retrieve(collection_name, [point_id])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, point_id)
        self.assertEqual(records[0].payload["chunk_id"], "videoQ_chunk_1")
        self.assertEqual(records[0].payload["video_id"], "videoQ")
        self.assertEqual(records[0].payload["title"], "Qdrant Unit Test")
        self.assertEqual(records[0].payload["creator"], "Tester")
        self.assertEqual(records[0].payload["engagement_rate"], 3.14)
        
    def test_qdrant_storage_node(self):
        chunks = [
            {
                "chunk_id": "videoQN_chunk_1",
                "video_id": "videoQN",
                "chunk_index": 1,
                "text": "Qdrant storage node unit test.",
                "embedding": [0.2] * 384
            }
        ]
        
        state: GraphState = {
            "url": "https://youtube.com/watch?v=videoQN",
            "metadata": {"video_id": "videoQN"},
            "transcript": "Qdrant storage node unit test.",
            "word_count": 5,
            "language": "en",
            "chunks": chunks,
            "storage_stats": None
        }
        
        result = qdrant_storage_node(state)
        
        # Verify node output
        self.assertIn("storage_stats", result)
        stats = result["storage_stats"]
        self.assertEqual(stats["collection"], "video_analysis")
        self.assertEqual(stats["stored_chunks"], 1)
        self.assertEqual(stats["status"], "success")
        
    def test_qdrant_storage_empty(self):
        result = qdrant_storage_node({"chunks": []})
        self.assertEqual(result["storage_stats"]["stored_chunks"], 0)
        self.assertEqual(result["storage_stats"]["status"], "success")
    def test_retrieval_and_analysis_service(self):
        # 1. Insert mock embedded chunks into Qdrant for retrieval testing
        collection_name = "test_retrieval_analysis"
        chunks = [
            {
                "chunk_id": "videoA_chunk_1",
                "video_id": "videoA",
                "chunk_index": 1,
                "text": "Stop scrolling and check out this amazing hack to scale your business!",
                "embedding": [0.15] * 384,
                "title": "Hack Video A",
                "creator": "Coach A",
                "platform": "instagram",
                "engagement_rate": 5.2,
                "views": 10000
            },
            {
                "chunk_id": "videoB_chunk_1",
                "video_id": "videoB",
                "chunk_index": 1,
                "text": "Welcome to my video today. I want to show you my home workspace tours.",
                "embedding": [0.05] * 384,
                "title": "Vlog Video B",
                "creator": "Vlogger B",
                "platform": "instagram",
                "engagement_rate": 2.1,
                "views": 5000
            }
        ]
        
        storage_stats = QdrantStorageService.store_chunks(chunks, collection_name=collection_name)
        self.assertEqual(storage_stats["status"], "success")
        
        # 2. Test retrieval service
        retrieved = RetrievalAnalysisService.retrieve_chunks(
            question="Why did Video A perform better?",
            collection_name=collection_name,
            limit=2
        )
        self.assertEqual(len(retrieved), 2)
        
        # 3. Test context builder service
        metadata = [
            {
                "video_id": "videoA",
                "title": "Hack Video A",
                "views": 10000,
                "likes": 500,
                "comments": 20,
                "engagement_rate": 5.20,
                "duration": 30,
                "followers": 15000
            },
            {
                "video_id": "videoB",
                "title": "Vlog Video B",
                "views": 5000,
                "likes": 100,
                "comments": 5,
                "engagement_rate": 2.10,
                "duration": 60,
                "followers": 8000
            }
        ]
        context = RetrievalAnalysisService.build_context(retrieved, metadata)
        self.assertIn("VIDEO METADATA:", context)
        self.assertIn("Hack Video A", context)
        self.assertIn("Vlog Video B", context)
        self.assertIn("RELEVANT TRANSCRIPT CHUNKS:", context)
        
        # 4. Test answer generator
        answer = RetrievalAnalysisService.generate_answer(
            question="Compare the hooks of these videos.",
            context=context,
            retrieved_chunks=retrieved
        )
        self.assertIn("Sources:", answer)
        self.assertTrue(any("videoA_chunk_1" in line or "videoB_chunk_1" in line for line in answer.split("\n")))

    def test_retrieval_and_analysis_nodes(self):
        # Insert mock data to video_analysis collection
        chunks = [
            {
                "chunk_id": "vidX_chunk_1",
                "video_id": "vidX",
                "chunk_index": 1,
                "text": "Stop scrolling! Here is the secret to scaling.",
                "embedding": [0.1] * 384
            }
        ]
        QdrantStorageService.store_chunks(chunks, collection_name="video_analysis")

        # Define state
        from app.services.pipeline import retriever_node, context_builder_node, answer_generation_node
        state: QueryState = {
            "question": "What is the hook?",
            "video_metadata": [
                {"video_id": "vidX", "title": "Vid X", "engagement_rate": 4.5},
                {"video_id": "vidY", "title": "Vid Y", "engagement_rate": 1.2}
            ],
            "collection_name": "video_analysis",
            "retrieved_chunks": None,
            "context": None,
            "response": None
        }

        # Run nodes individually
        ret_result = retriever_node(state)
        self.assertIn("retrieved_chunks", ret_result)
        state["retrieved_chunks"] = ret_result["retrieved_chunks"]
        
        context_result = context_builder_node(state)
        self.assertIn("context", context_result)
        state["context"] = context_result["context"]
        
        ans_result = answer_generation_node(state)
        self.assertIn("response", ans_result)
        self.assertIn("Sources:", ans_result["response"])

    def test_query_pipeline_integration(self):
        # Verify compiled pipeline compiles and runs successfully end-to-end
        from app.services.pipeline import query_pipeline
        
        # Seed collection
        chunks = [
            {
                "chunk_id": "vidA_chunk_1",
                "video_id": "vidA",
                "chunk_index": 1,
                "text": "Stop scrolling if you want to scale your engagement.",
                "embedding": [0.1] * 384
            }
        ]
        QdrantStorageService.store_chunks(chunks, collection_name="video_analysis")

        input_state = {
            "question": "Why did Video A perform better?",
            "video_metadata": [
                {"video_id": "vidA", "title": "Video A Title", "engagement_rate": 8.5},
                {"video_id": "vidB", "title": "Video B Title", "engagement_rate": 4.0}
            ]
        }

        # Invoke the compiled LangGraph workflow
        final_state = query_pipeline.invoke(input_state)
        
        # Assert workflow state transitions completed and final response populated
        self.assertIn("retrieved_chunks", final_state)
        self.assertIn("context", final_state)
        self.assertIn("response", final_state)
        self.assertIn("Sources:", final_state["response"])
        self.assertIn("vidA_chunk_1", final_state["response"])

if __name__ == "__main__":
    unittest.main()
