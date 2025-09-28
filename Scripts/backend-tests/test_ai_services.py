"""
Tests for AI services including multi-provider AI, embeddings, and RAG operations
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any

# Mock external dependencies
with patch.dict('sys.modules', {
    'openai': MagicMock(),
    'anthropic': MagicMock(),
    'google.generativeai': MagicMock(),
    'sentence_transformers': MagicMock(),
}):
    from python.src.server.services.llm_provider_service import LLMProviderService
    from python.src.server.services.embeddings.embedding_service import EmbeddingService
    from python.src.server.services.search.rag_service import RAGService

class TestLLMProviderService:
    """Test suite for LLM provider operations."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Anthropic response"
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 30
        mock_client.messages.create.return_value = mock_response
        return mock_client

    def test_openai_provider_initialization(self):
        """Test OpenAI provider setup."""
        with patch('python.src.server.services.llm_provider_service.OpenAI', return_value=MagicMock()):
            service = LLMProviderService()
            assert service.providers['openai'] is not None

    def test_anthropic_provider_initialization(self):
        """Test Anthropic provider setup."""
        with patch('python.src.server.services.llm_provider_service.Anthropic', return_value=MagicMock()):
            service = LLMProviderService()
            assert service.providers['anthropic'] is not None

    def test_generate_with_openai(self, mock_openai_client):
        """Test text generation with OpenAI."""
        with patch('python.src.server.services.llm_provider_service.OpenAI', return_value=mock_openai_client):
            service = LLMProviderService()
            result = service.generate_text("Test prompt", provider="openai", model="gpt-4")

            assert result["content"] == "Test response"
            assert result["provider"] == "openai"
            assert result["tokens_used"] == 100

    def test_generate_with_anthropic(self, mock_anthropic_client):
        """Test text generation with Anthropic."""
        with patch('python.src.server.services.llm_provider_service.Anthropic', return_value=mock_anthropic_client):
            service = LLMProviderService()
            result = service.generate_text("Test prompt", provider="anthropic", model="claude-3")

            assert result["content"] == "Anthropic response"
            assert result["provider"] == "anthropic"
            assert result["tokens_used"] == 80  # 50 + 30

    def test_provider_fallback(self):
        """Test automatic fallback when primary provider fails."""
        with patch('python.src.server.services.llm_provider_service.OpenAI') as mock_openai:
            # Make OpenAI fail
            mock_openai_instance = MagicMock()
            mock_openai_instance.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_openai_instance

            # Set up Anthropic as fallback
            with patch('python.src.server.services.llm_provider_service.Anthropic') as mock_anthropic:
                mock_anthropic_instance = MagicMock()
                mock_response = MagicMock()
                mock_response.content = [MagicMock()]
                mock_response.content[0].text = "Fallback response"
                mock_anthropic_instance.messages.create.return_value = mock_response
                mock_anthropic.return_value = mock_anthropic_instance

                service = LLMProviderService()
                result = service.generate_with_fallback("Test prompt", primary_provider="openai")

                assert result["content"] == "Fallback response"
                assert result["provider"] == "anthropic"
                assert result["fallback_used"] is True

    def test_token_limit_handling(self):
        """Test handling of token limits."""
        with patch('python.src.server.services.llm_provider_service.OpenAI') as mock_openai:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Short response"
            mock_response.usage.total_tokens = 10
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance

            service = LLMProviderService()

            # Test with max_tokens parameter
            result = service.generate_text("Test", provider="openai", max_tokens=50)
            assert result["content"] == "Short response"
            assert result["tokens_used"] == 10

    def test_model_validation(self):
        """Test model availability and validation."""
        service = LLMProviderService()

        # Test valid model
        assert service.is_model_available("openai", "gpt-4")

        # Test invalid model
        assert not service.is_model_available("openai", "invalid-model")

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        with patch('python.src.server.services.llm_provider_service.OpenAI') as mock_openai:
            mock_instance = MagicMock()
            # Simulate rate limit error
            mock_instance.chat.completions.create.side_effect = Exception("Rate limit exceeded")
            mock_openai.return_value = mock_instance

            service = LLMProviderService()

            with pytest.raises(Exception, match="Rate limit exceeded"):
                service.generate_text("Test prompt", provider="openai")

    def test_cost_calculation(self):
        """Test cost calculation for different providers."""
        service = LLMProviderService()

        # Test OpenAI cost calculation
        openai_cost = service.calculate_cost("openai", "gpt-4", input_tokens=1000, output_tokens=500)
        assert openai_cost > 0

        # Test Anthropic cost calculation
        anthropic_cost = service.calculate_cost("anthropic", "claude-3", input_tokens=1000, output_tokens=500)
        assert anthropic_cost > 0

    def test_streaming_responses(self):
        """Test streaming response functionality."""
        with patch('python.src.server.services.llm_provider_service.OpenAI') as mock_openai:
            mock_instance = MagicMock()

            # Mock streaming response
            async def mock_stream():
                chunks = [
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
                ]
                for chunk in chunks:
                    yield chunk

            mock_instance.chat.completions.create.return_value = mock_stream()
            mock_openai.return_value = mock_instance

            service = LLMProviderService()
            chunks = []
            for chunk in service.stream_generate("Test prompt", provider="openai"):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert "".join(chunks) == "Hello world!"

