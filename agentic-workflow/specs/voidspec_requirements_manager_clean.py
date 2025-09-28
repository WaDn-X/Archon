
"""
VoidSpec-Inspired Requirements Manager

This module implements an enhanced requirements manager that incorporates
VoidSpec's EARS approach with ZippyTrust validation and A/B testing capabilities.
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
class RubricScore:
    """VoidSpec-inspired rubric scoring for requirements."""
    clarity: float  # 0-1: penalize vague terms and long lines
    structure: float  # 0-1: presence of headers/sections
    testability: float  # 0-1: look for WHEN/THEN or explicit outcomes
    conformity: float  # 0-1: EARS compliance
    total: float  # average of all scores
    notes: List[str]  # specific feedback

@dataclass
class ABTestResult:
    """A/B test result for prompt versions."""
    feature: str
    versions: List[Dict[str, Any]]  # version info with scores
    winner: str
    created_at: str
    trust_score: Optional[float] = None

class VoidSpecRequirementsManager:
    """
    Enhanced requirements manager incorporating VoidSpec's EARS approach
    with ZippyTrust validation and A/B testing capabilities.
    """
    
    def __init__(self):
        self.ai_system = MultiProviderAISystem()
        self.trust_manager = ZippyTrustManager()
        self.ab_testing = EnhancedABTesting()
        self.rubric_scorer = EnhancedRubricScorer()
        self.requirements_db: Dict[str, Requirement] = {}
        self.traceability_links: List[TraceabilityLink] = []
        self.ab_results: List[ABTestResult] = []
        
    async def generate_requirements(self, prompt: str, version: str = 'v1', 
                                  use_ai: bool = True) -> Dict[str, Any]:
        """
        Generate requirements using VoidSpec's AI-powered approach.
        
        Args:
            prompt: User's feature description
            version: Prompt version (v1, v1b, enhanced)
            use_ai: Whether to use AI generation or fallback
            
        Returns:
            Dictionary containing generated requirements and metadata
        """
        try:
            if use_ai:
                # Try AI generation first
                try:
                    requirements_content = await self._generate_with_ai(prompt, version)
                except Exception as e:
                    logger.warning(f"AI generation failed: {e}, using fallback")
                    requirements_content = self._generate_fallback(prompt)
            else:
                requirements_content = self._generate_fallback(prompt)
            
            # Parse the generated content into structured requirements
            parsed_requirements = self._parse_ears_content(requirements_content)
            
            created_requirements = []
            
            for req_data in parsed_requirements:
                # Generate unique ID
                req_id = str(uuid.uuid4())
                
                # Create requirement object
                requirement = Requirement(
                    id=req_id,
                    title=req_data.get('title', 'Untitled Requirement'),
                    description=req_data.get('description', ''),
                    type=req_data.get('type', 'shall'),
                    actor=req_data.get('actor', 'system'),
                    condition=req_data.get('condition'),
                    action=req_data.get('action', ''),
                    object=req_data.get('object', ''),
                    constraint=req_data.get('constraint'),
                    priority=req_data.get('priority', 'medium'),
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                    author='ai_generated',
                    wallet_address='system'
                )
                
                # Store requirement
                self.requirements_db[req_id] = requirement
                
                # Score the requirement using VoidSpec's rubric
                rubric_score = await self.score_requirements(requirements_content)
                
                # Validate with ZippyTrust
                trust_score = await self._validate_with_zippytrust(requirement)
                requirement.trust_score = trust_score.zippy_trust_score
                requirement.validation_status = trust_score.verification_status
                
                req_dict = asdict(requirement)
                req_dict['rubric_score'] = asdict(rubric_score)
                
                created_requirements.append(req_dict)
            
            logger.info(f"Generated {len(created_requirements)} requirements using {version}")
            
            return {
                'success': True,
                'requirements': created_requirements,
                'total_count': len(created_requirements),
                'version': version,
                'ai_generated': use_ai,
                'raw_content': requirements_content
            }
            
        except Exception as e:
            logger.error(f"Failed to generate requirements: {e}")
            return {
                'success': False,
                'error': str(e),
                'requirements': []
            }
    
    async def run_ab_test(self, prompt: str, versions: List[str] = None,
                         provider: str = "grok", num_runs: int = 3) -> Dict[str, Any]:
        """
        Run enhanced A/B test between different prompt versions with ZippyTrust integration.

        Args:
            prompt: Feature description to test
            versions: List of versions to test
            provider: AI provider to use
            num_runs: Number of test runs per version

        Returns:
            Dictionary containing enhanced A/B test results
        """
        if versions is None:
            versions = ['v1', 'v1b', 'enhanced']

        try:
            # Use the enhanced A/B testing system
            test_result = await self.ab_testing.run_prompt_comparison(
                base_prompt=prompt,
                versions={version: f"{prompt} (Version: {version})" for version in versions},
                provider=provider,
                num_runs=num_runs,
                content_type="requirements"
            )

            # Enhance results with rubric scoring and trust validation
            enhanced_results = []
            for version_result in test_result.get('versions_tested', []):
                version_name = version_result.get('version', '')

                # Generate sample requirements for scoring
                sample_reqs = await self.generate_requirements(prompt, version_name, use_ai=True)
                rubric_score = None
                trust_score = None

                if sample_reqs['success']:
                    # Score with rubric
                    rubric_score = await self.score_requirements(sample_reqs['raw_content'])

                    # Validate with ZippyTrust
                    trust_score = await self._validate_sample_with_trust(sample_reqs)

                enhanced_result = {
                    'version': version_name,
                    'score': asdict(rubric_score) if rubric_score else None,
                    'trust_score': trust_score.zippy_trust_score if trust_score else 0.0,
                    'requirements_count': sample_reqs.get('total_count', 0),
                    'ai_generated': sample_reqs.get('ai_generated', False),
                    'performance_metrics': version_result.get('metrics', {}),
                    'content_quality': version_result.get('quality_score', 0.0)
                }
                enhanced_results.append(enhanced_result)

            # Determine winner based on combined scoring
            winner = self._determine_enhanced_winner(enhanced_results)

            # Create enhanced A/B test result
            ab_result = ABTestResult(
                feature=prompt,
                versions=enhanced_results,
                winner=winner['version'],
                created_at=datetime.now().isoformat(),
                trust_score=winner.get('combined_score', 0.0)
            )

            # Store the result
            self.ab_results.append(ab_result)

            logger.info(f"Enhanced A/B test completed. Winner: {winner['version']} (combined score: {winner.get('combined_score', 0.0)})")

            return {
                'success': True,
                'feature': prompt,
                'versions': enhanced_results,
                'winner': winner['version'],
                'winner_score': winner.get('combined_score', 0.0),
                'provider': provider,
                'num_runs': num_runs,
                'created_at': ab_result.created_at,
                'recommendations': self._generate_test_recommendations(enhanced_results)
            }

        except Exception as e:
            logger.error(f"Failed to run enhanced A/B test: {e}")
            return {
                'success': False,
                'error': str(e),
                'feature': prompt
            }

    def _determine_enhanced_winner(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determine winner based on combined rubric, trust, and performance scores.

        Args:
            results: List of test results

        Returns:
            Winner information with combined scoring
        """
        scored_results = []

        for result in results:
            rubric_score = result.get('score', {}).get('total', 0.0)
            trust_score = result.get('trust_score', 0.0)
            quality_score = result.get('content_quality', 0.0)

            # Weighted combination: 40% rubric, 40% trust, 20% quality
            combined_score = (
                rubric_score * 0.4 +
                trust_score * 0.4 +
                quality_score * 0.2
            )

            scored_results.append({
                **result,
                'combined_score': combined_score
            })

        # Return the result with highest combined score
        return max(scored_results, key=lambda x: x['combined_score'])

    def _generate_test_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations based on test results.

        Args:
            results: Test results to analyze

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze rubric scores
        rubric_scores = [r.get('score', {}).get('total', 0.0) for r in results if r.get('score')]
        if rubric_scores:
            avg_rubric = sum(rubric_scores) / len(rubric_scores)
            if avg_rubric < 0.7:
                recommendations.append("Consider improving requirement clarity and structure")

        # Analyze trust scores
        trust_scores = [r.get('trust_score', 0.0) for r in results]
        if trust_scores:
            avg_trust = sum(trust_scores) / len(trust_scores)
            if avg_trust < 0.8:
                recommendations.append("Enhance trust validation and security measures")

        # Version-specific recommendations
        for result in results:
            version = result.get('version', '')
            rubric_total = result.get('score', {}).get('total', 0.0)

            if rubric_total < 0.5:
                recommendations.append(f"Version {version} needs significant improvement in requirement quality")
            elif rubric_total > 0.9:
                recommendations.append(f"Version {version} shows excellent requirement quality")

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
            voidspec_overall = voidspec_score.get('overall_score', 0)

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
