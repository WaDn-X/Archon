"""
Requirements Manager for Spec-Driven Development

This module implements EARS (Easy Approach to Requirements Syntax) requirements
management with ZippyTrust validation and traceability.
"""

import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import logging

from ..plugins.trust_manager import ZippyTrustManager, TrustScore

logger = logging.getLogger(__name__)

@dataclass
class Requirement:
    """EARS-compliant requirement specification."""
    id: str
    title: str
    description: str
    type: str  # 'shall', 'should', 'may', 'will', 'can'
    actor: str
    condition: Optional[str]
    action: str
    object: str
    constraint: Optional[str]
    priority: str  # 'high', 'medium', 'low'
    created_at: str
    updated_at: str
    author: str
    wallet_address: str
    trust_score: Optional[float] = None
    validation_status: str = 'pending'

@dataclass
class TraceabilityLink:
    """Link between requirements and other artifacts."""
    source_id: str
    target_id: str
    relationship: str  # 'implements', 'depends_on', 'conflicts_with'
    created_at: str

class RequirementsManager:
    """
    Manages EARS (Easy Approach to Requirements Syntax) requirements
    with ZippyTrust validation and traceability.
    """
    
    def __init__(self):
        self.trust_manager = ZippyTrustManager()
        self.requirements_db: Dict[str, Requirement] = {}
        self.traceability_links: List[TraceabilityLink] = []
        
    async def create_requirement(self, user_input: str, wallet_address: str, 
                               author: str = "unknown") -> Dict[str, Any]:
        """
        Create structured requirements from natural language input.
        
        Args:
            user_input: Natural language description of requirements
            wallet_address: ZippyCoin wallet address
            author: Author of the requirement
            
        Returns:
            Dictionary containing the created requirement and metadata
        """
        try:
            # Parse natural language input into EARS format
            parsed_requirements = self._parse_natural_language(user_input)
            
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
                    author=author,
                    wallet_address=wallet_address
                )
                
                # Store requirement
                self.requirements_db[req_id] = requirement
                
                # Validate requirement with ZippyTrust
                trust_score = await self.validate_requirement(req_id)
                requirement.trust_score = trust_score.zippy_trust_score
                requirement.validation_status = trust_score.verification_status
                
                created_requirements.append(asdict(requirement))
            
            logger.info(f"Created {len(created_requirements)} requirements for wallet {wallet_address}")
            
            return {
                'success': True,
                'requirements': created_requirements,
                'total_count': len(created_requirements),
                'wallet_address': wallet_address,
                'author': author
            }
            
        except Exception as e:
            logger.error(f"Failed to create requirements: {e}")
            return {
                'success': False,
                'error': str(e),
                'requirements': []
            }
    
    async def validate_requirement(self, requirement_id: str) -> TrustScore:
        """
        Validate requirements using ZippyTrust criteria.
        
        Args:
            requirement_id: ID of the requirement to validate
            
        Returns:
            TrustScore object with validation results
        """
        try:
            if requirement_id not in self.requirements_db:
                raise ValueError(f"Requirement {requirement_id} not found")
            
            requirement = self.requirements_db[requirement_id]
            
            # Convert requirement to text for analysis
            req_text = self._requirement_to_text(requirement)
            
            # Create metadata for trust validation
            metadata = {
                'name': requirement.title,
                'description': requirement.description,
                'author': requirement.author,
                'version': '1.0.0',
                'dependencies': [],
                'tags': ['requirement', 'ears', requirement.type],
                'license': 'MIT'
            }
            
            # Validate with ZippyTrust
            trust_score = await self.trust_manager.verify_plugin(req_text, metadata)
            
            # Update requirement with validation results
            requirement.trust_score = trust_score.zippy_trust_score
            requirement.validation_status = trust_score.verification_status
            requirement.updated_at = datetime.now().isoformat()
            
            logger.info(f"Validated requirement {requirement_id} with trust score {trust_score.zippy_trust_score}")
            
            return trust_score
            
        except Exception as e:
            logger.error(f"Failed to validate requirement {requirement_id}: {e}")
            # Return a low trust score for failed validation
            return TrustScore(
                plugin_id=requirement_id,
                zippy_trust_score=0.1,
                verification_status='failed',
                code_quality_score=0.1,
                security_checks={},
                audit_trail=[f"Validation failed: {str(e)}"],
                last_updated=datetime.now().isoformat()
            )
    
    async def generate_traceability_matrix(self, project_id: str) -> Dict[str, Any]:
        """
        Generate REQ↔DESIGN↔TASK↔CODE traceability matrix.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dictionary containing traceability matrix
        """
        try:
            # Get all requirements for the project
            project_requirements = [
                req for req in self.requirements_db.values()
                if req.id.startswith(project_id)
            ]
            
            # Build traceability matrix
            matrix = {
                'project_id': project_id,
                'generated_at': datetime.now().isoformat(),
                'requirements': [],
                'traceability_links': [],
                'coverage_metrics': {}
            }
            
            for req in project_requirements:
                req_data = asdict(req)
                
                # Find related artifacts
                related_links = [
                    link for link in self.traceability_links
                    if link.source_id == req.id or link.target_id == req.id
                ]
                
                req_data['related_artifacts'] = [
                    {
                        'artifact_id': link.target_id if link.source_id == req.id else link.source_id,
                        'relationship': link.relationship,
                        'created_at': link.created_at
                    }
                    for link in related_links
                ]
                
                matrix['requirements'].append(req_data)
                matrix['traceability_links'].extend([asdict(link) for link in related_links])
            
            # Calculate coverage metrics
            total_requirements = len(project_requirements)
            validated_requirements = len([req for req in project_requirements if req.validation_status == 'verified'])
            linked_requirements = len([req for req in project_requirements if req_data['related_artifacts']])
            
            matrix['coverage_metrics'] = {
                'total_requirements': total_requirements,
                'validated_requirements': validated_requirements,
                'linked_requirements': linked_requirements,
                'validation_coverage': validated_requirements / total_requirements if total_requirements > 0 else 0,
                'linkage_coverage': linked_requirements / total_requirements if total_requirements > 0 else 0,
                'average_trust_score': sum(req.trust_score or 0 for req in project_requirements) / total_requirements if total_requirements > 0 else 0
            }
            
            logger.info(f"Generated traceability matrix for project {project_id}")
            
            return matrix
            
        except Exception as e:
            logger.error(f"Failed to generate traceability matrix for project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'project_id': project_id
            }
    
    def add_traceability_link(self, source_id: str, target_id: str, 
                            relationship: str) -> bool:
        """
        Add a traceability link between artifacts.
        
        Args:
            source_id: Source artifact ID
            target_id: Target artifact ID
            relationship: Type of relationship
            
        Returns:
            True if link was added successfully
        """
        try:
            link = TraceabilityLink(
                source_id=source_id,
                target_id=target_id,
                relationship=relationship,
                created_at=datetime.now().isoformat()
            )
            
            self.traceability_links.append(link)
            logger.info(f"Added traceability link: {source_id} {relationship} {target_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add traceability link: {e}")
            return False
    
    def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """Get a requirement by ID."""
        return self.requirements_db.get(requirement_id)
    
    def list_requirements(self, wallet_address: Optional[str] = None, 
                         author: Optional[str] = None) -> List[Requirement]:
        """List requirements with optional filtering."""
        requirements = list(self.requirements_db.values())
        
        if wallet_address:
            requirements = [req for req in requirements if req.wallet_address == wallet_address]
        
        if author:
            requirements = [req for req in requirements if req.author == author]
        
        return requirements
    
    def _parse_natural_language(self, user_input: str) -> List[Dict[str, Any]]:
        """
        Parse natural language input into EARS format.
        
        This is a simplified parser - in a real implementation, you'd use
        more sophisticated NLP techniques.
        """
        requirements = []
        
        # Split input into sentences
        sentences = re.split(r'[.!?]+', user_input)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Simple pattern matching for EARS parsing
            # In reality, you'd use more sophisticated NLP
            
            # Extract actor (who/what system)
            actor_match = re.search(r'(?:the\s+)?(\w+(?:\s+\w+)*?)\s+(?:shall|should|may|will|can)', sentence, re.IGNORECASE)
            actor = actor_match.group(1) if actor_match else 'system'
            
            # Extract requirement type
            type_match = re.search(r'(shall|should|may|will|can)', sentence, re.IGNORECASE)
            req_type = type_match.group(1).lower() if type_match else 'shall'
            
            # Extract action and object
            action_object_match = re.search(r'(?:shall|should|may|will|can)\s+(.+?)(?:\s+when|\s+if|\s+unless|$)', sentence, re.IGNORECASE)
            action_object = action_object_match.group(1).strip() if action_object_match else sentence
            
            # Extract condition (if any)
            condition_match = re.search(r'(?:when|if)\s+(.+?)(?:\s+unless|$)', sentence, re.IGNORECASE)
            condition = condition_match.group(1).strip() if condition_match else None
            
            # Extract constraint (if any)
            constraint_match = re.search(r'unless\s+(.+)', sentence, re.IGNORECASE)
            constraint = constraint_match.group(1).strip() if constraint_match else None
            
            # Determine priority based on requirement type
            priority_map = {
                'shall': 'high',
                'should': 'medium',
                'may': 'low',
                'will': 'high',
                'can': 'medium'
            }
            priority = priority_map.get(req_type, 'medium')
            
            requirement_data = {
                'title': f"Requirement {len(requirements) + 1}",
                'description': sentence,
                'type': req_type,
                'actor': actor,
                'condition': condition,
                'action': action_object,
                'object': action_object,
                'constraint': constraint,
                'priority': priority
            }
            
            requirements.append(requirement_data)
        
        return requirements
    
    def _requirement_to_text(self, requirement: Requirement) -> str:
        """Convert requirement to text for trust validation."""
        text_parts = []
        
        if requirement.title:
            text_parts.append(f"Title: {requirement.title}")
        
        if requirement.description:
            text_parts.append(f"Description: {requirement.description}")
        
        text_parts.append(f"Type: {requirement.type}")
        text_parts.append(f"Actor: {requirement.actor}")
        
        if requirement.condition:
            text_parts.append(f"Condition: {requirement.condition}")
        
        text_parts.append(f"Action: {requirement.action}")
        text_parts.append(f"Object: {requirement.object}")
        
        if requirement.constraint:
            text_parts.append(f"Constraint: {requirement.constraint}")
        
        text_parts.append(f"Priority: {requirement.priority}")
        text_parts.append(f"Author: {requirement.author}")
        
        return "\n".join(text_parts)
    
    def export_requirements(self, format: str = 'json') -> str:
        """Export requirements in specified format."""
        if format == 'json':
            return json.dumps([asdict(req) for req in self.requirements_db.values()], indent=2)
        elif format == 'ears':
            return self._export_ears_format()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_ears_format(self) -> str:
        """Export requirements in EARS format."""
        ears_lines = []
        
        for req in self.requirements_db.values():
            ears_line = f"{req.actor} {req.type} {req.action}"
            
            if req.condition:
                ears_line += f" when {req.condition}"
            
            if req.constraint:
                ears_line += f" unless {req.constraint}"
            
            ears_lines.append(ears_line)
        
        return "\n".join(ears_lines)
