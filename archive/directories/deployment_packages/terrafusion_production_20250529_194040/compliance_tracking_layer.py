"""
TerraFusion Compliance Tracking Layer

Phase II Implementation: Compliance Tracking Layer
- Inject document traceability into ExemptionSeer results
- Auto-flag low-confidence records for assessor queue
- Link all changes to audit trail (source, timestamp, AI model version)
"""

import os
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from sqlalchemy import create_engine, text, Column, String, DateTime, Float, Integer, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class ComplianceAuditLog(Base):
    """Database model for compliance audit logs"""
    __tablename__ = 'compliance_audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(String(255), nullable=False, index=True)
    record_type = Column(String(100), nullable=False)  # exemption, property, valuation
    record_id = Column(String(255), nullable=False, index=True)
    operation_type = Column(String(100), nullable=False)  # create, update, delete, ai_analysis
    source_system = Column(String(100), nullable=False)  # pacs, terrafusion, ai_model
    ai_model_version = Column(String(100))
    confidence_score = Column(Float)
    user_id = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    data_hash = Column(String(64))  # SHA-256 hash of record data
    change_summary = Column(Text)
    compliance_flags = Column(Text)  # JSON string of compliance flags
    review_required = Column(Boolean, default=False)
    reviewed_by = Column(String(255))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)

@dataclass
class ComplianceFlag:
    """Compliance flag for audit tracking"""
    flag_type: str  # confidence, validation, regulatory, workflow
    severity: str   # low, medium, high, critical
    description: str
    rule_id: str
    auto_generated: bool
    requires_review: bool

@dataclass
class DocumentTrace:
    """Document traceability record"""
    document_id: str
    document_type: str
    source_file: str
    creation_date: datetime
    last_modified: datetime
    checksum: str
    related_records: List[str]
    compliance_status: str

