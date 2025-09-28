"""
Enhanced Rubric Scorer for VoidSpec Integration

This module implements an enhanced rubric scoring system that combines VoidSpec's
traditional metrics with ZippyTrust validation and advanced scoring algorithms.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..plugins.trust_manager import ZippyTrustManager

logger = logging.getLogger(__name__)


@dataclass
class EnhancedRubricScore:
    """Enhanced rubric score combining multiple assessment dimensions."""
    # VoidSpec traditional metrics (0-1 scale)
    clarity: float
    structure: float
    testability: float
    conformity: float

    # ZippyTrust metrics
    security_score: float
    code_quality: float
    documentation_quality: float
    community_trust: float

    # Combined metrics
    total_score: float
    trust_level: str  # 'high', 'medium', 'low'
    notes: List[str]


class EnhancedRubricScorer:
    """
    Enhanced rubric scorer combining VoidSpec and ZippyTrust scoring.
    """

    def __init__(self):
        self.trust_manager = ZippyTrustManager()

    async def score_content(self, content: str, kind: str) -> EnhancedRubricScore:
        """
        Score content using enhanced rubric system.

        Args:
            content: Content to score
            kind: Type of content ('requirements', 'design', 'tasks')

        Returns:
            Enhanced rubric score
        """
        try:
            # Get traditional VoidSpec scoring
            voidspec_score = self._score_voidspec_metrics(content, kind)

            # Get ZippyTrust scoring
            trust_score = await self.trust_manager.score_content(content, kind)

            # Calculate combined score
            combined_score = self._calculate_combined_score(voidspec_score, trust_score)

            # Determine trust level
            trust_level = self._determine_trust_level(combined_score)

            # Combine notes
            all_notes = voidspec_score.get('notes', []) + trust_score.get('notes', [])

            return EnhancedRubricScore(
                clarity=voidspec_score['clarity'],
                structure=voidspec_score['structure'],
                testability=voidspec_score['testability'],
                conformity=voidspec_score['conformity'],
                security_score=trust_score.get('security_score', 0.5),
                code_quality=trust_score.get('code_quality', 0.5),
                documentation_quality=trust_score.get('documentation_quality', 0.5),
                community_trust=trust_score.get('community_trust', 0.5),
                total_score=combined_score,
                trust_level=trust_level,
                notes=all_notes
            )

        except Exception as e:
            logger.error(f"Error scoring content: {e}")
            return self._get_default_score()

    def _score_voidspec_metrics(self, content: str, kind: str) -> Dict[str, Any]:
        """
        Score content using traditional VoidSpec rubric.

        Args:
            content: Content to score
            kind: Type of content

        Returns:
            VoidSpec scoring results
        """
        lines = content.split('\n')
        text = content
        notes = []

        # Clarity: penalize vague terms and long lines
        vague_patterns = [
            r'\b(etc\.|and so on|TBD|to be decided)\b',
            r'\b(maybe|perhaps|might|could|should)\b',
            r'\b(somewhere|sometime|somehow)\b'
        ]

        clarity = 1.0
        vague_count = sum(1 for pattern in vague_patterns if re.search(pattern, text, re.IGNORECASE))
        if vague_count > 0:
            clarity -= min(0.3, vague_count * 0.1)
            notes.append(f'{vague_count} vague terms detected')

        long_lines = [l for l in lines if len(l.strip()) > 120]
        if long_lines:
            clarity -= min(0.2, len(long_lines) * 0.05)
            notes.append(f'{len(long_lines)} overly long lines')

        clarity = max(0, min(1, clarity))

        # Structure: presence of headers/sections
        structure = 0.0
        if re.search(r'^#\s+', text, re.MULTILINE):
            structure += 0.4

        if re.search(r'^##\s+', text, re.MULTILINE):
            structure += 0.3

        if re.search(r'^\d+\.', text, re.MULTILINE) or re.search(r'^-\s+', text, re.MULTILINE):
            structure += 0.3

        structure = min(1, structure)
        if structure < 0.5:
            notes.append('Weak document structure')

        # Testability: look for WHEN/THEN or explicit outcomes
        testability = 0.0
        testability_patterns = [
            r'\bWHEN\b.*\bTHE SYSTEM SHALL\b',
            r'\bGIVEN\b.*\bWHEN\b.*\bTHEN\b',
            r'\bOutcome:\b',
            r'\bAcceptance Criteria:\b',
            r'\bScenario:\b'
        ]

        matches = sum(1 for pattern in testability_patterns if re.search(pattern, text, re.IGNORECASE))
        testability = min(1, matches * 0.25)

        if testability < 0.5:
            notes.append('Limited testability indicators')

        # Conformity: adherence to format standards
        conformity = self._score_conformity(content, kind)
        if conformity < 0.7:
            notes.append('Format conformity issues')

        total = (clarity + structure + testability + conformity) / 4

        return {
            'clarity': round(clarity, 3),
            'structure': round(structure, 3),
            'testability': round(testability, 3),
            'conformity': round(conformity, 3),
            'total': round(total, 3),
            'notes': notes
        }

    def _score_conformity(self, content: str, kind: str) -> float:
        """
        Score conformity to expected format for the content type.

        Args:
            content: Content to score
            kind: Type of content

        Returns:
            Conformity score (0-1)
        """
        if kind == 'requirements':
            return self._score_requirements_conformity(content)
        elif kind == 'design':
            return self._score_design_conformity(content)
        elif kind == 'tasks':
            return self._score_tasks_conformity(content)
        else:
            return 0.5  # Neutral score for unknown types

    def _score_requirements_conformity(self, content: str) -> float:
        """Score requirements conformity to EARS format."""
        conformity = 0.0

        # Check for EARS markers
        if re.search(r'\bWHEN\b.*\bTHE SYSTEM SHALL\b', content, re.IGNORECASE):
            conformity += 0.6
        elif re.search(r'\bWHEN\b', content, re.IGNORECASE) or re.search(r'\bTHE SYSTEM SHALL\b', content, re.IGNORECASE):
            conformity += 0.3

        # Check for acceptance criteria
        if re.search(r'\bAcceptance Criteria:\b', content, re.IGNORECASE):
            conformity += 0.2

        # Check for scenario structure
        if re.search(r'\bScenario:\b', content, re.IGNORECASE):
            conformity += 0.2

        return min(1, conformity)

    def _score_design_conformity(self, content: str) -> float:
        """Score design conformity to technical documentation format."""
        conformity = 0.0

        # Check for technical architecture section
        if re.search(r'\bTechnical Architecture\b', content, re.IGNORECASE):
            conformity += 0.3

        # Check for component descriptions
        if re.search(r'\bComponents?:\b', content, re.IGNORECASE):
            conformity += 0.2

        # Check for diagrams or visual elements
        if re.search(r'\bDiagram\b', content, re.IGNORECASE):
            conformity += 0.2

        # Check for data flow or sequence information
        if re.search(r'\b(Data Flow|Sequence|Flow)\b', content, re.IGNORECASE):
            conformity += 0.2

        # Check for security considerations
        if re.search(r'\bSecurity\b', content, re.IGNORECASE):
            conformity += 0.1

        return min(1, conformity)

    def _score_tasks_conformity(self, content: str) -> float:
        """Score tasks conformity to structured task format."""
        conformity = 0.0

        # Check for numbered tasks
        if re.search(r'^\d+\.', content, re.MULTILINE):
            conformity += 0.4

        # Check for outcomes
        if re.search(r'\bOutcome:\b', content, re.IGNORECASE):
            conformity += 0.3

        # Check for dependencies
        if re.search(r'\bDependencies?:\b', content, re.IGNORECASE):
            conformity += 0.2

        # Check for estimates
        if re.search(r'\bEstimate:\b', content, re.IGNORECASE):
            conformity += 0.1

        return min(1, conformity)

    def _calculate_combined_score(self, voidspec_score: Dict[str, Any],
                                trust_score: Dict[str, Any]) -> float:
        """
        Calculate combined score from VoidSpec and ZippyTrust metrics.

        Args:
            voidspec_score: Traditional VoidSpec scoring
            trust_score: ZippyTrust scoring

        Returns:
            Combined score (0-1)
        """
        # Weight traditional metrics (60%) and trust metrics (40%)
        voidspec_weight = 0.6
        trust_weight = 0.4

        voidspec_total = voidspec_score.get('total', 0.5)
        trust_total = trust_score.get('overall_score', 0.5)

        combined = (voidspec_total * voidspec_weight) + (trust_total * trust_weight)
        return round(combined, 3)

    def _determine_trust_level(self, score: float) -> str:
        """Determine trust level based on combined score."""
        if score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        else:
            return 'low'

    def _get_default_score(self) -> EnhancedRubricScore:
        """Get default score when scoring fails."""
        return EnhancedRubricScore(
            clarity=0.5,
            structure=0.5,
            testability=0.5,
            conformity=0.5,
            security_score=0.5,
            code_quality=0.5,
            documentation_quality=0.5,
            community_trust=0.5,
            total_score=0.5,
            trust_level='medium',
            notes=['Scoring failed - using default values']
        )

    async def generate_trust_insights(self, score: EnhancedRubricScore) -> List[str]:
        """
        Generate trust insights for marketplace integration.

        Args:
            score: Enhanced rubric score

        Returns:
            List of trust insights
        """
        insights = []

        if score.trust_level == 'high':
            insights.append("High trust score indicates reliable and well-structured content")
        elif score.trust_level == 'medium':
            insights.append("Medium trust score suggests content with moderate reliability")
        else:
            insights.append("Low trust score indicates content that may need review")

        # Add specific insights based on metrics
        if score.clarity < 0.6:
            insights.append("Content clarity could be improved for better understanding")

        if score.security_score < 0.7:
            insights.append("Security considerations may need additional attention")

        if score.code_quality > 0.8:
            insights.append("Content demonstrates high code quality standards")

        if score.documentation_quality > 0.8:
            insights.append("Documentation quality is excellent")

        return insights

    def get_scoring_statistics(self, scores: List[EnhancedRubricScore]) -> Dict[str, Any]:
        """
        Calculate scoring statistics from multiple scores.

        Args:
            scores: List of enhanced rubric scores

        Returns:
            Statistics dictionary
        """
        if not scores:
            return {'count': 0}

        total_scores = [s.total_score for s in scores]
        clarity_scores = [s.clarity for s in scores]
        trust_levels = [s.trust_level for s in scores]

        return {
            'count': len(scores),
            'average_total_score': round(sum(total_scores) / len(total_scores), 3),
            'average_clarity': round(sum(clarity_scores) / len(clarity_scores), 3),
            'trust_level_distribution': {
                'high': trust_levels.count('high'),
                'medium': trust_levels.count('medium'),
                'low': trust_levels.count('low')
            },
            'min_score': min(total_scores),
            'max_score': max(total_scores)
        }

