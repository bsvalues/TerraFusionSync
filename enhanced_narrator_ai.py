"""
Enhanced NarratorAI Output Module

This module enhances the NarratorAI responses with markdown formatting,
confidence scores, and user-friendly summaries for county staff.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class EnhancedNarratorAI:
    """
    Enhanced NarratorAI wrapper that provides user-friendly output formatting
    and confidence scoring for county staff consumption.
    """
    
    def __init__(self):
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
    
    def format_gis_analysis(self, raw_analysis: str, data_context: Dict) -> Dict:
        """
        Format GIS export analysis into user-friendly markdown with confidence scoring.
        
        Args:
            raw_analysis: Raw AI analysis text
            data_context: Context about the GIS data being analyzed
            
        Returns:
            Formatted analysis with markdown, confidence scores, and recommendations
        """
        try:
            # Calculate confidence based on data quality indicators
            confidence_score = self._calculate_confidence(raw_analysis, data_context)
            confidence_level = self._get_confidence_level(confidence_score)
            
            # Format the analysis into structured sections
            formatted_analysis = {
                "summary": self._extract_executive_summary(raw_analysis),
                "detailed_analysis": self._format_detailed_analysis(raw_analysis),
                "key_insights": self._extract_key_insights(raw_analysis),
                "recommendations": self._generate_recommendations(raw_analysis, data_context),
                "data_quality": self._assess_data_quality(data_context),
                "confidence": {
                    "score": round(confidence_score, 2),
                    "level": confidence_level,
                    "explanation": self._get_confidence_explanation(confidence_score)
                },
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "data_records": data_context.get("record_count", 0),
                    "export_format": data_context.get("format", "unknown"),
                    "processing_time": data_context.get("duration_seconds", 0)
                }
            }
            
            return formatted_analysis
            
        except Exception as e:
            logger.error(f"Error formatting GIS analysis: {e}")
            return self._get_error_response(str(e))
    
    def format_sync_analysis(self, raw_analysis: str, sync_context: Dict) -> Dict:
        """
        Format sync operation analysis for county staff understanding.
        
        Args:
            raw_analysis: Raw AI analysis of sync operation
            sync_context: Context about the sync operation
            
        Returns:
            User-friendly analysis of sync performance and issues
        """
        try:
            confidence_score = self._calculate_sync_confidence(raw_analysis, sync_context)
            confidence_level = self._get_confidence_level(confidence_score)
            
            formatted_analysis = {
                "summary": self._extract_sync_summary(raw_analysis),
                "performance_analysis": self._format_sync_performance(raw_analysis, sync_context),
                "issues_identified": self._extract_sync_issues(raw_analysis),
                "recommendations": self._generate_sync_recommendations(raw_analysis, sync_context),
                "next_steps": self._suggest_next_steps(raw_analysis, sync_context),
                "confidence": {
                    "score": round(confidence_score, 2),
                    "level": confidence_level,
                    "explanation": self._get_confidence_explanation(confidence_score)
                },
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "records_processed": sync_context.get("records_processed", 0),
                    "sync_duration": sync_context.get("duration_seconds", 0),
                    "error_count": sync_context.get("errors", 0)
                }
            }
            
            return formatted_analysis
            
        except Exception as e:
            logger.error(f"Error formatting sync analysis: {e}")
            return self._get_error_response(str(e))
    
    def _extract_executive_summary(self, analysis: str) -> str:
        """Extract or generate an executive summary in markdown format."""
        # Look for existing summary or create one from first paragraph
        lines = analysis.split('\n')
        summary_lines = []
        
        for line in lines[:3]:  # Take first few lines
            if line.strip() and not line.startswith('#'):
                summary_lines.append(line.strip())
        
        summary = ' '.join(summary_lines)
        
        # Ensure it's concise (max 200 characters)
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        return f"**Executive Summary:** {summary}"
    
    def _format_detailed_analysis(self, analysis: str) -> str:
        """Format the detailed analysis with proper markdown structure."""
        # Add markdown headers and formatting
        formatted = analysis
        
        # Convert simple patterns to markdown
        formatted = re.sub(r'^(\d+\.?\s+)', r'* ', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'\b(ERROR|CRITICAL|WARNING)\b', r'**\1**', formatted)
        formatted = re.sub(r'\b(SUCCESS|COMPLETED|GOOD)\b', r'✅ **\1**', formatted)
        
        return formatted
    
    def _extract_key_insights(self, analysis: str) -> List[str]:
        """Extract key insights as bullet points."""
        insights = []
        
        # Look for patterns that indicate important findings
        patterns = [
            r'(?:found|identified|discovered|detected)\s+(.+?)(?:\.|$)',
            r'(?:shows|indicates|suggests|reveals)\s+(.+?)(?:\.|$)',
            r'(?:key|important|significant|notable)\s+(.+?)(?:\.|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, analysis, re.IGNORECASE)
            for match in matches[:3]:  # Limit to 3 insights per pattern
                cleaned_insight = match.strip()
                if len(cleaned_insight) > 10 and cleaned_insight not in insights:
                    insights.append(f"• {cleaned_insight}")
        
        # If no patterns found, extract first few sentences
        if not insights:
            sentences = re.split(r'[.!?]+', analysis)
            for sentence in sentences[:3]:
                if len(sentence.strip()) > 20:
                    insights.append(f"• {sentence.strip()}")
        
        return insights[:5]  # Maximum 5 insights
    
    def _generate_recommendations(self, analysis: str, context: Dict) -> List[str]:
        """Generate actionable recommendations for county staff."""
        recommendations = []
        
        # Based on data size
        record_count = context.get("record_count", 0)
        if record_count > 10000:
            recommendations.append("📊 Large dataset detected - consider filtering for faster processing")
        
        # Based on format
        export_format = context.get("format", "")
        if export_format == "csv":
            recommendations.append("📋 CSV format chosen - geometry data will be simplified to coordinates")
        elif export_format == "kml":
            recommendations.append("🌍 KML format works best for visualization in Google Earth")
        
        # Based on processing time
        duration = context.get("duration_seconds", 0)
        if duration > 30:
            recommendations.append("⏱️ Processing took longer than expected - consider smaller area or fewer layers")
        
        # Generic recommendations
        recommendations.append("💾 Save export results to shared county drive for team access")
        recommendations.append("📧 Share analysis summary with relevant department stakeholders")
        
        return recommendations
    
    def _assess_data_quality(self, context: Dict) -> Dict:
        """Assess the quality of the data being analyzed."""
        quality_score = 0.8  # Base score
        issues = []
        strengths = []
        
        # Check record count
        record_count = context.get("record_count", 0)
        if record_count > 1000:
            strengths.append("Substantial dataset size")
            quality_score += 0.1
        elif record_count < 100:
            issues.append("Small dataset size may limit analysis depth")
            quality_score -= 0.1
        
        # Check processing success
        if context.get("duration_seconds", 0) < 30:
            strengths.append("Fast processing indicates clean data")
        else:
            issues.append("Longer processing time may indicate data complexity")
            quality_score -= 0.05
        
        return {
            "score": min(1.0, max(0.0, quality_score)),
            "level": "high" if quality_score > 0.8 else "medium" if quality_score > 0.6 else "low",
            "issues": issues,
            "strengths": strengths
        }
    
    def _calculate_confidence(self, analysis: str, context: Dict) -> float:
        """Calculate confidence score based on analysis quality and data context."""
        confidence = 0.7  # Base confidence
        
        # Boost confidence for longer, more detailed analysis
        if len(analysis) > 200:
            confidence += 0.1
        
        # Boost for larger datasets (more data = more reliable analysis)
        record_count = context.get("record_count", 0)
        if record_count > 1000:
            confidence += 0.1
        elif record_count < 100:
            confidence -= 0.1
        
        # Reduce confidence for very fast processing (might indicate issues)
        if context.get("duration_seconds", 0) < 2:
            confidence -= 0.1
        
        # Check for uncertainty markers in analysis
        uncertainty_markers = ["might", "possibly", "unclear", "uncertain", "unknown"]
        uncertainty_count = sum(1 for marker in uncertainty_markers if marker in analysis.lower())
        confidence -= uncertainty_count * 0.05
        
        return min(1.0, max(0.1, confidence))
    
    def _calculate_sync_confidence(self, analysis: str, context: Dict) -> float:
        """Calculate confidence score for sync operation analysis."""
        confidence = 0.8  # Base confidence for sync operations
        
        # Check error rate
        records_processed = context.get("records_processed", 1)
        errors = context.get("errors", 0)
        error_rate = errors / records_processed if records_processed > 0 else 0
        
        if error_rate < 0.01:  # Less than 1% error rate
            confidence += 0.1
        elif error_rate > 0.05:  # More than 5% error rate
            confidence -= 0.2
        
        # Check completion status
        if context.get("status") == "COMPLETED":
            confidence += 0.1
        elif context.get("status") == "FAILED":
            confidence -= 0.3
        
        return min(1.0, max(0.1, confidence))
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert confidence score to human-readable level."""
        if score >= self.confidence_thresholds["high"]:
            return "high"
        elif score >= self.confidence_thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def _get_confidence_explanation(self, score: float) -> str:
        """Provide explanation for confidence level."""
        if score >= 0.8:
            return "High confidence - analysis based on substantial data with clear patterns"
        elif score >= 0.6:
            return "Medium confidence - analysis is reliable but may benefit from additional data"
        else:
            return "Lower confidence - limited data or unclear patterns detected"
    
    def _extract_sync_summary(self, analysis: str) -> str:
        """Extract summary specific to sync operations."""
        # Look for sync-specific patterns
        lines = analysis.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['sync', 'processed', 'records', 'complete']):
                return f"**Sync Summary:** {line.strip()}"
        
        # Fallback to general summary
        return self._extract_executive_summary(analysis)
    
    def _format_sync_performance(self, analysis: str, context: Dict) -> str:
        """Format sync performance metrics in user-friendly way."""
        records_processed = context.get("records_processed", 0)
        duration = context.get("duration_seconds", 0)
        errors = context.get("errors", 0)
        
        performance_md = f"""
**Sync Performance Metrics:**

• **Records Processed:** {records_processed:,}
• **Processing Time:** {duration:.1f} seconds
• **Processing Rate:** {records_processed/duration:.0f} records/second
• **Error Count:** {errors}
• **Success Rate:** {((records_processed-errors)/records_processed*100):.1f}%
        """.strip()
        
        return performance_md
    
    def _extract_sync_issues(self, analysis: str) -> List[str]:
        """Extract sync-specific issues and warnings."""
        issues = []
        
        # Look for error patterns
        error_patterns = [
            r'error[s]?\s+(.+?)(?:\.|$)',
            r'fail[ed|ure]\s+(.+?)(?:\.|$)',
            r'warning[s]?\s+(.+?)(?:\.|$)'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, analysis, re.IGNORECASE)
            for match in matches:
                issues.append(f"⚠️ {match.strip()}")
        
        return issues[:5]  # Limit to 5 issues
    
    def _generate_sync_recommendations(self, analysis: str, context: Dict) -> List[str]:
        """Generate sync-specific recommendations."""
        recommendations = []
        
        error_rate = context.get("errors", 0) / max(context.get("records_processed", 1), 1)
        
        if error_rate > 0.05:
            recommendations.append("🔍 High error rate detected - review data source quality")
        
        if context.get("duration_seconds", 0) > 60:
            recommendations.append("⚡ Consider processing in smaller batches for better performance")
        
        recommendations.append("📋 Schedule regular sync operations during off-peak hours")
        recommendations.append("💾 Monitor disk space before large sync operations")
        
        return recommendations
    
    def _suggest_next_steps(self, analysis: str, context: Dict) -> List[str]:
        """Suggest concrete next steps for county staff."""
        next_steps = []
        
        if context.get("status") == "COMPLETED":
            next_steps.append("✅ Verify exported data meets department requirements")
            next_steps.append("📤 Distribute results to relevant stakeholders")
        elif context.get("status") == "FAILED":
            next_steps.append("🔧 Contact IT support to investigate sync failure")
            next_steps.append("📞 Review error logs for specific issues")
        
        next_steps.append("📊 Update department dashboard with latest data")
        next_steps.append("📅 Schedule next sync operation if needed")
        
        return next_steps
    
    def _get_error_response(self, error_message: str) -> Dict:
        """Generate user-friendly error response."""
        return {
            "summary": "**Analysis Error:** Unable to process the requested analysis",
            "detailed_analysis": f"An error occurred during analysis: {error_message}",
            "key_insights": ["• Analysis could not be completed due to technical issues"],
            "recommendations": [
                "🔧 Contact system administrator for assistance",
                "📞 Provide error details when requesting support",
                "⏭️ Try again in a few minutes"
            ],
            "confidence": {
                "score": 0.0,
                "level": "low",
                "explanation": "Unable to provide reliable analysis due to processing error"
            },
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "error": True,
                "error_message": error_message
            }
        }