"""
Advanced Reranking Service

Provides sophisticated reranking algorithms for search results including:
- Recency boosting
- Authority scoring
- Engagement metrics
- Semantic relevance enhancement
- Cross-reference analysis
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import re

from .base_search_strategy import BaseSearchStrategy


@dataclass
class RerankingWeights:
    """Weights for different reranking factors."""
    similarity: float = 0.4      # Base similarity score
    recency: float = 0.15        # How recent the content is
    authority: float = 0.15      # Source authority/trust
    engagement: float = 0.1      # User engagement metrics
    relevance: float = 0.1       # Semantic relevance
    popularity: float = 0.1      # Content popularity


@dataclass
class RerankingResult:
    """Result from reranking process."""
    original_result: Dict[str, Any]
    reranked_score: float
    reranking_factors: Dict[str, float]
    explanations: List[str]


class AdvancedRerankingService:
    """Service for advanced reranking of search results."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.weights = RerankingWeights()

    async def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[RerankingResult]:
        """
        Rerank search results using multiple factors.

        Args:
            query: Original search query
            results: Raw search results
            context: Additional context for reranking

        Returns:
            List of reranked results with explanations
        """
        try:
            reranked_results = []

            for result in results:
                # Calculate reranking score
                reranked_score = await self._calculate_reranking_score(query, result, context)

                # Generate explanations
                explanations = self._generate_reranking_explanations(query, result, context)

                # Create reranking factors breakdown
                factors = {
                    "similarity": result.get("similarity", 0),
                    "recency": await self._calculate_recency_score(result),
                    "authority": await self._calculate_authority_score(result),
                    "engagement": await self._calculate_engagement_score(result),
                    "relevance": await self._calculate_relevance_score(query, result),
                    "popularity": await self._calculate_popularity_score(result)
                }

                reranked_result = RerankingResult(
                    original_result=result,
                    reranked_score=reranked_score,
                    reranking_factors=factors,
                    explanations=explanations
                )

                reranked_results.append(reranked_result)

            # Sort by reranked score
            reranked_results.sort(key=lambda x: x.reranked_score, reverse=True)

            return reranked_results

        except Exception as e:
            self.logger.error(f"Error in reranking: {e}")
            # Return original results if reranking fails
            return [
                RerankingResult(
                    original_result=result,
                    reranked_score=result.get("similarity", 0),
                    reranking_factors={"similarity": result.get("similarity", 0)},
                    explanations=["Reranking failed, using original similarity"]
                )
                for result in results
            ]

    async def _calculate_reranking_score(
        self,
        query: str,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate the final reranking score."""
        try:
            # Get base similarity
            base_similarity = result.get("similarity", 0)

            # Calculate additional factors
            recency_score = await self._calculate_recency_score(result)
            authority_score = await self._calculate_authority_score(result)
            engagement_score = await self._calculate_engagement_score(result)
            relevance_score = await self._calculate_relevance_score(query, result)
            popularity_score = await self._calculate_popularity_score(result)

            # Apply weights
            reranked_score = (
                base_similarity * self.weights.similarity +
                recency_score * self.weights.recency +
                authority_score * self.weights.authority +
                engagement_score * self.weights.engagement +
                relevance_score * self.weights.relevance +
                popularity_score * self.weights.popularity
            )

            return min(1.0, max(0.0, reranked_score))

        except Exception as e:
            self.logger.error(f"Error calculating reranking score: {e}")
            return result.get("similarity", 0)

    async def _calculate_recency_score(self, result: Dict[str, Any]) -> float:
        """Calculate recency score (newer content gets higher score)."""
        try:
            # Get creation/update date
            created_at = result.get("created_at") or result.get("updated_at")
            if not created_at:
                return 0.5  # Neutral score if no date

            # Parse date
            if isinstance(created_at, str):
                try:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    return 0.5
            else:
                date_obj = created_at

            # Calculate days since creation
            days_old = (datetime.now() - date_obj.replace(tzinfo=None)).days

            # Recency scoring: exponential decay
            # Content from today: 1.0
            # Content from 30 days ago: ~0.5
            # Content from 90 days ago: ~0.25
            if days_old <= 0:
                return 1.0
            elif days_old <= 30:
                return 1.0 / (1 + days_old * 0.05)  # Gradual decay
            else:
                return 0.25 / (1 + (days_old - 30) * 0.02)  # Slower decay for older content

        except Exception as e:
            self.logger.error(f"Error calculating recency score: {e}")
            return 0.5

    async def _calculate_authority_score(self, result: Dict[str, Any]) -> float:
        """Calculate authority score based on source credibility."""
        try:
            # Default neutral score
            score = 0.5

            # Check for domain authority indicators
            url = result.get("url", "")
            content = result.get("content", "")

            # High-authority domains
            high_authority_domains = [
                "github.com", "stackoverflow.com", "docs.microsoft.com",
                "developer.mozilla.org", "react.dev", "nodejs.org"
            ]

            # Check domain
            if any(domain in url.lower() for domain in high_authority_domains):
                score += 0.3

            # Check for official documentation indicators
            official_indicators = [
                "official", "documentation", "docs", "reference",
                "api reference", "developer guide"
            ]

            if any(indicator in content.lower() for indicator in official_indicators):
                score += 0.2

            # Check for code examples (indicates practical knowledge)
            if "```" in content or "<code>" in content or "function" in content.lower():
                score += 0.1

            return min(1.0, score)

        except Exception as e:
            self.logger.error(f"Error calculating authority score: {e}")
            return 0.5

    async def _calculate_engagement_score(self, result: Dict[str, Any]) -> float:
        """Calculate engagement score based on content quality indicators."""
        try:
            content = result.get("content", "")
            if not content:
                return 0.5

            score = 0.5  # Base score

            # Length quality (not too short, not too long)
            word_count = len(content.split())
            if 100 <= word_count <= 1000:
                score += 0.2
            elif word_count > 1000:
                score += 0.1  # Bonus for comprehensive content

            # Structure quality (has headings, lists, code blocks)
            structure_indicators = 0
            if re.search(r'^#{1,6}\s', content, re.MULTILINE): structure_indicators += 1
            if re.search(r'^[\d\*\-\+]\s', content, re.MULTILINE): structure_indicators += 1
            if "```" in content: structure_indicators += 1

            if structure_indicators >= 2:
                score += 0.2

            # Code quality indicators
            if "example" in content.lower() or "demo" in content.lower():
                score += 0.1

            return min(1.0, score)

        except Exception as e:
            self.logger.error(f"Error calculating engagement score: {e}")
            return 0.5

    async def _calculate_relevance_score(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate semantic relevance beyond basic similarity."""
        try:
            query_terms = set(query.lower().split())
            content = result.get("content", "").lower()

            # Calculate term overlap
            content_words = set(content.split())
            overlap = len(query_terms.intersection(content_words))

            if not query_terms:
                return 0.5

            overlap_ratio = overlap / len(query_terms)

            # Boost for exact phrase matches
            exact_phrase_bonus = 0.0
            if query.lower() in content:
                exact_phrase_bonus = 0.2

            # Boost for query terms in title
            title = result.get("title", "").lower()
            title_matches = len(query_terms.intersection(set(title.split())))
            title_bonus = (title_matches / len(query_terms)) * 0.1

            relevance = overlap_ratio + exact_phrase_bonus + title_bonus
            return min(1.0, relevance)

        except Exception as e:
            self.logger.error(f"Error calculating relevance score: {e}")
            return 0.5

    async def _calculate_popularity_score(self, result: Dict[str, Any]) -> float:
        """Calculate popularity score based on usage metrics."""
        try:
            # Default neutral score
            score = 0.5

            # Check for view/access metrics if available
            metadata = result.get("metadata", {})
            views = metadata.get("views", 0)
            likes = metadata.get("likes", 0)
            shares = metadata.get("shares", 0)

            # Simple popularity scoring
            if views > 100:
                score += 0.2
            if likes > 10:
                score += 0.1
            if shares > 5:
                score += 0.1

            # Check for trending/popular indicators
            if metadata.get("is_trending") or metadata.get("is_featured"):
                score += 0.2

            return min(1.0, score)

        except Exception as e:
            self.logger.error(f"Error calculating popularity score: {e}")
            return 0.5

    def _generate_reranking_explanations(
        self,
        query: str,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate human-readable explanations for reranking decisions."""
        try:
            explanations = []

            # Query relevance explanation
            query_terms = set(query.lower().split())
            title = result.get("title", "")
            content_snippet = result.get("content", "")[:100]

            if query_terms.intersection(set(title.lower().split())):
                explanations.append("Title contains query terms")

            if query.lower() in content_snippet.lower():
                explanations.append("Content contains exact query match")

            # Recency explanation
            created_at = result.get("created_at")
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_old = (datetime.now() - date_obj.replace(tzinfo=None)).days
                    if days_old <= 7:
                        explanations.append("Recently published content")
                    elif days_old <= 30:
                        explanations.append("Recent content")
                except:
                    pass

            # Authority explanation
            url = result.get("url", "")
            if any(domain in url.lower() for domain in ["github.com", "stackoverflow.com", "docs.microsoft.com"]):
                explanations.append("From authoritative source")

            # Engagement explanation
            content = result.get("content", "")
            if "```" in content:
                explanations.append("Contains code examples")

            if len(explanations) == 0:
                explanations.append("Standard relevance scoring applied")

            return explanations

        except Exception as e:
            self.logger.error(f"Error generating explanations: {e}")
            return ["Reranking applied"]

    async def get_reranking_insights(
        self,
        query: str,
        results: List[RerankingResult]
    ) -> Dict[str, Any]:
        """Get insights about the reranking process."""
        try:
            insights = {
                "total_results": len(results),
                "reranking_distribution": {},
                "top_factors": [],
                "improvement_opportunities": []
            }

            # Analyze reranking distribution
            for result in results[:5]:  # Top 5 results
                max_factor = max(result.reranking_factors.items(), key=lambda x: x[1])
                factor_name = max_factor[0]
                insights["reranking_distribution"][factor_name] = \
                    insights["reranking_distribution"].get(factor_name, 0) + 1

            # Identify top contributing factors
            sorted_factors = sorted(
                insights["reranking_distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            insights["top_factors"] = sorted_factors[:3]

            # Identify improvement opportunities
            avg_similarity = sum(r.original_result.get("similarity", 0) for r in results) / len(results)
            avg_reranked = sum(r.reranked_score for r in results) / len(results)

            if avg_reranked > avg_similarity + 0.1:
                insights["improvement_opportunities"].append(
                    "Reranking significantly improved result quality"
                )

            return insights

        except Exception as e:
            self.logger.error(f"Error getting reranking insights: {e}")
            return {}


# Global instance
advanced_reranking_service = AdvancedRerankingService()
