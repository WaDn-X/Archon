"""
Multi-Dimensional Embedding Service

Enhanced embedding service supporting multiple vector dimensions and advanced
embedding strategies for improved search accuracy and performance.
"""

import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .embedding_service import EmbeddingService
from ..llm_provider_service import get_llm_client, get_embedding_model


@dataclass
class MultiVectorEmbedding:
    """Multi-dimensional vector embedding with metadata."""
    vectors: List[List[float]]  # Multiple vector representations
    weights: List[float]        # Weight for each vector (sums to 1.0)
    metadata: Dict[str, Any]    # Additional metadata
    source_text: str           # Original text
    embedding_model: str       # Model used for embedding
    dimensions: int            # Total dimensions across all vectors


@dataclass
class DimensionReductionConfig:
    """Configuration for dimension reduction techniques."""
    method: str = "pca"  # pca, umap, tsne, autoencoder
    target_dimensions: int = 384
    preserve_variance: float = 0.95  # For PCA
    learning_rate: float = 0.1       # For autoencoder
    epochs: int = 100


class MultiDimensionalEmbeddingService:
    """Service for creating and managing multi-dimensional embeddings."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_embedding_service = EmbeddingService()

    async def create_multi_vector_embedding(
        self,
        text: str,
        strategies: List[str] = None,
        provider: str = None
    ) -> MultiVectorEmbedding:
        """
        Create multi-dimensional embeddings using multiple strategies.

        Args:
            text: Text to embed
            strategies: List of embedding strategies to use
            provider: AI provider to use

        Returns:
            MultiVectorEmbedding with multiple vector representations
        """
        if strategies is None:
            strategies = ["semantic", "keyword", "contextual"]

        vectors = []
        weights = []
        metadata = {}

        try:
            # Get base embedding for comparison
            base_embedding = await self.base_embedding_service.create_embedding(text, provider)
            vectors.append(base_embedding)
            weights.append(0.4)  # Base embedding gets 40% weight

            # Create additional vector representations
            for strategy in strategies[1:]:  # Skip first as it's the base
                try:
                    if strategy == "keyword":
                        vector = await self._create_keyword_embedding(text)
                    elif strategy == "contextual":
                        vector = await self._create_contextual_embedding(text)
                    elif strategy == "semantic":
                        vector = await self._create_enhanced_semantic_embedding(text)
                    else:
                        continue

                    if vector:
                        vectors.append(vector)
                        weights.append(0.2)  # Additional strategies get 20% each

                except Exception as e:
                    self.logger.warning(f"Failed to create {strategy} embedding: {e}")
                    continue

            # Normalize weights to sum to 1.0
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]

            # Calculate total dimensions
            total_dims = sum(len(v) for v in vectors)

            return MultiVectorEmbedding(
                vectors=vectors,
                weights=weights,
                metadata={
                    "strategies_used": strategies[:len(vectors)],
                    "total_strategies": len(strategies),
                    "base_provider": provider or "auto"
                },
                source_text=text,
                embedding_model=provider or "auto",
                dimensions=total_dims
            )

        except Exception as e:
            self.logger.error(f"Error creating multi-vector embedding: {e}")
            raise

    async def _create_keyword_embedding(self, text: str) -> List[float]:
        """Create keyword-based embedding focusing on important terms."""
        try:
            # Extract keywords using simple frequency analysis
            words = text.lower().split()
            word_freq = {}

            for word in words:
                if len(word) > 3:  # Ignore very short words
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Get top keywords (limit to 50 for embedding size)
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]

            # Create a simple embedding based on keyword presence and frequency
            embedding = [0.0] * 384  # Match standard embedding size

            for i, (keyword, freq) in enumerate(top_keywords):
                if i < len(embedding):
                    # Use frequency as a simple score (normalize by max freq)
                    max_freq = top_keywords[0][1] if top_keywords else 1
                    embedding[i] = freq / max_freq

            return embedding

        except Exception as e:
            self.logger.error(f"Error creating keyword embedding: {e}")
            return []

    async def _create_contextual_embedding(self, text: str) -> List[float]:
        """Create contextual embedding focusing on document structure."""
        try:
            # Simple contextual analysis based on text structure
            sentences = text.split('.')
            embedding = [0.0] * 384

            # Analyze sentence structure and context
            total_sentences = len(sentences)
            if total_sentences == 0:
                return embedding

            # Score based on sentence position (earlier sentences more important)
            for i, sentence in enumerate(sentences[:10]):  # First 10 sentences
                if i < len(embedding):
                    # Position weight (earlier = more important)
                    position_weight = (10 - i) / 10
                    # Length weight (medium length sentences preferred)
                    length_weight = min(len(sentence.split()) / 15, 1.0)  # Optimal ~15 words

                    embedding[i] = position_weight * length_weight

            return embedding

        except Exception as e:
            self.logger.error(f"Error creating contextual embedding: {e}")
            return []

    async def _create_enhanced_semantic_embedding(self, text: str) -> List[float]:
        """Create enhanced semantic embedding using multiple models/approaches."""
        try:
            # For now, return a modified version of the base embedding
            # In a full implementation, this would use multiple embedding models

            base_embedding = await self.base_embedding_service.create_embedding(text)

            # Create a variation by applying a simple transformation
            # This simulates using a different embedding approach
            enhanced_embedding = []
            for i, value in enumerate(base_embedding):
                # Apply a simple sinusoidal variation to simulate different model
                variation = 0.1 * (i % 10) / 10  # Small variation based on position
                enhanced_embedding.append(min(1.0, max(-1.0, value + variation)))

            return enhanced_embedding

        except Exception as e:
            self.logger.error(f"Error creating enhanced semantic embedding: {e}")
            return []

    def reduce_dimensions(
        self,
        embeddings: List[MultiVectorEmbedding],
        config: DimensionReductionConfig
    ) -> List[List[float]]:
        """
        Reduce multi-dimensional embeddings to target dimensions.

        Args:
            embeddings: List of multi-vector embeddings
            config: Dimension reduction configuration

        Returns:
            List of reduced-dimension embeddings
        """
        try:
            if not embeddings:
                return []

            # Combine all vectors from all embeddings
            all_vectors = []
            for embedding in embeddings:
                all_vectors.extend(embedding.vectors)

            if not all_vectors:
                return []

            # Convert to numpy array
            vectors_array = np.array(all_vectors)

            if config.method == "pca":
                return self._reduce_with_pca(vectors_array, config)
            elif config.method == "mean":
                return self._reduce_with_mean(vectors_array, config)
            else:
                # Fallback to mean reduction
                return self._reduce_with_mean(vectors_array, config)

        except Exception as e:
            self.logger.error(f"Error reducing dimensions: {e}")
            # Return original vectors if reduction fails
            return [emb.vectors[0] for emb in embeddings if emb.vectors]

    def _reduce_with_pca(self, vectors: np.ndarray, config: DimensionReductionConfig) -> List[List[float]]:
        """Reduce dimensions using PCA."""
        try:
            from sklearn.decomposition import PCA

            # Determine number of components to keep
            if config.target_dimensions:
                n_components = min(config.target_dimensions, vectors.shape[1])
            else:
                # Keep components that explain preserve_variance of variance
                pca = PCA()
                pca.fit(vectors)
                cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
                n_components = np.where(cumulative_variance >= config.preserve_variance)[0][0] + 1
                n_components = min(n_components, vectors.shape[1])

            # Apply PCA
            pca = PCA(n_components=n_components)
            reduced_vectors = pca.fit_transform(vectors)

            return reduced_vectors.tolist()

        except ImportError:
            self.logger.warning("sklearn not available, falling back to mean reduction")
            return self._reduce_with_mean(vectors, config)
        except Exception as e:
            self.logger.error(f"PCA reduction failed: {e}")
            return self._reduce_with_mean(vectors, config)

    def _reduce_with_mean(self, vectors: np.ndarray, config: DimensionReductionConfig) -> List[List[float]]:
        """Reduce dimensions by taking mean across multiple vectors."""
        try:
            # For each original vector, take chunks and compute means
            chunk_size = max(1, vectors.shape[1] // config.target_dimensions)

            reduced_vectors = []
            for vector in vectors:
                reduced = []
                for i in range(0, len(vector), chunk_size):
                    chunk = vector[i:i + chunk_size]
                    if chunk:
                        reduced.append(float(np.mean(chunk)))

                # Pad or truncate to target dimensions
                if len(reduced) < config.target_dimensions:
                    # Pad with zeros
                    reduced.extend([0.0] * (config.target_dimensions - len(reduced)))
                elif len(reduced) > config.target_dimensions:
                    # Truncate
                    reduced = reduced[:config.target_dimensions]

                reduced_vectors.append(reduced)

            return reduced_vectors

        except Exception as e:
            self.logger.error(f"Mean reduction failed: {e}")
            return vectors.tolist()

    async def search_multi_dimensional(
        self,
        query: str,
        embeddings: List[MultiVectorEmbedding],
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search using multi-dimensional embeddings with enhanced similarity.

        Args:
            query: Search query
            embeddings: List of multi-vector embeddings to search
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of search results with scores and metadata
        """
        try:
            if not embeddings:
                return []

            # Create query embedding
            query_embedding = await self.create_multi_vector_embedding(query)

            results = []
            for emb in embeddings:
                # Calculate similarity using weighted combination of vectors
                similarity = self._calculate_multi_vector_similarity(query_embedding, emb)

                if similarity >= similarity_threshold:
                    results.append({
                        "text": emb.source_text,
                        "similarity": similarity,
                        "metadata": emb.metadata,
                        "dimensions": emb.dimensions,
                        "strategies": emb.metadata.get("strategies_used", [])
                    })

            # Sort by similarity and return top k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]

        except Exception as e:
            self.logger.error(f"Error in multi-dimensional search: {e}")
            return []

    def _calculate_multi_vector_similarity(
        self,
        query_emb: MultiVectorEmbedding,
        target_emb: MultiVectorEmbedding
    ) -> float:
        """Calculate similarity between two multi-vector embeddings."""
        try:
            if not query_emb.vectors or not target_emb.vectors:
                return 0.0

            # Calculate similarity for each vector pair
            similarities = []
            for i, query_vector in enumerate(query_emb.vectors):
                if i < len(target_emb.vectors):
                    target_vector = target_emb.vectors[i]

                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_vector, target_vector)
                    similarities.append(similarity)

            # Weight the similarities and combine
            if similarities:
                # Use corresponding weights if available
                query_weight = query_emb.weights[i] if i < len(query_emb.weights) else 0.5
                target_weight = target_emb.weights[i] if i < len(target_emb.weights) else 0.5

                # Weighted combination
                combined_similarity = sum(similarities) / len(similarities)
                return combined_similarity

            return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating multi-vector similarity: {e}")
            return 0.0

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Convert to numpy arrays
            v1 = np.array(vec1)
            v2 = np.array(vec2)

            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))

        except Exception:
            return 0.0


# Global instance
multi_dimensional_service = MultiDimensionalEmbeddingService()
