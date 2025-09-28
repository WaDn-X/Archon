#!/usr/bin/env python3
"""
Simple VoidSpec Integration Demo

This script demonstrates the key concepts of VoidSpec integration
with Zippy-Archon without requiring complex imports.
"""

import re
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any

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
    trust_score: float = 0.0

class SimpleVoidSpecDemo:
    """
    Simplified demo of VoidSpec integration concepts.
    """
    
    def __init__(self):
        self.ab_results = []
    
    def score_requirements(self, content: str) -> RubricScore:
        """
        Score requirements using VoidSpec's rubric system.
        
        Args:
            content: Requirements content to score
            
        Returns:
            RubricScore object with detailed scoring
        """
        lines = content.split('\n')
        text = content
        notes = []
        
        # Clarity: penalize vague terms and long lines
        vague_patterns = [r'\b(etc\.|and so on|TBD|to be decided)\b']
        long_lines = [l for l in lines if len(l.strip()) > 120]
        
        clarity = 1.0
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in vague_patterns):
            clarity -= 0.3
            notes.append('Vague terms present')
        if long_lines:
            clarity -= 0.2
            notes.append(f'{len(long_lines)} overly long lines')
        clarity = max(0, min(1, clarity))
        
        # Structure: presence of headers/sections
        structure = 0.0
        if re.search(r'^#\s+Requirements', text, re.MULTILINE):
            structure += 0.4
        if re.search(r'^##\s+', text, re.MULTILINE) or re.search(r'-\s+', text):
            structure += 0.3
        if re.search(r'\d+\.', text):
            structure += 0.3
        structure = min(1, structure)
        
        # Testability: look for WHEN/THEN or explicit outcomes
        testability = 0.0
        testability_patterns = [
            r'\bWHEN\b', r'\bTHE SYSTEM SHALL\b', r'\bTHEN\b',
            r'\bOutcome:\b', r'\bAcceptance:\b'
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in testability_patterns):
            testability += 0.7
        if re.search(r'\bDependencies?:\b', text, re.IGNORECASE):
            testability += 0.3
        testability = min(1, testability)
        
        # Conformity: EARS compliance
        conformity = 0.0
        if re.search(r'\bWHEN\b.*\bTHE SYSTEM SHALL\b', text, re.IGNORECASE):
            conformity = 1.0
        else:
            notes.append('Missing EARS markers (WHEN/THE SYSTEM SHALL)')
        
        total = round((clarity + structure + testability + conformity) / 4, 3)
        
        return RubricScore(
            clarity=clarity,
            structure=structure,
            testability=testability,
            conformity=conformity,
            total=total,
            notes=notes
        )
    
    def generate_requirements(self, prompt: str, version: str = 'v1') -> Dict[str, Any]:
        """
        Generate requirements using VoidSpec's approach.
        
        Args:
            prompt: User's feature description
            version: Prompt version (v1, v1b, enhanced)
            
        Returns:
            Dictionary containing generated requirements
        """
        # Generate EARS-compliant requirements
        requirements = [
            f"# Requirements",
            "",
            f"## Feature: {prompt}",
            "",
            "WHEN a user performs the primary action",
            "THE SYSTEM SHALL provide the expected response",
            "",
            "WHEN the system encounters an error condition",
            "THE SYSTEM SHALL display a meaningful error message",
            "",
            "### Additional Requirements:",
            "- Use clear, testable language",
            "- Include error handling scenarios",
            "- Define system boundaries"
        ]
        
        content = "\n".join(requirements)
        
        # Score the content
        rubric_score = self.score_requirements(content)
        
        return {
            'success': True,
            'content': content,
            'version': version,
            'rubric_score': asdict(rubric_score),
            'generated_at': datetime.now().isoformat()
        }
    
    def run_ab_test(self, prompt: str, versions: List[str] = None) -> Dict[str, Any]:
        """
        Run A/B test between different prompt versions.
        
        Args:
            prompt: Feature description to test
            versions: List of versions to test (default: ['v1', 'v1b'])
            
        Returns:
            Dictionary containing A/B test results
        """
        if versions is None:
            versions = ['v1', 'v1b']
        
        test_results = []
        
        for version in versions:
            # Generate requirements for this version
            result = self.generate_requirements(prompt, version)
            
            if result['success']:
                test_results.append({
                    'version': version,
                    'score': result['rubric_score'],
                    'content_preview': result['content'][:100] + "..."
                })
        
        # Determine winner based on total rubric score
        winner = max(test_results, key=lambda x: x['score']['total'])
        
        # Create A/B test result
        ab_result = ABTestResult(
            feature=prompt,
            versions=test_results,
            winner=winner['version'],
            created_at=datetime.now().isoformat()
        )
        
        # Store the result
        self.ab_results.append(ab_result)
        
        return {
            'success': True,
            'feature': prompt,
            'versions': test_results,
            'winner': winner['version'],
            'winner_score': winner['score']['total'],
            'created_at': ab_result.created_at
        }
    
    def export_ab_results(self, format: str = 'json') -> str:
        """Export A/B test results in specified format."""
        if format == 'json':
            return json.dumps([asdict(result) for result in self.ab_results], indent=2)
        elif format == 'csv':
            # Convert to CSV format
            csv_lines = ['feature,winner,created_at,trust_score']
            for result in self.ab_results:
                csv_lines.append(f"{result.feature},{result.winner},{result.created_at},{result.trust_score}")
            return '\n'.join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

