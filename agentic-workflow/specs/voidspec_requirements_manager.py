"""
VoidSpec Requirements Manager

Enhanced requirements manager that generates and manages software requirements
using EARS (Easy Approach to Requirements Syntax) with VoidSpec integration
and ZippyTrust validation.
"""

import re
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import logging

from ..ai.multi_provider_ai import MultiProviderAISystem
from ..plugins.trust_manager import ZippyTrustManager, TrustScore
from ..testing.enhanced_ab_testing import EnhancedABTesting
from ..testing.enhanced_rubric import EnhancedRubricScorer
from .requirements_manager import Requirement, TraceabilityLink

logger = logging.getLogger(__name__)

@dataclass
class ABTestResult:
    """Results from A/B testing different requirement versions."""
    id: str
    feature: str
    versions_tested: List[str]
    winner: str
    winner_score: float
    trust_score: Optional[float]
    created_at: datetime

class VoidSpecRequirementsManager:
    """
    Enhanced requirements manager with VoidSpec integration.

    This manager generates requirements using AI, validates them against
    EARS patterns, and uses ZippyTrust for quality assurance.
    """

    def __init__(self):
        self.ai_system = MultiProviderAISystem()
        self.trust_manager = ZippyTrustManager()
        self.ab_testing = EnhancedABTesting()
        self.rubric_scorer = EnhancedRubricScorer()
        self.requirements_db: Dict[str, Requirement] = {}
        self.traceability_links: List[TraceabilityLink] = []
        self.ab_results: List[ABTestResult] = []

    async def generate_requirements(
        self,
        user_story: str,
        version: str = "ears",
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Generate requirements from a user story using specified approach.

        Args:
            user_story: User story or feature description
            version: Version/approach to use ('ears', 'traditional', etc.)
            use_ai: Whether to use AI for generation

        Returns:
            Dictionary containing generated requirements and metadata
        """
        try:
            if use_ai:
                content = await self._generate_with_ai(user_story, version)
            else:
                content = self._generate_template(user_story, version)

            # Parse requirements from content
            requirements = self._parse_requirements(content, version)

            # Validate EARS compliance
            validation_results = self._validate_ears_compliance(requirements)

            # Create requirement objects
            req_objects = []
            for req_data in requirements:
                req_obj = Requirement(
                    id=f"req_{uuid.uuid4().hex[:8]}",
                    title=req_data.get('title', f"Requirement {len(req_objects) + 1}"),
                    description=req_data.get('description', ''),
                    type=req_data.get('type', 'shall'),
                    actor=req_data.get('actor', 'system'),
                    condition=req_data.get('condition'),
                    action=req_data.get('action'),
                    object=req_data.get('object'),
                    constraint=req_data.get('constraint'),
                    priority=req_data.get('priority', 'medium'),
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                    author="ai_generated",
                    wallet_address="system"
                )
                req_objects.append(req_obj)
                self.requirements_db[req_obj.id] = req_obj

            return {
                'success': True,
                'content': content,
                'requirements': [asdict(req) for req in req_objects],
                'validation_results': validation_results,
                'version': version,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate requirements: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _generate_with_ai(self, prompt: str, version: str) -> str:
        """
        Generate requirements using AI.

        Args:
            prompt: User's feature description
            version: Prompt version to use

        Returns:
            Generated requirements content
        """
        if version == "ears":
            prompt_template = f"""
            Generate software requirements using EARS (Easy Approach to Requirements Syntax):

            FEATURE: {prompt}

            Use these EARS patterns:
            1. Ubiquitous: "The SYSTEM SHALL [function]"
            2. Event-driven: "WHEN [condition] THE SYSTEM SHALL [response]"
            3. State-driven: "WHILE [state] THE SYSTEM SHALL [behavior]"
            4. Optional: "The SYSTEM SHOULD [function]"
            5. Unwanted: "The SYSTEM SHALL NOT [undesirable behavior]"

            Generate 5-10 requirements covering:
            - Functional requirements
            - Non-functional requirements (performance, security, usability)
            - Edge cases and error handling

            Format each requirement clearly with EARS pattern identification.
            """
        else:
            prompt_template = f"""
            Generate traditional software requirements for: {prompt}

            Include:
            - Functional requirements
            - Non-functional requirements
            - Business rules
            - Constraints

            Use clear, unambiguous language.
            """

        return await self.ai_system.generate_content(
            prompt=prompt_template,
            content_type="requirements"
        )

    def _generate_template(self, user_story: str, version: str) -> str:
        """Generate requirements using templates (fallback when AI unavailable)."""
        if version == "ears":
            return f"""
# Requirements for: {user_story}

## Functional Requirements

WHEN a user performs the primary action,
THE SYSTEM SHALL provide the expected response within 2 seconds.

WHEN invalid input is provided,
THE SYSTEM SHALL display an appropriate error message and prevent invalid operations.

WHILE the system is processing,
THE SYSTEM SHALL show progress indicators to the user.

## Non-Functional Requirements

The SYSTEM SHALL handle up to 1000 concurrent users without performance degradation.

The SYSTEM SHALL encrypt all sensitive data at rest and in transit.

The SYSTEM SHOULD provide a response time of less than 500ms for common operations.
"""
        else:
            return f"""
# Traditional Requirements for: {user_story}

1. The system shall allow users to perform the primary function.
2. The system shall validate all user inputs.
3. The system shall provide appropriate error messages.
4. The system shall maintain data integrity.
5. The system shall meet performance requirements.
"""

    def _parse_requirements(self, content: str, version: str) -> List[Dict[str, Any]]:
        """Parse requirements from generated content."""
        requirements = []

        # Split content into lines and find requirement statements
        lines = content.split('\n')
        current_req = {}

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for EARS patterns
            if version == "ears":
                if line.upper().startswith(('WHEN', 'WHILE', 'THE SYSTEM SHALL', 'THE SYSTEM SHOULD', 'THE SYSTEM SHALL NOT')):
                    if current_req:
                        requirements.append(current_req)

                    current_req = self._parse_ears_requirement(line)
            else:
                # Traditional parsing
                if re.match(r'^\d+\.', line):
                    if current_req:
                        requirements.append(current_req)

                    current_req = {
                        'title': line,
                        'description': line,
                        'type': 'shall'
                    }

        if current_req:
            requirements.append(current_req)

        return requirements

    def _parse_ears_requirement(self, line: str) -> Dict[str, Any]:
        """Parse a single EARS requirement."""
        req = {
            'description': line,
            'type': 'shall',
            'actor': 'system'
        }

        # Extract components based on EARS pattern
        if line.upper().startswith('WHEN'):
            # Event-driven: WHEN [condition] THE SYSTEM SHALL [response]
            parts = line.split(' THE SYSTEM SHALL ')
            if len(parts) == 2:
                req['condition'] = parts[0].replace('WHEN ', '').strip()
                req['action'] = parts[1].strip()
                req['type'] = 'event_driven'

        elif line.upper().startswith('WHILE'):
            # State-driven: WHILE [state] THE SYSTEM SHALL [behavior]
            parts = line.split(' THE SYSTEM SHALL ')
            if len(parts) == 2:
                req['condition'] = parts[0].replace('WHILE ', '').strip()
                req['action'] = parts[1].strip()
                req['type'] = 'state_driven'

        elif 'SHALL NOT' in line.upper():
            # Unwanted behavior
            req['action'] = line.split('SHALL NOT')[1].strip()
            req['type'] = 'unwanted'

        elif 'SHOULD' in line.upper():
            # Optional
            req['action'] = line.split('SHOULD')[1].strip()
            req['type'] = 'should'

        else:
            # Ubiquitous
            req['action'] = line.replace('The SYSTEM SHALL', '').strip()
            req['type'] = 'ubiquitous'

        return req

    def _validate_ears_compliance(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate requirements against EARS compliance."""
        total_reqs = len(requirements)
        compliant_reqs = 0
        issues = []

        ears_patterns = ['ubiquitous', 'event_driven', 'state_driven', 'should', 'unwanted']

        for req in requirements:
            req_type = req.get('type', '')
            if req_type in ears_patterns:
                compliant_reqs += 1
            else:
                issues.append(f"Unknown requirement type: {req_type}")

        compliance_score = compliant_reqs / total_reqs if total_reqs > 0 else 0

        return {
            'compliance_score': compliance_score,
            'compliant_requirements': compliant_reqs,
            'total_requirements': total_reqs,
            'issues': issues
        }

    async def score_requirements(self, content: str) -> Dict[str, Any]:
        """Score requirements using VoidSpec rubric."""
        try:
            # Basic rubric scoring
            scores = {
                'completeness': self._score_completeness(content),
                'clarity': self._score_clarity(content),
                'consistency': self._score_consistency(content),
                'testability': self._score_testability(content),
                'feasibility': self._score_feasibility(content)
            }

            total_score = sum(scores.values()) / len(scores)

            return {
                'scores': scores,
                'total': total_score,
                'grade': self._get_grade(total_score)
            }

        except Exception as e:
            logger.error(f"Failed to score requirements: {e}")
            return {'error': str(e)}

    def _score_completeness(self, content: str) -> float:
        """Score completeness of requirements."""
        criteria = [
            'functional requirements',
            'non-functional requirements',
            'edge cases',
            'error handling',
            'constraints'
        ]

        score = 0
        for criterion in criteria:
            if criterion.lower() in content.lower():
                score += 1

        return score / len(criteria)

    def _score_clarity(self, content: str) -> float:
        """Score clarity of requirements."""
        # Check for ambiguous words
        ambiguous_words = ['etc', 'and/or', 'as appropriate', 'reasonable', 'sufficient']
        penalty = 0

        for word in ambiguous_words:
            if word in content.lower():
                penalty += 0.1

        return max(0, 1.0 - penalty)

    def _score_consistency(self, content: str) -> float:
        """Score consistency of requirements."""
        # Check for consistent terminology
        shall_count = content.upper().count('SHALL')
        should_count = content.upper().count('SHOULD')
        may_count = content.upper().count('MAY')

        if shall_count > 0 and (should_count == 0 and may_count == 0):
            return 0.8  # Good use of modal verbs
        elif shall_count == 0:
            return 0.5  # No mandatory requirements
        else:
            return 0.9  # Mixed usage is acceptable

    def _score_testability(self, content: str) -> float:
        """Score testability of requirements."""
        testable_indicators = [
            'shall', 'should', 'when', 'if', 'then',
            'response time', 'performance', 'accuracy'
        ]

        score = 0
        for indicator in testable_indicators:
            if indicator in content.lower():
                score += 1

        return min(1.0, score / len(testable_indicators))

    def _score_feasibility(self, content: str) -> float:
        """Score feasibility of requirements."""
        # Check for realistic constraints
        unrealistic_patterns = [
            'infinite', 'unlimited', 'perfect', '100% uptime',
            'zero latency', 'instantaneous'
        ]

        penalty = 0
        for pattern in unrealistic_patterns:
            if pattern in content.lower():
                penalty += 0.2

        return max(0, 1.0 - penalty)

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'

    async def run_ab_test(self, prompt: str, versions: List[str] = None) -> Dict[str, Any]:
        """
        Run A/B test between different prompt versions.

        Args:
            prompt: Feature description to test
            versions: List of versions to test (default: ['v1', 'v1b'])

        Returns:
            Dictionary containing A/B test results
        """
        if versions is None:
            versions = ['ears', 'traditional']

        try:
            test_results = []

            for version in versions:
                # Generate requirements for this version
                result = await self.generate_requirements(prompt, version, use_ai=True)

                if result['success']:
                    # Score the generated content
                    rubric_score = await self.score_requirements(result['content'])

                    test_results.append({
                        'version': version,
                        'content': result['content'],
                        'score': rubric_score['total'],
                        'grade': rubric_score['grade']
                    })

            # Determine winner
            if test_results:
                winner = max(test_results, key=lambda x: x['score'])

                # Store A/B test result
                ab_result = ABTestResult(
                    id=f"ab_{uuid.uuid4().hex[:8]}",
                    feature=prompt[:50],
                    versions_tested=versions,
                    winner=winner['version'],
                    winner_score=winner['score'],
                    trust_score=None,  # Could be calculated separately
                    created_at=datetime.now()
                )

                self.ab_results.append(ab_result)

                return {
                    'success': True,
                    'winner': winner['version'],
                    'winner_score': winner['score'],
                    'all_results': test_results,
                    'recommendations': self._generate_ab_recommendations(test_results)
                }
            else:
                return {'success': False, 'error': 'No valid test results'}

        except Exception as e:
            logger.error(f"A/B test failed: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_ab_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on A/B test results."""
        recommendations = []

        if not results:
            return recommendations

        # Find best and worst performers
        best = max(results, key=lambda x: x['score'])
        worst = min(results, key=lambda x: x['score'])

        if best['score'] > worst['score']:
            recommendations.append(f"Use {best['version']} format for better requirement quality")
            recommendations.append(f"{best['version']} scored {best['score']:.2f} vs {worst['version']} {worst['score']:.2f}")

        # Check for significant differences
        score_range = best['score'] - worst['score']
        if score_range > 0.3:
            recommendations.append(f"Significant quality difference detected ({score_range:.2f})")
        elif score_range > 0.1:
            recommendations.append(f"Moderate quality difference detected ({score_range:.2f})")
        else:
            recommendations.append("Results are very close, both approaches are viable")

        # Overall quality assessment
        avg_score = sum(r['score'] for r in results) / len(results)
        if avg_score > 0.8:
            recommendations.append("High quality requirements generated overall")
        elif avg_score > 0.6:
            recommendations.append("Good quality requirements with room for improvement")
        else:
            recommendations.append("Requirements need significant improvement")

        return recommendations

    async def score_with_enhanced_rubric(self, content: str) -> Dict[str, Any]:
        """
        Score requirements using the enhanced rubric scorer system.

        Args:
            content: Requirements content to score

        Returns:
            Enhanced scoring results
        """
        try:
            # Use the enhanced rubric scorer
            enhanced_score = await self.rubric_scorer.score_content(
                content, "requirements"
            )

            # Also use the traditional VoidSpec rubric for comparison
            voidspec_score = await self.score_requirements(content)

            return {
                'enhanced_score': enhanced_score,
                'voidspec_score': voidspec_score,
                'comparison': self._compare_scoring_methods(enhanced_score, voidspec_score)
            }

        except Exception as e:
            logger.error(f"Failed to score with enhanced rubric: {e}")
            return {
                'error': str(e),
                'enhanced_score': None,
                'voidspec_score': None
            }

    def _compare_scoring_methods(
        self,
        enhanced_score: Dict[str, Any],
        voidspec_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare different scoring methods."""
        try:
            enhanced_overall = enhanced_score.get('overall_score', 0)
            voidspec_overall = voidspec_score.get('total', 0)

            return {
                'enhanced_vs_voidspec': enhanced_overall - voidspec_overall,
                'consistency_check': abs(enhanced_overall - voidspec_overall) < 0.2,
                'recommendation': 'enhanced' if enhanced_overall > voidspec_overall else 'voidspec'
            }
        except Exception as e:
            return {'comparison_error': str(e)}

    async def generate_comprehensive_specification(
        self,
        user_story: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive specification using all available tools.

        Args:
            user_story: User story or feature description
            context: Additional context information

        Returns:
            Complete specification package
        """
        try:
            # Generate requirements using multiple approaches
            ears_reqs = await self.generate_requirements(user_story, "ears", use_ai=True)
            traditional_reqs = await self.generate_requirements(user_story, "traditional", use_ai=True)

            # Run A/B testing between approaches
            ab_results = await self.run_ab_test(user_story, ["ears", "traditional"])

            # Score both versions
            ears_score = await self.score_with_enhanced_rubric(ears_reqs.get('content', ''))
            traditional_score = await self.score_with_enhanced_rubric(traditional_reqs.get('content', ''))

            # Generate design artifacts
            from .voidspec_design_manager import VoidSpecDesignManager, ArchitectureType
            design_manager = VoidSpecDesignManager()

            # Use the better performing requirements for design
            best_reqs = ears_reqs if ears_score['enhanced_score'].get('overall_score', 0) > traditional_score['enhanced_score'].get('overall_score', 0) else traditional_reqs

            design = await design_manager.generate_architecture_design(
                best_reqs,
                ArchitectureType.MICROSERVICES
            )

            # Validate trust scores
            trust_validation = await self._validate_with_trust_system(
                ears_reqs, traditional_reqs, design
            )

            return {
                'success': True,
                'user_story': user_story,
                'requirements': {
                    'ears': ears_reqs,
                    'traditional': traditional_reqs
                },
                'ab_testing': ab_results,
                'scoring': {
                    'ears': ears_score,
                    'traditional': traditional_score
                },
                'design': design,
                'trust_validation': trust_validation,
                'recommendations': self._generate_final_recommendations(
                    ears_score, traditional_score, ab_results, design
                )
            }

        except Exception as e:
            logger.error(f"Failed to generate comprehensive specification: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _validate_with_trust_system(
        self,
        ears_reqs: Dict[str, Any],
        traditional_reqs: Dict[str, Any],
        design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate all artifacts with the trust system."""
        try:
            # Calculate trust scores for each artifact
            ears_trust = await self.trust_manager.calculate_trust_score(
                design_content=ears_reqs.get('content', ''),
                validation_results={'type': 'requirements'}
            )

            traditional_trust = await self.trust_manager.calculate_trust_score(
                design_content=traditional_reqs.get('content', ''),
                validation_results={'type': 'requirements'}
            )

            design_trust = design.get('trust_score')

            return {
                'ears_requirements_trust': ears_trust.overall_score if ears_trust else 0,
                'traditional_requirements_trust': traditional_trust.overall_score if traditional_trust else 0,
                'design_trust': design_trust.overall_score if design_trust else 0,
                'overall_confidence': self._calculate_overall_confidence([
                    ears_trust, traditional_trust, design_trust
                ])
            }

        except Exception as e:
            logger.error(f"Trust validation failed: {e}")
            return {'error': str(e)}

    def _calculate_overall_confidence(self, trust_scores: List[Optional[TrustScore]]) -> float:
        """Calculate overall confidence from multiple trust scores."""
        valid_scores = [ts.overall_score for ts in trust_scores if ts is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

    def _generate_final_recommendations(
        self,
        ears_score: Dict[str, Any],
        traditional_score: Dict[str, Any],
        ab_results: Dict[str, Any],
        design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate final recommendations based on all analysis."""
        try:
            ears_overall = ears_score['enhanced_score'].get('overall_score', 0)
            traditional_overall = traditional_score['enhanced_score'].get('overall_score', 0)
            design_success = design.get('success', False)

            recommendations = {
                'preferred_approach': 'ears' if ears_overall > traditional_overall else 'traditional',
                'confidence_level': 'high' if abs(ears_overall - traditional_overall) > 0.2 else 'medium',
                'design_readiness': 'ready' if design_success else 'needs_work',
                'next_steps': []
            }

            # Add specific recommendations
            if ears_overall > traditional_overall:
                recommendations['next_steps'].append('Use EARS format for all future requirements')
                recommendations['next_steps'].append('Implement generated design artifacts')
            else:
                recommendations['next_steps'].append('Refine traditional requirements with EARS elements')
                recommendations['next_steps'].append('Re-run design generation with improved requirements')

            if not design_success:
                recommendations['next_steps'].append('Address design generation issues')
                recommendations['next_steps'].append('Validate requirements completeness')

            return recommendations

        except Exception as e:
            return {'error': f'Failed to generate recommendations: {str(e)}'}

    def get_requirement_text(self, requirement: Requirement) -> str:
        """Convert requirement object to readable text."""
        text_parts = []

        if requirement.title:
            text_parts.append(f"Title: {requirement.title}")

        if requirement.description:
            text_parts.append(f"Description: {requirement.description}")

        if requirement.type:
            text_parts.append(f"Type: {requirement.type}")

        if requirement.priority:
            text_parts.append(f"Priority: {requirement.priority}")

        if requirement.author:
            text_parts.append(f"Author: {requirement.author}")

        return "\n".join(text_parts)

    def get_ab_results(self) -> List[Dict[str, Any]]:
        """Get all A/B test results."""
        return [asdict(result) for result in self.ab_results]

    def export_ab_results(self, format: str = 'json') -> str:
        """Export A/B test results in specified format."""
        if format == 'json':
            return json.dumps([asdict(result) for result in self.ab_results], indent=2)
        elif format == 'csv':
            # Convert to CSV format
            csv_lines = ['feature,winner,created_at,trust_score']
            for result in self.ab_results:
                csv_lines.append(f"{result.feature},{result.winner},{result.created_at},{result.trust_score or 0}")
            return '\n'.join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
