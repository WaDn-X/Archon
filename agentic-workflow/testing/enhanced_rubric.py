"""
Enhanced Rubric Scoring System

This module implements an enhanced rubric scoring system that combines
VoidSpec's metrics with ZippyTrust validation and generates trust insights.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EnhancedRubricScore:
    """Enhanced rubric score combining VoidSpec and ZippyTrust metrics."""
    # VoidSpec metrics (0-1 scale)
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
    total: float
    trust_level: str  # 'high', 'medium', 'low'
    notes: List[str]
    scored_at: str

class EnhancedRubricScorer:
    """
    Enhanced rubric scoring system combining VoidSpec and ZippyTrust metrics.
    """
    
    def __init__(self):
        self.weights = {
            'clarity': 0.15,
            'structure': 0.15,
            'testability': 0.20,
            'conformity': 0.15,
            'security_score': 0.10,
            'code_quality': 0.10,
            'documentation_quality': 0.10,
            'community_trust': 0.05
        }
    
    async def score_content(self, content: str, kind: str) -> EnhancedRubricScore:
        """
        Score content using enhanced rubric system.
        
        Args:
            content: Content to score
            kind: Type of content (requirements, design, tasks)
            
        Returns:
            EnhancedRubricScore object
        """
        try:
            notes = []
            
            # Score VoidSpec metrics
            clarity = self._score_clarity(content, notes)
            structure = self._score_structure(content, notes)
            testability = self._score_testability(content, notes)
            conformity = self._score_conformity(content, notes)
            
            # Score ZippyTrust metrics
            security_score = self._score_security(content, notes)
            code_quality = self._score_code_quality(content, notes)
            documentation_quality = self._score_documentation_quality(content, notes)
            community_trust = self._score_community_trust(content, notes)
            
            # Calculate weighted total
            scores = {
                'clarity': clarity,
                'structure': structure,
                'testability': testability,
                'conformity': conformity,
                'security_score': security_score,
                'code_quality': code_quality,
                'documentation_quality': documentation_quality,
                'community_trust': community_trust
            }
            
            total = sum(scores[key] * self.weights[key] for key in scores)
            
            # Determine trust level
            trust_level = self._determine_trust_level(total)
            
            return EnhancedRubricScore(
                clarity=clarity,
                structure=structure,
                testability=testability,
                conformity=conformity,
                security_score=security_score,
                code_quality=code_quality,
                documentation_quality=documentation_quality,
                community_trust=community_trust,
                total=round(total, 3),
                trust_level=trust_level,
                notes=notes,
                scored_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to score content: {e}")
            return EnhancedRubricScore(
                clarity=0.0,
                structure=0.0,
                testability=0.0,
                conformity=0.0,
                security_score=0.0,
                code_quality=0.0,
                documentation_quality=0.0,
                community_trust=0.0,
                total=0.0,
                trust_level='low',
                notes=[f'Scoring failed: {str(e)}'],
                scored_at=datetime.now().isoformat()
            )
    
    async def generate_trust_insights(self, score: EnhancedRubricScore) -> List[str]:
        """
        Generate trust insights for marketplace integration.
        
        Args:
            score: EnhancedRubricScore object
            
        Returns:
            List of trust insights
        """
        insights = []
        
        # Overall trust assessment
        if score.total >= 0.8:
            insights.append("High trust score - suitable for marketplace publication")
        elif score.total >= 0.6:
            insights.append("Medium trust score - review recommended before publication")
        else:
            insights.append("Low trust score - improvement needed before publication")
        
        # Specific metric insights
        if score.clarity < 0.6:
            insights.append("Clarity needs improvement - consider simplifying language")
        
        if score.testability < 0.6:
            insights.append("Testability concerns - add more specific acceptance criteria")
        
        if score.security_score < 0.7:
            insights.append("Security review recommended - potential vulnerabilities detected")
        
        if score.documentation_quality < 0.6:
            insights.append("Documentation quality low - add more detailed explanations")
        
        # Positive insights
        if score.conformity >= 0.8:
            insights.append("Excellent EARS compliance - well-structured requirements")
        
        if score.structure >= 0.8:
            insights.append("Strong structural organization - easy to follow")
        
        if score.code_quality >= 0.8:
            insights.append("High code quality - maintainable and well-written")
        
        return insights
    
    def _score_clarity(self, content: str, notes: List[str]) -> float:
        """Score content clarity."""
        score = 1.0
        
        # Check for vague terms
        vague_patterns = [
            r'\b(etc\.|and so on|TBD|to be decided|maybe|possibly)\b',
            r'\b(user|system|data)\b.*\b(etc\.|and so on)\b'
        ]
        
        for pattern in vague_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 0.2
                notes.append('Vague terms detected')
        
        # Check for long lines
        lines = content.split('\n')
        long_lines = [l for l in lines if len(l.strip()) > 120]
        if long_lines:
            score -= 0.1
            notes.append(f'{len(long_lines)} overly long lines')
        
        # Check for jargon
        jargon_patterns = [
            r'\b(paradigm|synergy|leverage|disrupt|innovate)\b',
            r'\b(utilize|facilitate|implement|deploy)\b'
        ]
        
        jargon_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                          for pattern in jargon_patterns)
        if jargon_count > 3:
            score -= 0.1
            notes.append('Excessive jargon detected')
        
        return max(0, min(1, score))
    
    def _score_structure(self, content: str, notes: List[str]) -> float:
        """Score content structure."""
        score = 0.0
        
        # Check for headers
        if re.search(r'^#\s+', content, re.MULTILINE):
            score += 0.3
        if re.search(r'^##\s+', content, re.MULTILINE):
            score += 0.2
        
        # Check for lists
        if re.search(r'^\s*[-*+]\s+', content, re.MULTILINE):
            score += 0.2
        if re.search(r'^\s*\d+\.\s+', content, re.MULTILINE):
            score += 0.2
        
        # Check for sections
        if re.search(r'^\s*[A-Z][A-Z\s]+:\s*$', content, re.MULTILINE):
            score += 0.1
        
        return min(1, score)
    
    def _score_testability(self, content: str, notes: List[str]) -> float:
        """Score content testability."""
        score = 0.0
        
        # Check for WHEN/THEN patterns
        if re.search(r'\bWHEN\b.*\bTHEN\b', content, re.IGNORECASE):
            score += 0.4
        elif re.search(r'\bWHEN\b', content, re.IGNORECASE):
            score += 0.2
        
        # Check for acceptance criteria
        if re.search(r'\bAcceptance:\b', content, re.IGNORECASE):
            score += 0.2
        if re.search(r'\bOutcome:\b', content, re.IGNORECASE):
            score += 0.2
        
        # Check for specific conditions
        if re.search(r'\bif\b.*\bthen\b', content, re.IGNORECASE):
            score += 0.1
        
        # Check for measurable criteria
        measurable_patterns = [
            r'\d+\s*(seconds?|minutes?|hours?|days?)',
            r'\d+\s*(users?|requests?|items?)',
            r'\d+%',
            r'\d+\s*(MB|GB|KB)'
        ]
        
        if any(re.search(pattern, content, re.IGNORECASE) for pattern in measurable_patterns):
            score += 0.1
        
        return min(1, score)
    
    def _score_conformity(self, content: str, notes: List[str]) -> float:
        """Score EARS conformity."""
        score = 0.0
        
        # Check for EARS patterns
        if re.search(r'\bWHEN\b.*\bTHE SYSTEM SHALL\b', content, re.IGNORECASE):
            score += 0.6
        elif re.search(r'\bWHEN\b', content, re.IGNORECASE):
            score += 0.3
        
        # Check for proper requirement structure
        if re.search(r'\bSHALL\b', content, re.IGNORECASE):
            score += 0.2
        
        # Check for actor specification
        if re.search(r'\bTHE SYSTEM\b', content, re.IGNORECASE):
            score += 0.2
        
        if score == 0:
            notes.append('Missing EARS markers (WHEN/THE SYSTEM SHALL)')
        
        return min(1, score)
    
    def _score_security(self, content: str, notes: List[str]) -> float:
        """Score security considerations."""
        score = 0.5  # Base score
        
        # Check for security keywords
        security_keywords = [
            'authentication', 'authorization', 'encryption', 'validation',
            'sanitize', 'secure', 'permission', 'access control'
        ]
        
        security_count = sum(len(re.findall(keyword, content, re.IGNORECASE)) 
                           for keyword in security_keywords)
        
        if security_count > 0:
            score += min(0.3, security_count * 0.1)
        
        # Check for potential security issues
        security_issues = [
            r'\bpassword\b.*\bplain\s*text',
            r'\bSQL\b.*\binjection',
            r'\bXSS\b',
            r'\bCSRF\b'
        ]
        
        for pattern in security_issues:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 0.2
                notes.append('Potential security issue detected')
        
        return max(0, min(1, score))
    
    def _score_code_quality(self, content: str, notes: List[str]) -> float:
        """Score code quality (for code snippets)."""
        score = 0.5  # Base score
        
        # Check for code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        
        if code_blocks:
            for code in code_blocks:
                # Check for comments
                if re.search(r'#.*|//.*|/\*.*?\*/', code):
                    score += 0.1
                
                # Check for meaningful variable names
                if re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', code):
                    score += 0.1
                
                # Check for proper indentation
                lines = code.split('\n')
                if all(line.startswith(' ') or not line.strip() for line in lines):
                    score += 0.1
        
        return min(1, score)
    
    def _score_documentation_quality(self, content: str, notes: List[str]) -> float:
        """Score documentation quality."""
        score = 0.0
        
        # Check for detailed explanations
        if len(content.split()) > 100:
            score += 0.3
        
        # Check for examples
        if re.search(r'\bExample:\b|\bFor example\b', content, re.IGNORECASE):
            score += 0.2
        
        # Check for step-by-step instructions
        if re.search(r'\d+\.\s+', content):
            score += 0.2
        
        # Check for cross-references
        if re.search(r'\bSee\b.*\bfor\b', content, re.IGNORECASE):
            score += 0.1
        
        # Check for definitions
        if re.search(r'\bDefinition:\b|\bmeans\b|\brefers to\b', content, re.IGNORECASE):
            score += 0.2
        
        return min(1, score)
    
    def _score_community_trust(self, content: str, notes: List[str]) -> float:
        """Score community trust (placeholder for now)."""
        # This would integrate with actual community feedback
        # For now, return a base score
        return 0.5
    
    def _determine_trust_level(self, total_score: float) -> str:
        """Determine trust level based on total score."""
        if total_score >= 0.8:
            return 'high'
        elif total_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def get_scoring_weights(self) -> Dict[str, float]:
        """Get current scoring weights."""
        return self.weights.copy()
    
    def update_scoring_weights(self, new_weights: Dict[str, float]):
        """Update scoring weights."""
        # Validate weights
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        self.weights = new_weights.copy()
        logger.info(f"Updated scoring weights: {new_weights}")
    
    def generate_score_report(self, score: EnhancedRubricScore) -> Dict[str, Any]:
        """Generate detailed score report."""
        return {
            'overview': {
                'total_score': score.total,
                'trust_level': score.trust_level,
                'scored_at': score.scored_at
            },
            'metrics': {
                'voidspec_metrics': {
                    'clarity': score.clarity,
                    'structure': score.structure,
                    'testability': score.testability,
                    'conformity': score.conformity
                },
                'zippytrust_metrics': {
                    'security_score': score.security_score,
                    'code_quality': score.code_quality,
                    'documentation_quality': score.documentation_quality,
                    'community_trust': score.community_trust
                }
            },
            'weights': self.weights,
            'notes': score.notes,
            'recommendations': self._generate_recommendations(score)
        }
    
    def _generate_recommendations(self, score: EnhancedRubricScore) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if score.clarity < 0.7:
            recommendations.append("Improve clarity by using specific, measurable terms")
        
        if score.testability < 0.7:
            recommendations.append("Add more specific acceptance criteria and test conditions")
        
        if score.conformity < 0.7:
            recommendations.append("Use EARS notation: WHEN [condition] THE SYSTEM SHALL [action]")
        
        if score.security_score < 0.7:
            recommendations.append("Include security considerations and validation requirements")
        
        if score.documentation_quality < 0.7:
            recommendations.append("Add more detailed explanations and examples")
        
        return recommendations
