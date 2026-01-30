"""
Intelligent Document Chunking Service

Provides advanced document chunking strategies for optimal search and retrieval:
- Semantic chunking based on content structure
- Intelligent overlap optimization
- Context preservation
- Chunk quality scoring
- Adaptive chunking strategies
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    chunk_id: str
    start_position: int
    end_position: int
    chunk_length: int
    quality_score: float
    semantic_coherence: float
    overlap_with_previous: int
    overlap_with_next: int
    section_type: str  # header, paragraph, list, code, etc.
    importance_score: float  # 0-1 based on content importance


@dataclass
class ChunkingStrategy:
    """Configuration for chunking strategy."""
    method: str = "semantic"  # semantic, fixed, sentence, paragraph
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    overlap_ratio: float = 0.1  # 10% overlap
    preserve_structure: bool = True
    adaptive_sizing: bool = True
    quality_threshold: float = 0.6


class ChunkQualityAnalyzer:
    """Analyzes chunk quality for optimization."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_chunk_quality(self, text: str, context: Dict[str, Any] = None) -> Dict[str, float]:
        """Analyze various quality metrics for a text chunk."""
        try:
            metrics = {}

            # Length quality (not too short, not too long)
            word_count = len(text.split())
            if 50 <= word_count <= 500:
                metrics["length_quality"] = 1.0
            elif word_count < 50:
                metrics["length_quality"] = word_count / 50
            else:
                metrics["length_quality"] = max(0.5, 1.0 - (word_count - 500) / 1000)

            # Structure quality (has complete sentences, proper punctuation)
            sentences = re.split(r'[.!?]+', text)
            complete_sentences = len([s for s in sentences if len(s.strip()) > 10])

            if len(sentences) > 0:
                metrics["structure_quality"] = min(1.0, complete_sentences / len(sentences))
            else:
                metrics["structure_quality"] = 0.5

            # Content density (information-rich content)
            # Simple heuristic: ratio of meaningful words to total words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            meaningful_words = len([w for w in text.lower().split() if w not in stop_words])
            total_words = len(text.split())

            if total_words > 0:
                metrics["content_density"] = meaningful_words / total_words
            else:
                metrics["content_density"] = 0.5

            # Coherence (text flows naturally)
            # Simple heuristic: sentence length variation
            sentence_lengths = [len(s.strip().split()) for s in sentences if s.strip()]
            if len(sentence_lengths) > 1:
                mean_length = sum(sentence_lengths) / len(sentence_lengths)
                variance = sum((l - mean_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
                # Lower variance = more coherent
                metrics["coherence"] = max(0.0, 1.0 - variance / 100)
            else:
                metrics["coherence"] = 0.7

            # Overall quality score
            weights = {
                "length_quality": 0.25,
                "structure_quality": 0.25,
                "content_density": 0.25,
                "coherence": 0.25
            }

            metrics["overall_quality"] = sum(
                metrics.get(key, 0.5) * weight
                for key, weight in weights.items()
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error analyzing chunk quality: {e}")
            return {"overall_quality": 0.5}


class IntelligentChunkingService:
    """Service for intelligent document chunking with semantic awareness."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.quality_analyzer = ChunkQualityAnalyzer()

    def chunk_document(
        self,
        text: str,
        strategy: ChunkingStrategy = None,
        preserve_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Intelligently chunk a document using semantic analysis.

        Args:
            text: Document text to chunk
            strategy: Chunking strategy configuration
            preserve_metadata: Whether to include chunk metadata

        Returns:
            List of document chunks with metadata
        """
        if strategy is None:
            strategy = ChunkingStrategy()

        try:
            if strategy.method == "semantic":
                return self._semantic_chunking(text, strategy)
            elif strategy.method == "fixed":
                return self._fixed_size_chunking(text, strategy)
            elif strategy.method == "sentence":
                return self._sentence_based_chunking(text, strategy)
            elif strategy.method == "paragraph":
                return self._paragraph_based_chunking(text, strategy)
            else:
                # Default to semantic chunking
                return self._semantic_chunking(text, strategy)

        except Exception as e:
            self.logger.error(f"Error in document chunking: {e}")
            # Fallback to simple sentence-based chunking
            return self._sentence_based_chunking(text, strategy or ChunkingStrategy())

    def _semantic_chunking(self, text: str, strategy: ChunkingStrategy) -> List[Dict[str, Any]]:
        """Perform semantic-aware chunking."""
        try:
            # First, identify structural elements
            sections = self._identify_sections(text)

            chunks = []
            current_chunk = ""
            current_start = 0

            for section in sections:
                section_text = section["text"]
                section_type = section["type"]

                # Check if adding this section would exceed max size
                potential_chunk = current_chunk + " " + section_text if current_chunk else section_text

                if len(potential_chunk.split()) > strategy.max_chunk_size:
                    # Current chunk is ready, save it
                    if current_chunk.strip():
                        chunk_data = self._create_chunk_data(
                            current_chunk, current_start, len(current_chunk), strategy
                        )
                        chunks.append(chunk_data)

                    # Start new chunk with current section
                    current_chunk = section_text
                    current_start = section["start_pos"]
                else:
                    # Add to current chunk
                    current_chunk = potential_chunk

            # Add final chunk
            if current_chunk.strip():
                chunk_data = self._create_chunk_data(
                    current_chunk, current_start, len(current_chunk), strategy
                )
                chunks.append(chunk_data)

            # Optimize overlaps
            if strategy.overlap_ratio > 0:
                chunks = self._optimize_overlaps(chunks, strategy)

            return chunks

        except Exception as e:
            self.logger.error(f"Error in semantic chunking: {e}")
            return []

    def _identify_sections(self, text: str) -> List[Dict[str, Any]]:
        """Identify structural sections in text."""
        sections = []

        # Headers (lines starting with #)
        header_pattern = r'(^#{1,6}\s+.*$)'  # Markdown headers
        headers = re.finditer(header_pattern, text, re.MULTILINE)

        for header in headers:
            sections.append({
                "text": header.group(1).strip(),
                "type": "header",
                "start_pos": header.start(),
                "end_pos": header.end(),
                "level": len(header.group(1)) - len(header.group(1).lstrip('#'))
            })

        # Code blocks
        code_pattern = r'```[\s\S]*?```'
        code_blocks = re.finditer(code_pattern, text)

        for code in code_blocks:
            sections.append({
                "text": code.group(0).strip(),
                "type": "code_block",
                "start_pos": code.start(),
                "end_pos": code.end()
            })

        # Lists (ordered and unordered)
        list_pattern = r'^(?:\d+\.|\*|\-|\+)\s+.*$'
        lists = re.finditer(list_pattern, text, re.MULTILINE)

        for list_item in lists:
            sections.append({
                "text": list_item.group(0).strip(),
                "type": "list_item",
                "start_pos": list_item.start(),
                "end_pos": list_item.end()
            })

        # Paragraphs (text between structural elements)
        if sections:
            # Sort sections by position
            sections.sort(key=lambda x: x["start_pos"])

            # Add paragraph sections between structural elements
            prev_end = 0
            for section in sections:
                if section["start_pos"] > prev_end:
                    paragraph_text = text[prev_end:section["start_pos"]].strip()
                    if paragraph_text:
                        sections.append({
                            "text": paragraph_text,
                            "type": "paragraph",
                            "start_pos": prev_end,
                            "end_pos": section["start_pos"]
                        })
                prev_end = section["end_pos"]

            # Add final paragraph if needed
            if prev_end < len(text):
                final_text = text[prev_end:].strip()
                if final_text:
                    sections.append({
                        "text": final_text,
                        "type": "paragraph",
                        "start_pos": prev_end,
                        "end_pos": len(text)
                    })

        # If no structural elements found, treat as single paragraph
        if not sections:
            sections.append({
                "text": text.strip(),
                "type": "paragraph",
                "start_pos": 0,
                "end_pos": len(text)
            })

        return sections

    def _create_chunk_data(
        self,
        text: str,
        start_pos: int,
        length: int,
        strategy: ChunkingStrategy
    ) -> Dict[str, Any]:
        """Create chunk data with metadata."""
        # Analyze quality
        quality_metrics = self.quality_analyzer.analyze_chunk_quality(text)

        # Determine importance based on content type and position
        importance = self._calculate_importance(text, quality_metrics)

        # Determine section type
        section_type = self._determine_section_type(text)

        chunk_metadata = ChunkMetadata(
            chunk_id=f"chunk_{start_pos}_{start_pos + length}",
            start_position=start_pos,
            end_position=start_pos + length,
            chunk_length=len(text),
            quality_score=quality_metrics.get("overall_quality", 0.5),
            semantic_coherence=quality_metrics.get("coherence", 0.5),
            overlap_with_previous=0,  # Will be set during overlap optimization
            overlap_with_next=0,     # Will be set during overlap optimization
            section_type=section_type,
            importance_score=importance
        )

        return {
            "text": text.strip(),
            "metadata": chunk_metadata.__dict__ if hasattr(chunk_metadata, '__dict__') else chunk_metadata,
            "start_position": start_pos,
            "end_position": start_pos + length,
            "length": len(text),
            "quality_score": quality_metrics.get("overall_quality", 0.5)
        }

    def _calculate_importance(self, text: str, quality_metrics: Dict[str, float]) -> float:
        """Calculate importance score for a chunk."""
        importance = 0.5  # Base importance

        # Boost for high-quality content
        if quality_metrics.get("overall_quality", 0) > 0.7:
            importance += 0.2

        # Boost for headers and structured content
        if text.strip().startswith('#'):
            importance += 0.3
        elif '```' in text:
            importance += 0.2  # Code blocks are important
        elif any(marker in text.lower() for marker in ['example', 'demo', 'tutorial']):
            importance += 0.1

        return min(1.0, importance)

    def _determine_section_type(self, text: str) -> str:
        """Determine the type of section this chunk represents."""
        text_lower = text.lower().strip()

        if text_lower.startswith('#'):
            return "header"
        elif '```' in text:
            return "code_block"
        elif any(text_lower.startswith(marker) for marker in ['*', '-', '+', '1.', '2.', '3.']):
            return "list"
        elif len(text.split('.')) > 3 and len(text) > 200:
            return "paragraph"
        else:
            return "content"

    def _optimize_overlaps(self, chunks: List[Dict[str, Any]], strategy: ChunkingStrategy) -> List[Dict[str, Any]]:
        """Optimize chunk overlaps for better context preservation."""
        if not chunks:
            return chunks

        optimized_chunks = []

        for i, chunk in enumerate(chunks):
            # Calculate overlap with previous chunk
            if i > 0:
                prev_chunk = chunks[i - 1]
                overlap = self._calculate_chunk_overlap(chunk, prev_chunk, strategy.overlap_ratio)
                chunk["metadata"]["overlap_with_previous"] = overlap
            else:
                chunk["metadata"]["overlap_with_previous"] = 0

            # Calculate overlap with next chunk
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                overlap = self._calculate_chunk_overlap(chunk, next_chunk, strategy.overlap_ratio)
                chunk["metadata"]["overlap_with_next"] = overlap
            else:
                chunk["metadata"]["overlap_with_next"] = 0

            optimized_chunks.append(chunk)

        return optimized_chunks

    def _calculate_chunk_overlap(
        self,
        chunk1: Dict[str, Any],
        chunk2: Dict[str, Any],
        overlap_ratio: float
    ) -> int:
        """Calculate optimal overlap between two chunks."""
        try:
            # Simple overlap calculation based on text similarity
            text1 = chunk1["text"].lower()
            text2 = chunk2["text"].lower()

            # Count common words
            words1 = set(text1.split())
            words2 = set(text2.split())
            common_words = len(words1.intersection(words2))

            # Calculate overlap as percentage of smaller chunk
            min_words = min(len(words1), len(words2))
            if min_words == 0:
                return 0

            overlap_percent = common_words / min_words

            # Apply overlap ratio
            target_overlap = int(len(chunk1["text"].split()) * overlap_ratio)

            # Adjust based on actual content overlap
            if overlap_percent > 0.3:  # High content overlap
                target_overlap = int(target_overlap * 1.5)
            elif overlap_percent < 0.1:  # Low content overlap
                target_overlap = int(target_overlap * 0.7)

            return min(target_overlap, 100)  # Cap at 100 words

        except Exception as e:
            self.logger.error(f"Error calculating chunk overlap: {e}")
            return int(len(chunk1["text"].split()) * overlap_ratio)

    def _fixed_size_chunking(self, text: str, strategy: ChunkingStrategy) -> List[Dict[str, Any]]:
        """Simple fixed-size chunking."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), strategy.max_chunk_size - int(strategy.max_chunk_size * strategy.overlap_ratio)):
            chunk_words = words[i:i + strategy.max_chunk_size]
            chunk_text = " ".join(chunk_words)

            if len(chunk_text.strip()) >= strategy.min_chunk_size:
                chunk_data = self._create_chunk_data(
                    chunk_text, i, len(chunk_text), strategy
                )
                chunks.append(chunk_data)

        return chunks

    def _sentence_based_chunking(self, text: str, strategy: ChunkingStrategy) -> List[Dict[str, Any]]:
        """Chunk based on sentence boundaries."""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if adding this sentence would exceed max size
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence

            if len(potential_chunk.split()) > strategy.max_chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_data = self._create_chunk_data(
                        current_chunk, 0, len(current_chunk), strategy
                    )
                    chunks.append(chunk_data)

                # Start new chunk
                current_chunk = sentence
            else:
                current_chunk = potential_chunk

        # Add final chunk
        if current_chunk:
            chunk_data = self._create_chunk_data(
                current_chunk, 0, len(current_chunk), strategy
            )
            chunks.append(chunk_data)

        return chunks

    def _paragraph_based_chunking(self, text: str, strategy: ChunkingStrategy) -> List[Dict[str, Any]]:
        """Chunk based on paragraph boundaries."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []

        for paragraph in paragraphs:
            if len(paragraph.split()) > strategy.max_chunk_size:
                # Paragraph is too long, use sentence-based chunking
                sentence_chunks = self._sentence_based_chunking(paragraph, strategy)
                chunks.extend(sentence_chunks)
            elif len(paragraph.split()) >= strategy.min_chunk_size:
                chunk_data = self._create_chunk_data(
                    paragraph, 0, len(paragraph), strategy
                )
                chunks.append(chunk_data)

        return chunks

    def optimize_chunking_strategy(
        self,
        text: str,
        target_chunk_count: int = 10
    ) -> ChunkingStrategy:
        """Optimize chunking strategy for a document."""
        try:
            # Analyze document characteristics
            word_count = len(text.split())
            sentence_count = len(re.split(r'[.!?]+', text))

            # Adaptive strategy based on document size and complexity
            if word_count < 1000:
                # Small document - use larger chunks
                return ChunkingStrategy(
                    method="semantic",
                    max_chunk_size=800,
                    min_chunk_size=200,
                    overlap_ratio=0.15
                )
            elif word_count < 5000:
                # Medium document - balanced approach
                return ChunkingStrategy(
                    method="semantic",
                    max_chunk_size=600,
                    min_chunk_size=150,
                    overlap_ratio=0.1
                )
            else:
                # Large document - smaller chunks for better granularity
                return ChunkingStrategy(
                    method="semantic",
                    max_chunk_size=400,
                    min_chunk_size=100,
                    overlap_ratio=0.05
                )

        except Exception as e:
            self.logger.error(f"Error optimizing chunking strategy: {e}")
            return ChunkingStrategy()

    def get_chunking_insights(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get insights about the chunking results."""
        try:
            if not chunks:
                return {}

            insights = {
                "total_chunks": len(chunks),
                "average_chunk_size": sum(c["length"] for c in chunks) / len(chunks),
                "quality_distribution": {},
                "section_types": {},
                "overlap_analysis": {}
            }

            # Quality distribution
            quality_scores = [c.get("quality_score", 0) for c in chunks]
            for score in quality_scores:
                quality_range = f"{int(score * 10) * 10}-{int(score * 10) * 10 + 9}%"
                insights["quality_distribution"][quality_range] = \
                    insights["quality_distribution"].get(quality_range, 0) + 1

            # Section types
            for chunk in chunks:
                section_type = chunk.get("metadata", {}).get("section_type", "unknown")
                insights["section_types"][section_type] = \
                    insights["section_types"].get(section_type, 0) + 1

            # Overlap analysis
            total_overlap = sum(
                c.get("metadata", {}).get("overlap_with_next", 0) for c in chunks
            )
            if len(chunks) > 1:
                insights["overlap_analysis"]["average_overlap"] = total_overlap / (len(chunks) - 1)
            else:
                insights["overlap_analysis"]["average_overlap"] = 0

            return insights

        except Exception as e:
            self.logger.error(f"Error getting chunking insights: {e}")
            return {}


# Global instance
intelligent_chunking_service = IntelligentChunkingService()
