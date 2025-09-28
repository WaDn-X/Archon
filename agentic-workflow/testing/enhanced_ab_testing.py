"""
Enhanced A/B Testing System with ZippyTrust Integration

This module implements a sophisticated A/B testing system that combines
VoidSpec's rubric scoring with ZippyTrust validation and marketplace features.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.trust_manager import ZippyTrustManager, TrustScore
from plugins.marketplace import ZippyCoinMarketplace
from testing.enhanced_rubric import EnhancedRubricScorer

logger = logging.getLogger(__name__)

@dataclass
class ABTestConfig:
    """Configuration for A/B test."""
    test_id: str
    prompt: str
    versions: List[str]
    rubric_weights: Dict[str, float]
    trust_threshold: float
    marketplace_publish: bool
    created_at: str

@dataclass
class ABTestResult:
    """Enhanced A/B test result with trust scoring."""
    test_id: str
    prompt: str
    versions: List[Dict[str, Any]]
    winner: str
    winner_score: float
    trust_scores: Dict[str, float]
    marketplace_id: Optional[str]
    created_at: str
    metadata: Dict[str, Any]

class EnhancedABTesting:
    """
    Enhanced A/B testing system with ZippyTrust integration and marketplace features.
    """
    
    def __init__(self):
        self.trust_manager = ZippyTrustManager()
        self.marketplace = ZippyCoinMarketplace()
        self.rubric_scorer = EnhancedRubricScorer()
        self.test_results: Dict[str, ABTestResult] = {}
        
    async def run_prompt_comparison(self, prompt: str, versions: List[str] = None,
                                  config: Optional[ABTestConfig] = None) -> Dict[str, Any]:
        """
        Run comprehensive A/B test between prompt versions.
        
        Args:
            prompt: Feature description to test
            versions: List of versions to test
            config: Test configuration
            
        Returns:
            Dictionary containing A/B test results
        """
        if versions is None:
            versions = ['v1', 'v1b', 'enhanced']
            
        test_id = str(uuid.uuid4())
        
        if config is None:
            config = ABTestConfig(
                test_id=test_id,
                prompt=prompt,
                versions=versions,
                rubric_weights={
                    'clarity': 0.25,
                    'structure': 0.25,
                    'testability': 0.25,
                    'conformity': 0.25
                },
                trust_threshold=0.7,
                marketplace_publish=True,
                created_at=datetime.now().isoformat()
            )
        
        try:
            test_results = []
            trust_scores = {}
            
            for version in versions:
                # Generate content for this version
                content = await self._generate_version_content(prompt, version)
                
                # Score with enhanced rubric
                rubric_score = await self.rubric_scorer.score_content(content, 'requirements')
                
                # Validate with ZippyTrust
                trust_score = await self._validate_with_zippytrust(content, version)
                trust_scores[version] = trust_score.zippy_trust_score
                
                # Calculate weighted score
                weighted_score = self._calculate_weighted_score(rubric_score, trust_score, config.rubric_weights)
                
                test_results.append({
                    'version': version,
                    'content': content,
                    'rubric_score': asdict(rubric_score),
                    'trust_score': trust_score.zippy_trust_score,
                    'weighted_score': weighted_score,
                    'metadata': {
                        'generation_time': datetime.now().isoformat(),
                        'content_length': len(content),
                        'trust_validation': trust_score.verification_status
                    }
                })
            
            # Determine winner
            winner = max(test_results, key=lambda x: x['weighted_score'])
            
            # Create A/B test result
            ab_result = ABTestResult(
                test_id=test_id,
                prompt=prompt,
                versions=test_results,
                winner=winner['version'],
                winner_score=winner['weighted_score'],
                trust_scores=trust_scores,
                marketplace_id=None,
                created_at=datetime.now().isoformat(),
                metadata={
                    'config': asdict(config),
                    'total_versions': len(versions),
                    'average_trust_score': sum(trust_scores.values()) / len(trust_scores)
                }
            )
            
            # Store result
            self.test_results[test_id] = ab_result
            
            # Publish to marketplace if configured
            if config.marketplace_publish:
                marketplace_id = await self._publish_to_marketplace(ab_result)
                ab_result.marketplace_id = marketplace_id
            
            logger.info(f"A/B test completed. Winner: {winner['version']} (score: {winner['weighted_score']})")
            
            return {
                'success': True,
                'test_id': test_id,
                'result': asdict(ab_result)
            }
            
        except Exception as e:
            logger.error(f"Failed to run A/B test: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_id': test_id
            }
    
    async def score_with_zippytrust(self, content: str, kind: str) -> Dict[str, Any]:
        """
        Score content using both VoidSpec rubric and ZippyTrust.
        
        Args:
            content: Content to score
            kind: Type of content (requirements, design, tasks)
            
        Returns:
            Dictionary containing combined scoring results
        """
        try:
            # Score with enhanced rubric
            rubric_score = await self.rubric_scorer.score_content(content, kind)
            
            # Validate with ZippyTrust
            trust_score = await self._validate_with_zippytrust(content, kind)
            
            # Generate trust insights
            trust_insights = await self.rubric_scorer.generate_trust_insights(rubric_score)
            
            return {
                'success': True,
                'rubric_score': asdict(rubric_score),
                'trust_score': asdict(trust_score),
                'trust_insights': trust_insights,
                'combined_score': (rubric_score.total + trust_score.zippy_trust_score) / 2,
                'scored_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to score content: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def publish_to_marketplace(self, test_result: ABTestResult) -> bool:
        """
        Publish A/B test results to ZippyCoin marketplace.
        
        Args:
            test_result: A/B test result to publish
            
        Returns:
            True if published successfully
        """
        try:
            # Create marketplace listing
            listing_data = {
                'type': 'ab_test_result',
                'title': f"A/B Test: {test_result.prompt[:50]}...",
                'description': f"Comprehensive A/B test results for prompt optimization",
                'content': asdict(test_result),
                'tags': ['ab_testing', 'prompt_optimization', 'requirements'],
                'pricing': {
                    'currency': 'zippycoin',
                    'amount': 10.0  # Base price for A/B test results
                },
                'metadata': {
                    'winner_version': test_result.winner,
                    'winner_score': test_result.winner_score,
                    'total_versions': len(test_result.versions),
                    'trust_scores': test_result.trust_scores
                }
            }
            
            # Publish to marketplace
            marketplace_id = await self.marketplace.create_listing(listing_data)
            
            logger.info(f"Published A/B test result to marketplace: {marketplace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish to marketplace: {e}")
            return False
    
    async def _generate_version_content(self, prompt: str, version: str) -> str:
        """Generate content for a specific version."""
        # This would integrate with the multi-provider AI system
        # For now, return mock content
        return f"# Generated Content for {version}\n\n{prompt}\n\n## Implementation\n\nThis is mock content for version {version}."
    
    async def _validate_with_zippytrust(self, content: str, version: str) -> TrustScore:
        """Validate content with ZippyTrust."""
        try:
            metadata = {
                'name': f"ab_test_content_{version}",
                'description': f"Content generated for A/B test version {version}",
                'author': 'ab_testing_system',
                'version': '1.0.0',
                'dependencies': [],
                'tags': ['ab_testing', 'requirements', version],
                'license': 'MIT'
            }
            
            trust_score = await self.trust_manager.verify_plugin(content, metadata)
            return trust_score
            
        except Exception as e:
            logger.error(f"Failed to validate with ZippyTrust: {e}")
            return TrustScore(
                plugin_id=f"ab_test_{version}",
                zippy_trust_score=0.1,
                verification_status='failed',
                code_quality_score=0.1,
                security_checks={},
                audit_trail=[f"Validation failed: {str(e)}"],
                last_updated=datetime.now().isoformat()
            )
    
    def _calculate_weighted_score(self, rubric_score: Any, trust_score: TrustScore, 
                                weights: Dict[str, float]) -> float:
        """Calculate weighted score combining rubric and trust scores."""
        # Combine rubric score with trust score
        combined_score = (rubric_score.total + trust_score.zippy_trust_score) / 2
        
        # Apply weights if provided
        if weights:
            weighted_score = sum(
                getattr(rubric_score, key, 0) * weight 
                for key, weight in weights.items()
            )
            # Combine with trust score
            final_score = (weighted_score + trust_score.zippy_trust_score) / 2
        else:
            final_score = combined_score
            
        return round(final_score, 3)
    
    async def _publish_to_marketplace(self, ab_result: ABTestResult) -> Optional[str]:
        """Publish A/B test result to marketplace."""
        try:
            return await self.publish_to_marketplace(ab_result)
        except Exception as e:
            logger.error(f"Failed to publish to marketplace: {e}")
            return None
    
    def get_test_result(self, test_id: str) -> Optional[ABTestResult]:
        """Get A/B test result by ID."""
        return self.test_results.get(test_id)
    
    def list_test_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent A/B test results."""
        results = list(self.test_results.values())
        results.sort(key=lambda x: x.created_at, reverse=True)
        return [asdict(result) for result in results[:limit]]
    
    def export_test_results(self, format: str = 'json') -> str:
        """Export A/B test results in specified format."""
        if format == 'json':
            return json.dumps([asdict(result) for result in self.test_results.values()], indent=2)
        elif format == 'csv':
            # Convert to CSV format
            csv_lines = ['test_id,prompt,winner,winner_score,created_at,marketplace_id']
            for result in self.test_results.values():
                csv_lines.append(f"{result.test_id},{result.prompt},{result.winner},{result.winner_score},{result.created_at},{result.marketplace_id or ''}")
            return '\n'.join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