class ComplianceTracker:
    """
    Compliance tracking and audit trail management.
    Ensures all changes and AI operations are properly logged and traceable.
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize compliance tracker.
        
        Args:
            database_url: Database connection string
        """
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        self.engine = create_engine(self.database_url) if self.database_url else None
        self.Session = sessionmaker(bind=self.engine) if self.engine else None
        
        # Compliance rules configuration
        self.compliance_rules = self._load_compliance_rules()
        
        # Document tracking
        self.document_traces: List[DocumentTrace] = []
        
        # Compliance thresholds
        self.confidence_thresholds = {
            "exemption_analysis": 0.85,
            "property_valuation": 0.90,
            "ownership_verification": 0.95
        }
        
        # Initialize database tables
        if self.engine:
            Base.metadata.create_all(self.engine)
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules configuration"""
        return {
            "confidence_thresholds": {
                "ai_exemption_analysis": 0.85,
                "property_assessment": 0.90,
                "document_validation": 0.95
            },
            "mandatory_reviews": [
                "high_value_exemption",  # > $50,000
                "unusual_property_type",
                "ownership_change_pending",
                "ai_confidence_below_threshold"
            ],
            "retention_periods": {
                "audit_logs": 2555,  # 7 years in days
                "document_traces": 3650,  # 10 years
                "compliance_reports": 1825  # 5 years
            },
            "notification_rules": {
                "critical_flags": ["assessor", "supervisor"],
                "high_flags": ["assessor"],
                "medium_flags": ["system_admin"]
            }
        }
    
    def log_ai_analysis(self, 
                       record_type: str,
                       record_id: str, 
                       ai_model: str,
                       model_version: str,
                       analysis_result: Dict[str, Any],
                       user_id: str = None) -> str:
        """
        Log AI analysis operation with compliance tracking.
        
        Args:
            record_type: Type of record analyzed
            record_id: ID of the record
            ai_model: AI model used
            model_version: Version of the AI model
            analysis_result: Results from AI analysis
            user_id: User who initiated the analysis
            
        Returns:
            Operation ID for tracking
        """
        operation_id = self._generate_operation_id("ai_analysis")
        
        # Extract confidence score
        confidence_score = analysis_result.get("confidence_score", 0.0)
        
        # Check compliance flags
        compliance_flags = self._check_compliance_flags(
            record_type, analysis_result, confidence_score
        )
        
        # Determine if review is required
        review_required = self._requires_review(compliance_flags, confidence_score, record_type)
        
        # Create audit log entry
        audit_entry = ComplianceAuditLog(
            operation_id=operation_id,
            record_type=record_type,
            record_id=record_id,
            operation_type="ai_analysis",
            source_system=f"ai_model_{ai_model}",
            ai_model_version=model_version,
            confidence_score=confidence_score,
            user_id=user_id,
            data_hash=self._calculate_hash(analysis_result),
            change_summary=f"AI analysis using {ai_model} v{model_version}",
            compliance_flags=json.dumps([asdict(flag) for flag in compliance_flags]),
            review_required=review_required
        )
        
        # Save to database
        if self.Session:
            session = self.Session()
            try:
                session.add(audit_entry)
                session.commit()
                logger.info(f"AI analysis logged: {operation_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log AI analysis: {str(e)}")
            finally:
                session.close()
        
        # Trigger notifications if needed
        if review_required:
            self._trigger_compliance_notification(compliance_flags, operation_id)
        
        return operation_id
    
    def log_data_change(self,
                       record_type: str,
                       record_id: str,
                       operation_type: str,
                       old_data: Dict[str, Any],
                       new_data: Dict[str, Any],
                       source_system: str,
                       user_id: str = None) -> str:
        """
        Log data change operation with full audit trail.
        
        Args:
            record_type: Type of record changed
            record_id: ID of the record
            operation_type: Type of operation (create, update, delete)
            old_data: Previous state of the data
            new_data: New state of the data
            source_system: System that made the change
            user_id: User who made the change
            
        Returns:
            Operation ID for tracking
        """
        operation_id = self._generate_operation_id(operation_type)
        
        # Calculate change summary
        change_summary = self._generate_change_summary(old_data, new_data, operation_type)
        
        # Check for compliance violations
        compliance_flags = self._validate_data_change(
            record_type, old_data, new_data, operation_type
        )
        
        # Create audit log entry
        audit_entry = ComplianceAuditLog(
            operation_id=operation_id,
            record_type=record_type,
            record_id=record_id,
            operation_type=operation_type,
            source_system=source_system,
            user_id=user_id,
            data_hash=self._calculate_hash(new_data),
            change_summary=change_summary,
            compliance_flags=json.dumps([asdict(flag) for flag in compliance_flags]),
            review_required=any(flag.requires_review for flag in compliance_flags)
        )
        
        # Save to database
        if self.Session:
            session = self.Session()
            try:
                session.add(audit_entry)
                session.commit()
                logger.info(f"Data change logged: {operation_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log data change: {str(e)}")
            finally:
                session.close()
        
        return operation_id
    
    def track_document(self,
                      document_path: str,
                      document_type: str,
                      related_records: List[str]) -> DocumentTrace:
        """
        Track document for compliance and traceability.
        
        Args:
            document_path: Path to the document
            document_type: Type of document
            related_records: List of related record IDs
            
        Returns:
            Document trace record
        """
        document_file = Path(document_path)
        
        if not document_file.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        # Calculate checksum
        checksum = self._calculate_file_checksum(document_file)
        
        # Create document trace
        doc_trace = DocumentTrace(
            document_id=str(uuid.uuid4()),
            document_type=document_type,
            source_file=str(document_file.absolute()),
            creation_date=datetime.fromtimestamp(document_file.stat().st_ctime),
            last_modified=datetime.fromtimestamp(document_file.stat().st_mtime),
            checksum=checksum,
            related_records=related_records,
            compliance_status="tracked"
        )
        
        self.document_traces.append(doc_trace)
        
        logger.info(f"Document tracked: {doc_trace.document_id}")
        return doc_trace
    
    def flag_for_review(self,
                       record_type: str,
                       record_id: str,
                       reason: str,
                       priority: str = "medium") -> str:
        """
        Flag a record for manual review.
        
        Args:
            record_type: Type of record
            record_id: Record ID
            reason: Reason for flagging
            priority: Priority level
            
        Returns:
            Operation ID for the flag
        """
        operation_id = self._generate_operation_id("flag_review")
        
        # Create compliance flag
        compliance_flag = ComplianceFlag(
            flag_type="workflow",
            severity=priority,
            description=reason,
            rule_id="manual_flag",
            auto_generated=False,
            requires_review=True
        )
        
        # Create audit log entry
        audit_entry = ComplianceAuditLog(
            operation_id=operation_id,
            record_type=record_type,
            record_id=record_id,
            operation_type="flag_review",
            source_system="manual",
            change_summary=f"Flagged for review: {reason}",
            compliance_flags=json.dumps([asdict(compliance_flag)]),
            review_required=True
        )
        
        # Save to database
        if self.Session:
            session = self.Session()
            try:
                session.add(audit_entry)
                session.commit()
                logger.info(f"Record flagged for review: {operation_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to flag record: {str(e)}")
            finally:
                session.close()
        
        return operation_id
    
    def get_review_queue(self, user_role: str = None) -> List[Dict[str, Any]]:
        """
        Get records pending review.
        
        Args:
            user_role: Filter by user role permissions
            
        Returns:
            List of records pending review
        """
        if not self.Session:
            return []
        
        session = self.Session()
        
        try:
            query = session.query(ComplianceAuditLog).filter(
                ComplianceAuditLog.review_required == True,
                ComplianceAuditLog.reviewed_at.is_(None)
            ).order_by(ComplianceAuditLog.timestamp.desc())
            
            review_items = []
            for log_entry in query.all():
                flags = json.loads(log_entry.compliance_flags or "[]")
                
                review_items.append({
                    "operation_id": log_entry.operation_id,
                    "record_type": log_entry.record_type,
                    "record_id": log_entry.record_id,
                    "operation_type": log_entry.operation_type,
                    "timestamp": log_entry.timestamp.isoformat(),
                    "confidence_score": log_entry.confidence_score,
                    "change_summary": log_entry.change_summary,
                    "compliance_flags": flags,
                    "priority": self._determine_priority(flags)
                })
            
            return review_items
            
        except Exception as e:
            logger.error(f"Error getting review queue: {str(e)}")
            return []
        finally:
            session.close()
    
    def complete_review(self,
                       operation_id: str,
                       reviewer_id: str,
                       review_notes: str,
                       approved: bool) -> bool:
        """
        Complete a compliance review.
        
        Args:
            operation_id: Operation ID being reviewed
            reviewer_id: ID of the reviewer
            review_notes: Review notes
            approved: Whether the review was approved
            
        Returns:
            Success status
        """
        if not self.Session:
            return False
        
        session = self.Session()
        
        try:
            # Update the audit log entry
            log_entry = session.query(ComplianceAuditLog).filter(
                ComplianceAuditLog.operation_id == operation_id
            ).first()
            
            if not log_entry:
                logger.error(f"Audit log entry not found: {operation_id}")
                return False
            
            log_entry.reviewed_by = reviewer_id
            log_entry.reviewed_at = datetime.utcnow()
            log_entry.review_notes = review_notes
            log_entry.review_required = False
            
            # Add approval status to notes
            status = "APPROVED" if approved else "REJECTED"
            log_entry.review_notes = f"{status}: {review_notes}"
            
            session.commit()
            logger.info(f"Review completed for operation: {operation_id}")
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error completing review: {str(e)}")
            return False
        finally:
            session.close()
    
    def _check_compliance_flags(self,
                               record_type: str,
                               analysis_result: Dict[str, Any],
                               confidence_score: float) -> List[ComplianceFlag]:
        """Check for compliance flags based on analysis results"""
        flags = []
        
        # Low confidence flag
        threshold = self.confidence_thresholds.get(record_type, 0.85)
        if confidence_score < threshold:
            flags.append(ComplianceFlag(
                flag_type="confidence",
                severity="medium" if confidence_score > 0.7 else "high",
                description=f"AI confidence below threshold ({confidence_score:.2f} < {threshold})",
                rule_id="low_confidence",
                auto_generated=True,
                requires_review=True
            ))
        
        # High value exemption flag
        if record_type == "exemption" and analysis_result.get("exemption_amount", 0) > 50000:
            flags.append(ComplianceFlag(
                flag_type="regulatory",
                severity="high",
                description="High value exemption requires additional review",
                rule_id="high_value_exemption",
                auto_generated=True,
                requires_review=True
            ))
        
        return flags
    
    def _requires_review(self,
                        compliance_flags: List[ComplianceFlag],
                        confidence_score: float,
                        record_type: str) -> bool:
        """Determine if a record requires manual review"""
        
        # Any flag that requires review
        if any(flag.requires_review for flag in compliance_flags):
            return True
        
        # Critical or high severity flags
        critical_flags = [flag for flag in compliance_flags if flag.severity in ["critical", "high"]]
        if critical_flags:
            return True
        
        # Low confidence scores
        threshold = self.confidence_thresholds.get(record_type, 0.85)
        if confidence_score < threshold:
            return True
        
        return False
    
    def _generate_operation_id(self, operation_type: str) -> str:
        """Generate unique operation ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{operation_type}_{timestamp}"
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of data"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _generate_change_summary(self,
                                old_data: Dict[str, Any],
                                new_data: Dict[str, Any],
                                operation_type: str) -> str:
        """Generate human-readable change summary"""
        
        if operation_type == "create":
            return "New record created"
        elif operation_type == "delete":
            return "Record deleted"
        
        # For updates, identify changed fields
        changed_fields = []
        for key in new_data:
            if key in old_data and old_data[key] != new_data[key]:
                changed_fields.append(f"{key}: {old_data[key]} → {new_data[key]}")
        
        if changed_fields:
            return f"Updated fields: {', '.join(changed_fields[:5])}"  # Limit to 5 fields
        else:
            return "No changes detected"
    
    def _validate_data_change(self,
                             record_type: str,
                             old_data: Dict[str, Any],
                             new_data: Dict[str, Any],
                             operation_type: str) -> List[ComplianceFlag]:
        """Validate data changes for compliance violations"""
        flags = []
        
        # Example validation rules
        if record_type == "exemption" and operation_type == "update":
            # Check for significant value changes
            old_amount = old_data.get("exemption_amount", 0)
            new_amount = new_data.get("exemption_amount", 0)
            
            if abs(new_amount - old_amount) > old_amount * 0.5:  # 50% change
                flags.append(ComplianceFlag(
                    flag_type="validation",
                    severity="high",
                    description=f"Large exemption amount change: {old_amount} → {new_amount}",
                    rule_id="large_value_change",
                    auto_generated=True,
                    requires_review=True
                ))
        
        return flags
    
    def _determine_priority(self, flags: List[Dict[str, Any]]) -> str:
        """Determine priority based on compliance flags"""
        if any(flag.get("severity") == "critical" for flag in flags):
            return "critical"
        elif any(flag.get("severity") == "high" for flag in flags):
            return "high"
        else:
            return "medium"
    
    def _trigger_compliance_notification(self,
                                       compliance_flags: List[ComplianceFlag],
                                       operation_id: str):
        """Trigger notifications for compliance issues"""
        # This would integrate with notification system
        logger.info(f"Compliance notification triggered for operation: {operation_id}")
        
        for flag in compliance_flags:
            if flag.severity in ["critical", "high"]:
                logger.warning(f"High priority compliance flag: {flag.description}")

def main():
    """Main function for compliance tracking demonstration"""
    logger.info("Starting Compliance Tracking Layer - Phase II Implementation")
    
    # Initialize compliance tracker
    tracker = ComplianceTracker()
    
    # Example AI analysis logging
    ai_result = {
        "confidence_score": 0.82,
        "exemption_amount": 75000,
        "recommendation": "approve",
        "risk_factors": ["high_value", "new_applicant"]
    }
    
    operation_id = tracker.log_ai_analysis(
        record_type="exemption",
        record_id="EX-2024-001",
        ai_model="ExemptionSeer",
        model_version="2.1.0",
        analysis_result=ai_result,
        user_id="assessor_001"
    )
    
    # Get review queue
    review_queue = tracker.get_review_queue()
    
    logger.info("Compliance Tracking Layer Phase II - Complete")
    
    return {
        "status": "success",
        "operation_logged": operation_id,
        "review_queue_size": len(review_queue),
        "compliance_features": [
            "AI analysis tracking",
            "Document traceability",
            "Automated compliance flagging",
            "Review queue management",
            "Audit trail maintenance"
        ]
    }

if __name__ == "__main__":
    result = main()
    print(f"Compliance Tracking Result: {result}")