class TestEmbeddingService:
    """Test suite for embedding operations."""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock sentence transformer for embeddings."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        return mock_model

    def test_embedding_generation(self, mock_sentence_transformer):
        """Test generating embeddings for text."""
        with patch('python.src.server.services.embeddings.embedding_service.SentenceTransformer', return_value=mock_sentence_transformer):
            service = EmbeddingService()
            texts = ["This is a test document.", "Another test document."]

            embeddings = service.generate_embeddings(texts)

            assert len(embeddings) == 2
            assert len(embeddings[0]) == 5  # Mock returns 5-dimensional vectors
            assert embeddings[0] == [0.1, 0.2, 0.3, 0.4, 0.5]

    def test_batch_embedding_processing(self, mock_sentence_transformer):
        """Test batch processing of embeddings."""
        with patch('python.src.server.services.embeddings.embedding_service.SentenceTransformer', return_value=mock_sentence_transformer):
            service = EmbeddingService()

            # Large batch of texts
            texts = [f"Document {i}" for i in range(100)]
            embeddings = service.generate_embeddings_batch(texts, batch_size=10)

            assert len(embeddings) == 100
            # Verify all embeddings have the same mock values
            assert all(emb == [0.1, 0.2, 0.3, 0.4, 0.5] for emb in embeddings)

    def test_embedding_similarity(self):
        """Test embedding similarity calculations."""
        service = EmbeddingService()

        # Test cosine similarity
        vec1 = [1, 0, 0]
        vec2 = [0, 1, 0]
        vec3 = [1, 1, 0]

        similarity_1_2 = service.cosine_similarity(vec1, vec2)
        similarity_1_3 = service.cosine_similarity(vec1, vec3)

        assert similarity_1_2 == 0  # Orthogonal vectors
        assert similarity_1_3 > similarity_1_2  # vec3 is more similar to vec1

    def test_embedding_caching(self):
        """Test embedding caching functionality."""
        with patch('python.src.server.services.embeddings.embedding_service.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_model.encode.return_value = [[0.5, 0.6, 0.7]]
            mock_transformer.return_value = mock_model

            service = EmbeddingService()

            # First call should generate embedding
            emb1 = service.generate_embeddings(["test"], use_cache=True)

            # Second call with same text should use cache
            emb2 = service.generate_embeddings(["test"], use_cache=True)

            assert emb1 == emb2
            # Model should only be called once due to caching
            assert mock_model.encode.call_count == 1

    def test_embedding_dimensions(self):
        """Test embedding dimensionality handling."""
        service = EmbeddingService()

        # Test dimension reduction
        high_dim_vector = list(range(768))  # Typical BERT dimension
        reduced_vector = service.reduce_dimensions(high_dim_vector, target_dim=384)

        assert len(reduced_vector) == 384

        # Test dimension normalization
        normalized_vector = service.normalize_embedding(high_dim_vector)
        # Normalized vector should have unit length
        magnitude = sum(x**2 for x in normalized_vector) ** 0.5
        assert abs(magnitude - 1.0) < 0.001

    def test_embedding_validation(self):
        """Test embedding input validation."""
        service = EmbeddingService()

        # Test empty input
        with pytest.raises(ValueError, match="Empty text input"):
            service.generate_embeddings([])

        # Test invalid text input
        with pytest.raises(ValueError, match="Invalid text input"):
            service.generate_embeddings([None, ""])

    def test_model_loading(self):
        """Test different model loading configurations."""
        with patch('python.src.server.services.embeddings.embedding_service.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model

            # Test different model configurations
            configs = [
                {"model_name": "all-MiniLM-L6-v2", "device": "cpu"},
                {"model_name": "paraphrase-MiniLM-L3-v2", "device": "cuda"},
            ]

            for config in configs:
                service = EmbeddingService(**config)
                assert service.model is not None
                mock_transformer.assert_called_with(
                    model_name=config["model_name"],
                    device=config["device"]
                )

class TestRAGService:
    """Test suite for RAG (Retrieval-Augmented Generation) operations."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service for RAG."""
        mock_service = MagicMock()
        mock_service.generate_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_service.cosine_similarity.return_value = 0.8
        return mock_service

    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store for RAG."""
        mock_store = MagicMock()
        mock_store.search.return_value = [
            {"id": "doc1", "content": "Test document", "score": 0.9},
            {"id": "doc2", "content": "Another document", "score": 0.7},
        ]
        return mock_store

    def test_rag_query_processing(self, mock_embedding_service, mock_vector_store):
        """Test RAG query processing pipeline."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store):

            service = RAGService()

            query = "What is machine learning?"
            results = service.process_query(query, top_k=2)

            assert len(results) == 2
            assert results[0]["content"] == "Test document"
            assert results[0]["score"] == 0.9

    def test_context_retrieval(self, mock_embedding_service, mock_vector_store):
        """Test context retrieval from knowledge base."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store):

            service = RAGService()

            query = "artificial intelligence"
            context = service.retrieve_context(query, max_tokens=500)

            assert isinstance(context, str)
            assert len(context) > 0
            assert "Test document" in context

    def test_rag_response_generation(self, mock_embedding_service, mock_vector_store):
        """Test end-to-end RAG response generation."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store), \
             patch('python.src.server.services.search.rag_service.LLMProviderService') as mock_llm:

            mock_llm_instance = MagicMock()
            mock_llm_instance.generate_text.return_value = {
                "content": "Machine learning is a subset of AI...",
                "provider": "openai",
                "tokens_used": 150
            }
            mock_llm.return_value = mock_llm_instance

            service = RAGService()

            query = "Explain machine learning"
            response = service.generate_rag_response(query)

            assert "Machine learning is a subset of AI" in response["content"]
            assert response["provider"] == "openai"
            assert response["retrieved_docs"] == 2

    def test_relevance_filtering(self, mock_embedding_service, mock_vector_store):
        """Test relevance filtering of retrieved documents."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store):

            service = RAGService()

            # Mock low relevance results
            mock_vector_store.search.return_value = [
                {"id": "doc1", "content": "Irrelevant content", "score": 0.3},
                {"id": "doc2", "content": "Somewhat relevant", "score": 0.6},
                {"id": "doc3", "content": "Highly relevant", "score": 0.95},
            ]

            results = service.process_query("test query", min_score=0.5)

            # Should only return results above threshold
            assert len(results) == 2
            assert all(result["score"] >= 0.5 for result in results)

    def test_context_window_management(self, mock_embedding_service, mock_vector_store):
        """Test context window management for large documents."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store):

            service = RAGService()

            # Mock very long document
            long_content = "Word " * 1000  # 2000 characters
            mock_vector_store.search.return_value = [
                {"id": "doc1", "content": long_content, "score": 0.9}
            ]

            context = service.retrieve_context("test query", max_tokens=100)

            # Context should be truncated to fit token limit
            assert len(context.split()) <= 100

    def test_multi_query_expansion(self, mock_embedding_service, mock_vector_store):
        """Test multi-query expansion for better retrieval."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store), \
             patch('python.src.server.services.search.rag_service.LLMProviderService') as mock_llm:

            mock_llm_instance = MagicMock()
            mock_llm_instance.generate_text.return_value = {
                "content": "What is AI?\nHow does AI work?\nAI applications",
                "provider": "openai"
            }
            mock_llm.return_value = mock_llm_instance

            service = RAGService()

            original_query = "artificial intelligence"
            expanded_queries = service.expand_query(original_query)

            assert len(expanded_queries) > 1
            assert original_query in expanded_queries

    def test_rag_performance_monitoring(self, mock_embedding_service, mock_vector_store):
        """Test performance monitoring for RAG operations."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store):

            service = RAGService()

            import time
            start_time = time.time()

            service.process_query("test query")
            end_time = time.time()

            # Check that performance metrics are recorded
            metrics = service.get_performance_metrics()
            assert "avg_query_time" in metrics
            assert "total_queries" in metrics
            assert metrics["total_queries"] >= 1

    def test_error_handling(self, mock_embedding_service, mock_vector_store):
        """Test error handling in RAG operations."""
        with patch('python.src.server.services.search.rag_service.EmbeddingService', return_value=mock_embedding_service), \
             patch('python.src.server.services.search.rag_service.VectorStore', return_value=mock_vector_store):

            # Make vector store fail
            mock_vector_store.search.side_effect = Exception("Vector store error")

            service = RAGService()

            # Should handle error gracefully
            results = service.process_query("test query")
            assert results == []  # Return empty results on error

    def test_rag_configuration(self):
        """Test RAG service configuration options."""
        service = RAGService(
            top_k=5,
            min_score=0.7,
            max_context_length=1000,
            use_reranking=True
        )

        assert service.top_k == 5
        assert service.min_score == 0.7
        assert service.max_context_length == 1000
        assert service.use_reranking is True
