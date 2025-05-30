
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIDecisionStatus(Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    OVERRIDE = "override"
    ESCALATED = "escalated"

class AIReviewLevel(Enum):
    AUTOMATIC = "automatic"  # Low confidence, auto-approve
    STAFF_REVIEW = "staff_review"  # Medium confidence, requires staff review
    SUPERVISOR_REVIEW = "supervisor_review"  # High impact, requires supervisor
    DIRECTOR_APPROVAL = "director_approval"  # Critical decisions, director approval

class AIDecisionRecord:
    """Records AI decisions and human oversight"""
    
    def __init__(self, decision_data: Dict[str, Any]):
        self.id = decision_data.get("id", f"ai_decision_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
        self.ai_system = decision_data.get("ai_system", "unknown")
        self.decision_type = decision_data.get("decision_type", "unknown")
        self.confidence_score = decision_data.get("confidence_score", 0.0)
        self.ai_recommendation = decision_data.get("ai_recommendation", {})
        self.supporting_evidence = decision_data.get("supporting_evidence", [])
        self.property_id = decision_data.get("property_id")
        self.created_at = datetime.now()
        self.status = AIDecisionStatus.PENDING_REVIEW
        self.review_level = self._determine_review_level()
        self.human_reviews = []
        self.final_decision = None
        self.audit_trail = []

    def _determine_review_level(self) -> AIReviewLevel:
        """Determine required review level based on decision type and confidence"""
        
        # Critical decisions always require director approval
        critical_decisions = ["fraud_detection", "major_exemption_change", "value_adjustment_over_threshold"]
        if self.decision_type in critical_decisions:
            return AIReviewLevel.DIRECTOR_APPROVAL
        
        # High impact decisions require supervisor review
        high_impact = ["exemption_qualification", "property_reclassification"]
        if self.decision_type in high_impact:
            return AIReviewLevel.SUPERVISOR_REVIEW
        
        # Low confidence always requires human review
        if self.confidence_score < 0.7:
            return AIReviewLevel.STAFF_REVIEW
        
        # High confidence routine decisions can be automatic
        if self.confidence_score >= 0.95 and self.decision_type in ["routine_exemption", "data_validation"]:
            return AIReviewLevel.AUTOMATIC
        
        # Default to staff review
        return AIReviewLevel.STAFF_REVIEW

class HumanReview:
    """Human review of AI decision"""
    
    def __init__(self, reviewer_data: Dict[str, Any]):
        self.reviewer_id = reviewer_data["reviewer_id"]
        self.reviewer_name = reviewer_data["reviewer_name"]
        self.reviewer_role = reviewer_data["reviewer_role"]
        self.review_timestamp = datetime.now()
        self.decision = reviewer_data["decision"]  # approve, reject, override, escalate
        self.comments = reviewer_data.get("comments", "")
        self.override_reason = reviewer_data.get("override_reason")
        self.new_recommendation = reviewer_data.get("new_recommendation")

class AIDecisionOversightSystem:
    """
    Comprehensive AI oversight system ensuring human-in-the-loop for critical decisions.
    Provides clear approval workflows, override mechanisms, and audit trails.
    """
    
    def __init__(self):
        self.storage_path = Path("data/ai_decisions")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load authorized reviewers
        self.authorized_reviewers = self._load_authorized_reviewers()
        
        # Decision thresholds and rules
        self.decision_rules = {
            "exemption_qualification": {
                "auto_approve_threshold": 0.95,
                "requires_supervisor": ["senior_exemption", "agricultural", "disability"],
                "financial_threshold": 50000  # Dollar amount requiring director approval
            },
            "fraud_detection": {
                "auto_approve_threshold": 0.0,  # Never auto-approve fraud detection
                "immediate_escalation": True,
                "notification_required": ["assessor", "director", "legal"]
            },
            "property_valuation": {
                "auto_approve_threshold": 0.9,
                "variance_threshold": 0.15,  # 15% variance requires review
                "high_value_threshold": 1000000  # $1M+ requires supervisor
            }
        }
    
    def _load_authorized_reviewers(self) -> Dict[str, Dict]:
        """Load authorized reviewers and their roles"""
        reviewers_file = Path("county_users.json")
        if reviewers_file.exists():
            try:
                with open(reviewers_file, 'r') as f:
                    users = json.load(f)
                    
                # Filter users with review permissions
                return {
                    user["id"]: {
                        "name": user["name"],
                        "role": user["role"],
                        "permissions": user.get("permissions", []),
                        "can_approve": "ai_review" in user.get("permissions", []),
                        "can_override": "ai_override" in user.get("permissions", []),
                        "approval_level": user.get("approval_level", "staff")
                    }
                    for user in users if "ai_review" in user.get("permissions", [])
                }
            except Exception as e:
                logger.error(f"Failed to load authorized reviewers: {e}")
        
        # Default fallback
        return {
            "admin": {
                "name": "System Administrator",
                "role": "admin",
                "permissions": ["ai_review", "ai_override"],
                "can_approve": True,
                "can_override": True,
                "approval_level": "director"
            }
        }
    
    def submit_ai_decision(self, decision_data: Dict[str, Any]) -> str:
        """Submit AI decision for human review"""
        
        # Create decision record
        decision = AIDecisionRecord(decision_data)
        
        # Auto-approve if meets criteria
        if self._should_auto_approve(decision):
            decision.status = AIDecisionStatus.APPROVED
            decision.final_decision = decision.ai_recommendation
            decision.audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "auto_approved",
                "reason": f"High confidence ({decision.confidence_score:.2f}) routine decision"
            })
            logger.info(f"AI decision {decision.id} auto-approved")
        else:
            # Queue for human review
            decision.audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "queued_for_review",
                "review_level": decision.review_level.value,
                "reason": self._get_review_reason(decision)
            })
            logger.info(f"AI decision {decision.id} queued for {decision.review_level.value}")
        
        # Save decision
        self._save_decision(decision)
        
        # Send notifications if required
        self._send_review_notifications(decision)
        
        return decision.id
    
    def _should_auto_approve(self, decision: AIDecisionRecord) -> bool:
        """Determine if decision should be auto-approved"""
        
        # Never auto-approve critical decisions
        if decision.review_level in [AIReviewLevel.DIRECTOR_APPROVAL, AIReviewLevel.SUPERVISOR_REVIEW]:
            return False
        
        # Check decision-specific rules
        rules = self.decision_rules.get(decision.decision_type, {})
        threshold = rules.get("auto_approve_threshold", 0.95)
        
        return decision.confidence_score >= threshold and decision.review_level == AIReviewLevel.AUTOMATIC
    
    def _get_review_reason(self, decision: AIDecisionRecord) -> str:
        """Get human-readable reason for review requirement"""
        
        if decision.confidence_score < 0.7:
            return f"Low confidence score ({decision.confidence_score:.2f})"
        
        if decision.decision_type in ["fraud_detection", "major_exemption_change"]:
            return "Critical decision type requires human oversight"
        
        rules = self.decision_rules.get(decision.decision_type, {})
        
        # Check financial thresholds
        if "financial_threshold" in rules:
            amount = decision.ai_recommendation.get("financial_impact", 0)
            if amount > rules["financial_threshold"]:
                return f"Financial impact (${amount:,.2f}) exceeds threshold"
        
        return "Requires human verification per policy"
    
    def submit_human_review(self, decision_id: str, reviewer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit human review of AI decision"""
        
        # Load decision
        decision = self._load_decision(decision_id)
        if not decision:
            return {"error": "Decision not found"}
        
        # Validate reviewer authorization
        reviewer_id = reviewer_data["reviewer_id"]
        if reviewer_id not in self.authorized_reviewers:
            return {"error": "Unauthorized reviewer"}
        
        reviewer_info = self.authorized_reviewers[reviewer_id]
        
        # Check approval level authorization
        required_level = decision.review_level
        reviewer_level = reviewer_info["approval_level"]
        
        if not self._check_approval_authority(required_level, reviewer_level):
            return {"error": f"Insufficient approval authority. Requires {required_level.value}, reviewer has {reviewer_level}"}
        
        # Create human review
        review = HumanReview(reviewer_data)
        decision.human_reviews.append(review)
        
        # Process review decision
        if review.decision == "approve":
            decision.status = AIDecisionStatus.APPROVED
            decision.final_decision = decision.ai_recommendation
            
        elif review.decision == "reject":
            decision.status = AIDecisionStatus.REJECTED
            decision.final_decision = None
            
        elif review.decision == "override":
            decision.status = AIDecisionStatus.OVERRIDE
            decision.final_decision = review.new_recommendation
            
        elif review.decision == "escalate":
            decision.status = AIDecisionStatus.ESCALATED
            decision.review_level = AIReviewLevel.DIRECTOR_APPROVAL
        
        # Update audit trail
        decision.audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "action": f"human_review_{review.decision}",
            "reviewer": review.reviewer_name,
            "reviewer_role": review.reviewer_role,
            "comments": review.comments
        })
        
        # Save updated decision
        self._save_decision(decision)
        
        logger.info(f"Human review submitted for decision {decision_id} by {review.reviewer_name}: {review.decision}")
        
        return {
            "success": True,
            "decision_id": decision_id,
            "status": decision.status.value,
            "final_decision": decision.final_decision
        }
    
    def _check_approval_authority(self, required_level: AIReviewLevel, reviewer_level: str) -> bool:
        """Check if reviewer has sufficient authority"""
        
        authority_hierarchy = {
            "staff": [AIReviewLevel.STAFF_REVIEW, AIReviewLevel.AUTOMATIC],
            "supervisor": [AIReviewLevel.STAFF_REVIEW, AIReviewLevel.SUPERVISOR_REVIEW, AIReviewLevel.AUTOMATIC],
            "director": [AIReviewLevel.STAFF_REVIEW, AIReviewLevel.SUPERVISOR_REVIEW, AIReviewLevel.DIRECTOR_APPROVAL, AIReviewLevel.AUTOMATIC]
        }
        
        return required_level in authority_hierarchy.get(reviewer_level, [])
    
    def get_pending_reviews(self, reviewer_id: str) -> List[Dict]:
        """Get pending reviews for a specific reviewer"""
        
        if reviewer_id not in self.authorized_reviewers:
            return []
        
        reviewer_info = self.authorized_reviewers[reviewer_id]
        reviewer_level = reviewer_info["approval_level"]
        
        pending_decisions = []
        
        # Scan all decision files
        for decision_file in self.storage_path.glob("*.json"):
            try:
                decision = self._load_decision(decision_file.stem)
                if decision and decision.status == AIDecisionStatus.PENDING_REVIEW:
                    # Check if reviewer can handle this decision
                    if self._check_approval_authority(decision.review_level, reviewer_level):
                        pending_decisions.append({
                            "id": decision.id,
                            "decision_type": decision.decision_type,
                            "ai_system": decision.ai_system,
                            "confidence_score": decision.confidence_score,
                            "created_at": decision.created_at.isoformat(),
                            "review_level": decision.review_level.value,
                            "property_id": decision.property_id,
                            "ai_recommendation": decision.ai_recommendation
                        })
            except Exception as e:
                logger.error(f"Error loading decision {decision_file}: {e}")
        
        # Sort by creation date (oldest first)
        pending_decisions.sort(key=lambda x: x["created_at"])
        
        return pending_decisions
    
    def get_decision_audit_trail(self, decision_id: str) -> Optional[Dict]:
        """Get complete audit trail for a decision"""
        
        decision = self._load_decision(decision_id)
        if not decision:
            return None
        
        return {
            "decision_id": decision.id,
            "ai_system": decision.ai_system,
            "decision_type": decision.decision_type,
            "property_id": decision.property_id,
            "created_at": decision.created_at.isoformat(),
            "status": decision.status.value,
            "review_level": decision.review_level.value,
            "confidence_score": decision.confidence_score,
            "ai_recommendation": decision.ai_recommendation,
            "final_decision": decision.final_decision,
            "human_reviews": [
                {
                    "reviewer": review.reviewer_name,
                    "role": review.reviewer_role,
                    "timestamp": review.review_timestamp.isoformat(),
                    "decision": review.decision,
                    "comments": review.comments
                }
                for review in decision.human_reviews
            ],
            "audit_trail": decision.audit_trail
        }
    
    def _save_decision(self, decision: AIDecisionRecord):
        """Save decision to storage"""
        
        decision_file = self.storage_path / f"{decision.id}.json"
        
        # Convert to serializable format
        decision_data = {
            "id": decision.id,
            "ai_system": decision.ai_system,
            "decision_type": decision.decision_type,
            "confidence_score": decision.confidence_score,
            "ai_recommendation": decision.ai_recommendation,
            "supporting_evidence": decision.supporting_evidence,
            "property_id": decision.property_id,
            "created_at": decision.created_at.isoformat(),
            "status": decision.status.value,
            "review_level": decision.review_level.value,
            "final_decision": decision.final_decision,
            "human_reviews": [
                {
                    "reviewer_id": review.reviewer_id,
                    "reviewer_name": review.reviewer_name,
                    "reviewer_role": review.reviewer_role,
                    "review_timestamp": review.review_timestamp.isoformat(),
                    "decision": review.decision,
                    "comments": review.comments,
                    "override_reason": review.override_reason,
                    "new_recommendation": review.new_recommendation
                }
                for review in decision.human_reviews
            ],
            "audit_trail": decision.audit_trail
        }
        
        with open(decision_file, 'w') as f:
            json.dump(decision_data, f, indent=2)
    
    def _load_decision(self, decision_id: str) -> Optional[AIDecisionRecord]:
        """Load decision from storage"""
        
        decision_file = self.storage_path / f"{decision_id}.json"
        if not decision_file.exists():
            return None
        
        try:
            with open(decision_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct decision object
            decision = AIDecisionRecord(data)
            decision.created_at = datetime.fromisoformat(data["created_at"])
            decision.status = AIDecisionStatus(data["status"])
            decision.review_level = AIReviewLevel(data["review_level"])
            decision.final_decision = data["final_decision"]
            decision.audit_trail = data["audit_trail"]
            
            # Reconstruct human reviews
            decision.human_reviews = []
            for review_data in data.get("human_reviews", []):
                review = HumanReview(review_data)
                review.review_timestamp = datetime.fromisoformat(review_data["review_timestamp"])
                decision.human_reviews.append(review)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error loading decision {decision_id}: {e}")
            return None
    
    def _send_review_notifications(self, decision: AIDecisionRecord):
        """Send notifications for decisions requiring review"""
        
        # This would integrate with your notification system
        logger.info(f"Notification: AI decision {decision.id} requires {decision.review_level.value}")
        
        # In production, send email/Slack notifications to appropriate reviewers

def main():
    """Demo of AI oversight system"""
    
    oversight = AIDecisionOversightSystem()
    
    # Example: AI exemption recommendation
    exemption_decision = {
        "ai_system": "ExemptionSeer",
        "decision_type": "exemption_qualification",
        "confidence_score": 0.85,
        "property_id": "12345",
        "ai_recommendation": {
            "exempt": True,
            "exemption_type": "senior_citizen",
            "exemption_amount": 15000,
            "reasoning": "Property owner meets age and income requirements"
        },
        "supporting_evidence": [
            "Age verified: 67 years old",
            "Income verified: $28,000 annually", 
            "Property value: $180,000"
        ]
    }
    
    # Submit for review
    decision_id = oversight.submit_ai_decision(exemption_decision)
    print(f"AI decision submitted: {decision_id}")
    
    # Check pending reviews
    pending = oversight.get_pending_reviews("admin")
    print(f"Pending reviews: {len(pending)}")
    
    # Human review
    if pending:
        review_result = oversight.submit_human_review(decision_id, {
            "reviewer_id": "admin",
            "reviewer_name": "System Administrator",
            "reviewer_role": "admin",
            "decision": "approve",
            "comments": "AI recommendation verified and approved"
        })
        print(f"Review result: {review_result}")
    
    # Get audit trail
    audit = oversight.get_decision_audit_trail(decision_id)
    print(f"Audit trail: {json.dumps(audit, indent=2)}")

if __name__ == "__main__":
    main()
