#!/usr/bin/env python3
"""
Test script for VoidSpec integration with Zippy-Archon

This script demonstrates the enhanced requirements manager that incorporates
VoidSpec's EARS approach with ZippyTrust validation and A/B testing capabilities.
"""

import asyncio
import json
from agentic_workflow.specs.voidspec_requirements_manager import VoidSpecRequirementsManager

async def test_voidspec_integration():
    """Test the VoidSpec integration features."""
    
    print("🚀 Testing VoidSpec Integration with Zippy-Archon")
    print("=" * 60)
    
    # Initialize the enhanced requirements manager
    manager = VoidSpecRequirementsManager()
    
    # Test 1: Generate requirements with AI
    print("\n📝 Test 1: Generate Requirements with AI")
    print("-" * 40)
    
    prompt = "Create a user authentication system with login and registration"
    
    result = await manager.generate_requirements(
        prompt=prompt,
        version='v1',
        use_ai=True
    )
    
    if result['success']:
        print(f"✅ Generated {result['total_count']} requirements")
        print(f"📊 Version: {result['version']}")
        print(f"🤖 AI Generated: {result['ai_generated']}")
        
        # Show the first requirement
        if result['requirements']:
            req = result['requirements'][0]
            print(f"\n📋 Sample Requirement:")
            print(f"   Title: {req['title']}")
            print(f"   Type: {req['type']}")
            print(f"   Actor: {req['actor']}")
            print(f"   Condition: {req['condition']}")
            print(f"   Action: {req['action']}")
            print(f"   Trust Score: {req['trust_score']:.2f}")
            
            if 'rubric_score' in req:
                rubric = req['rubric_score']
                print(f"   Rubric Score: {rubric['total']:.3f}")
                print(f"     - Clarity: {rubric['clarity']:.3f}")
                print(f"     - Structure: {rubric['structure']:.3f}")
                print(f"     - Testability: {rubric['testability']:.3f}")
                print(f"     - Conformity: {rubric['conformity']:.3f}")
    else:
        print(f"❌ Failed to generate requirements: {result['error']}")
    
    # Test 2: Run A/B test
    print("\n🔬 Test 2: Run A/B Test")
    print("-" * 40)
    
    ab_result = await manager.run_ab_test(
        prompt="Implement a shopping cart feature",
        versions=['v1', 'v1b']
    )
    
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
    else:
        print(f"❌ A/B test failed: {ab_result['error']}")
    
    # Test 3: Score requirements manually
    print("\n📊 Test 3: Manual Requirements Scoring")
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
    
    rubric_score = await manager.score_requirements(sample_content)
    
    print(f"📋 Sample Content Scoring:")
    print(f"   Total Score: {rubric_score.total:.3f}")
    print(f"   Clarity: {rubric_score.clarity:.3f}")
    print(f"   Structure: {rubric_score.structure:.3f}")
    print(f"   Testability: {rubric_score.testability:.3f}")
    print(f"   Conformity: {rubric_score.conformity:.3f}")
    
    if rubric_score.notes:
        print(f"   Notes: {', '.join(rubric_score.notes)}")
    
    # Test 4: Export A/B results
    print("\n📤 Test 4: Export A/B Results")
    print("-" * 40)
    
    ab_results = manager.get_ab_results()
    print(f"📊 Total A/B tests: {len(ab_results)}")
    
    if ab_results:
        # Export as JSON
        json_export = manager.export_ab_results('json')
        print(f"📄 JSON Export (first 200 chars): {json_export[:200]}...")
        
        # Export as CSV
        csv_export = manager.export_ab_results('csv')
        print(f"📊 CSV Export:")
        for line in csv_export.split('\n'):
            print(f"   {line}")
    
    # Test 5: Generate fallback requirements
    print("\n🔄 Test 5: Fallback Requirements Generation")
    print("-" * 40)
    
    fallback_result = await manager.generate_requirements(
        prompt="Build a simple calculator",
        version='fallback',
        use_ai=False
    )
    
    if fallback_result['success']:
        print(f"✅ Generated {fallback_result['total_count']} fallback requirements")
        print(f"🤖 AI Generated: {fallback_result['ai_generated']}")
        
        # Show raw content
        print(f"\n📄 Raw Content Preview:")
        content_lines = fallback_result['raw_content'].split('\n')[:10]
        for line in content_lines:
            print(f"   {line}")
    else:
        print(f"❌ Fallback generation failed: {fallback_result['error']}")
    
    print("\n🎉 VoidSpec Integration Test Complete!")
    print("=" * 60)

def main():
    """Main function to run the test."""
    try:
        asyncio.run(test_voidspec_integration())
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