def main():
    """Main demo function."""
    print("🚀 VoidSpec Integration Demo with Zippy-Archon")
    print("=" * 60)
    
    demo = SimpleVoidSpecDemo()
    
    # Test 1: Generate requirements
    print("\n📝 Test 1: Generate Requirements")
    print("-" * 40)
    
    prompt = "Create a user authentication system with login and registration"
    result = demo.generate_requirements(prompt, 'v1')
    
    if result['success']:
        print(f"✅ Generated requirements using {result['version']}")
        print(f"📊 Rubric Score: {result['rubric_score']['total']:.3f}")
        print(f"   - Clarity: {result['rubric_score']['clarity']:.3f}")
        print(f"   - Structure: {result['rubric_score']['structure']:.3f}")
        print(f"   - Testability: {result['rubric_score']['testability']:.3f}")
        print(f"   - Conformity: {result['rubric_score']['conformity']:.3f}")
        
        print(f"\n📄 Content Preview:")
        content_lines = result['content'].split('\n')[:8]
        for line in content_lines:
            print(f"   {line}")
    
    # Test 2: Run A/B test
    print("\n🔬 Test 2: Run A/B Test")
    print("-" * 40)
    
    ab_result = demo.run_ab_test("Implement a shopping cart feature")
    
    if ab_result['success']:
        print(f"✅ A/B test completed successfully")
        print(f"🏆 Winner: {ab_result['winner']}")
        print(f"📊 Winner Score: {ab_result['winner_score']:.3f}")
        
        print(f"\n📈 Version Comparison:")
        for version in ab_result['versions']:
            score = version['score']
            print(f"   {version['version']}: {score['total']:.3f} "
                  f"(C:{score['clarity']:.2f} S:{score['structure']:.2f} "
                  f"T:{score['testability']:.2f} F:{score['conformity']:.2f})")
    
    # Test 3: Score sample content
    print("\n📊 Test 3: Score Sample Content")
    print("-" * 40)
    
    sample_content = """
# Requirements

## Feature: User Authentication

WHEN a user enters valid credentials
THE SYSTEM SHALL authenticate the user and grant access

WHEN a user enters invalid credentials
THE SYSTEM SHALL display an error message and deny access

### Additional Requirements:
- Use secure password hashing
- Implement session management
- Include password reset functionality
"""
    
    rubric_score = demo.score_requirements(sample_content)
    
    print(f"📋 Sample Content Scoring:")
    print(f"   Total Score: {rubric_score.total:.3f}")
    print(f"   Clarity: {rubric_score.clarity:.3f}")
    print(f"   Structure: {rubric_score.structure:.3f}")
    print(f"   Testability: {rubric_score.testability:.3f}")
    print(f"   Conformity: {rubric_score.conformity:.3f}")
    
    if rubric_score.notes:
        print(f"   Notes: {', '.join(rubric_score.notes)}")
    
    # Test 4: Export results
    print("\n📤 Test 4: Export Results")
    print("-" * 40)
    
    # Export as JSON
    json_export = demo.export_ab_results('json')
    print(f"📄 JSON Export (first 200 chars): {json_export[:200]}...")
    
    # Export as CSV
    csv_export = demo.export_ab_results('csv')
    print(f"📊 CSV Export:")
    for line in csv_export.split('\n'):
        print(f"   {line}")
    
    print("\n🎉 VoidSpec Integration Demo Complete!")
    print("=" * 60)
    print("\n💡 Key Features Demonstrated:")
    print("   ✅ EARS-compliant requirements generation")
    print("   ✅ Rubric-based scoring (clarity, structure, testability, conformity)")
    print("   ✅ A/B testing between prompt versions")
    print("   ✅ JSON and CSV export capabilities")
    print("   ✅ Integration with ZippyTrust concepts")
    print("\n🚀 Next Steps:")
    print("   📝 Implement AI provider integration (Grok, OpenAI)")
    print("   🔗 Connect with ZippyCoin marketplace")
    print("   🎯 Add VS Code extension panels")
    print("   📊 Implement milestone management")

if __name__ == "__main__":
    main()
