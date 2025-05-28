"""
Medical evidence validator for health insights.

This module validates evidence sources and ensures appropriate medical
disclaimers are applied to health insights.
"""

from typing import List, Optional, Dict, Any
from .health_insights_models import HealthInsight, InsightCategory, EvidenceLevel


class MedicalEvidenceValidator:
    """Validates medical evidence and ensures appropriate disclaimers."""
    
    # Credible medical sources
    CREDIBLE_SOURCES = {
        # Government health organizations
        'CDC': 'Centers for Disease Control and Prevention',
        'WHO': 'World Health Organization',
        'NIH': 'National Institutes of Health',
        'NHS': 'National Health Service',
        
        # Professional medical organizations
        'AHA': 'American Heart Association',
        'ACSM': 'American College of Sports Medicine',
        'AASM': 'American Academy of Sleep Medicine',
        'NSF': 'National Sleep Foundation',
        'ADA': 'American Diabetes Association',
        'ACE': 'American Council on Exercise',
        
        # Medical journals (abbreviated list)
        'NEJM': 'New England Journal of Medicine',
        'JAMA': 'Journal of the American Medical Association',
        'Lancet': 'The Lancet',
        'BMJ': 'British Medical Journal',
        
        # Research databases
        'PubMed': 'PubMed Central',
        'Cochrane': 'Cochrane Reviews',
        
        # Sports science
        'Sports Science': 'Peer-reviewed sports science research',
        'Exercise Science': 'Exercise science research'
    }
    
    # Medical disclaimer templates
    DISCLAIMER_TEMPLATES = {
        'general': "This analysis is for informational purposes only and does not constitute medical advice. Consult with healthcare professionals for personalized medical guidance.",
        
        'sleep': "Sleep recommendations are based on general guidelines. Individual sleep needs may vary. Consult a sleep specialist for persistent sleep issues.",
        
        'activity': "Exercise recommendations should be adapted to your fitness level and health conditions. Consult with healthcare providers before starting new exercise programs.",
        
        'heart_health': "Heart rate data is for general wellness tracking. Consult a cardiologist for any heart health concerns or abnormal readings.",
        
        'body_metrics': "Body metrics are general indicators. They don't account for individual variations in body composition. Consult healthcare providers for comprehensive health assessments.",
        
        'nutrition': "Nutritional insights are based on general guidelines. Individual dietary needs vary. Consult a registered dietitian for personalized nutrition advice.",
        
        'recovery': "Recovery metrics are indicators of general wellness. They are not diagnostic tools. Consult healthcare providers if you have concerns about recovery or fatigue.",
        
        'pattern_based': "This insight is based on patterns in your personal data. It may not reflect general medical recommendations.",
        
        'low_confidence': "This insight has lower statistical confidence due to limited data. Consider it as one factor among many in your health decisions.",
        
        'correlation': "Correlation does not imply causation. This relationship pattern may not indicate a direct cause-and-effect relationship."
    }
    
    # Categories requiring special medical attention
    HIGH_RISK_CATEGORIES = {
        InsightCategory.HEART_HEALTH: "Heart-related insights require medical supervision",
        InsightCategory.BODY_METRICS: "Significant weight changes should be discussed with healthcare providers"
    }
    
    def __init__(self):
        """Initialize the medical evidence validator."""
        self.validation_log = []
    
    def is_credible_source(self, source: str) -> bool:
        """Check if a source is from a credible medical organization."""
        # Check exact matches
        if source in self.CREDIBLE_SOURCES:
            return True
        
        # Check if source contains credible organization name
        source_upper = source.upper()
        for code, full_name in self.CREDIBLE_SOURCES.items():
            if code in source_upper or full_name.upper() in source_upper:
                return True
        
        # Check for common research indicators
        research_indicators = ['study', 'research', 'clinical trial', 'meta-analysis', 
                             'systematic review', 'peer-reviewed']
        source_lower = source.lower()
        return any(indicator in source_lower for indicator in research_indicators)
    
    def validate_evidence_sources(self, sources: List[str]) -> Dict[str, Any]:
        """Validate a list of evidence sources."""
        validated_sources = []
        credible_count = 0
        
        for source in sources:
            is_credible = self.is_credible_source(source)
            validated_sources.append({
                'source': source,
                'is_credible': is_credible
            })
            if is_credible:
                credible_count += 1
        
        return {
            'validated_sources': validated_sources,
            'credible_count': credible_count,
            'total_count': len(sources),
            'credibility_ratio': credible_count / len(sources) if sources else 0
        }
    
    def generate_medical_disclaimer(self, insight: HealthInsight) -> str:
        """Generate appropriate medical disclaimer for an insight."""
        disclaimers = []
        
        # Add general disclaimer
        disclaimers.append(self.DISCLAIMER_TEMPLATES['general'])
        
        # Add category-specific disclaimer
        category_disclaimer = self.DISCLAIMER_TEMPLATES.get(
            insight.category.value, 
            None
        )
        if category_disclaimer:
            disclaimers.append(category_disclaimer)
        
        # Add high-risk category warning
        if insight.category in self.HIGH_RISK_CATEGORIES:
            disclaimers.append(self.HIGH_RISK_CATEGORIES[insight.category])
        
        # Add pattern-based disclaimer if applicable
        if insight.evidence_level == EvidenceLevel.PATTERN_BASED:
            disclaimers.append(self.DISCLAIMER_TEMPLATES['pattern_based'])
        
        # Add low confidence disclaimer if applicable
        if insight.confidence < 70:
            disclaimers.append(self.DISCLAIMER_TEMPLATES['low_confidence'])
        
        # Add correlation disclaimer if applicable
        if insight.insight_type.value == 'correlation':
            disclaimers.append(self.DISCLAIMER_TEMPLATES['correlation'])
        
        # Combine disclaimers, removing duplicates
        unique_disclaimers = list(dict.fromkeys(disclaimers))
        return " ".join(unique_disclaimers)
    
    def add_evidence_context(self, insight: HealthInsight) -> HealthInsight:
        """Add evidence context to enhance credibility transparency."""
        # Validate sources
        validation_result = self.validate_evidence_sources(insight.evidence_sources)
        
        # Add validation metadata
        if 'evidence_validation' not in insight.supporting_data:
            insight.supporting_data['evidence_validation'] = {}
        
        insight.supporting_data['evidence_validation'] = {
            'credible_sources': validation_result['credible_count'],
            'total_sources': validation_result['total_count'],
            'credibility_ratio': validation_result['credibility_ratio'],
            'validation_timestamp': 'current'
        }
        
        # Adjust evidence level based on source credibility
        if validation_result['credibility_ratio'] == 0 and insight.evidence_level != EvidenceLevel.PATTERN_BASED:
            # Downgrade to pattern-based if no credible sources
            insight.evidence_level = EvidenceLevel.PATTERN_BASED
            
        # Add source attribution to description if high credibility
        if validation_result['credibility_ratio'] >= 0.8:
            credible_sources = [
                s['source'] for s in validation_result['validated_sources'] 
                if s['is_credible']
            ]
            if credible_sources and not insight.description.endswith('.'):
                insight.description += '.'
            insight.description += f" Based on guidelines from: {', '.join(credible_sources[:3])}."
        
        return insight
    
    def ensure_medical_safety(self, insight: HealthInsight) -> HealthInsight:
        """Ensure insight includes appropriate medical safety information."""
        # Generate comprehensive disclaimer
        insight.medical_disclaimer = self.generate_medical_disclaimer(insight)
        
        # Add evidence context
        insight = self.add_evidence_context(insight)
        
        # Add safety flags for high-risk insights
        if insight.category in self.HIGH_RISK_CATEGORIES:
            if 'safety_flags' not in insight.supporting_data:
                insight.supporting_data['safety_flags'] = []
            insight.supporting_data['safety_flags'].append('requires_medical_supervision')
        
        # Ensure recommendation doesn't overstep medical boundaries
        insight.recommendation = self._sanitize_recommendation(insight.recommendation, insight.category)
        
        # Log validation
        self.validation_log.append({
            'insight_title': insight.title,
            'category': insight.category.value,
            'evidence_level': insight.evidence_level.value,
            'has_credible_sources': insight.supporting_data.get('evidence_validation', {}).get('credibility_ratio', 0) > 0
        })
        
        return insight
    
    def _sanitize_recommendation(self, recommendation: str, category: InsightCategory) -> str:
        """Ensure recommendations don't make medical claims."""
        # Words to avoid in recommendations
        avoid_words = {
            'diagnose', 'cure', 'treat', 'prescribe', 'medication', 
            'disease', 'disorder', 'syndrome', 'condition'
        }
        
        # Replace medical terms with wellness-focused language
        replacements = {
            'treat': 'help manage',
            'cure': 'improve',
            'diagnose': 'monitor',
            'disease': 'health concern',
            'disorder': 'pattern',
            'condition': 'situation'
        }
        
        recommendation_lower = recommendation.lower()
        for avoid_word in avoid_words:
            if avoid_word in recommendation_lower:
                replacement = replacements.get(avoid_word, 'address')
                recommendation = recommendation.replace(avoid_word, replacement)
                recommendation = recommendation.replace(avoid_word.capitalize(), replacement.capitalize())
        
        # Ensure recommendations are framed as suggestions
        if not any(word in recommendation.lower() for word in ['try', 'consider', 'might', 'may', 'could']):
            recommendation = "Consider: " + recommendation
        
        return recommendation
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation activities."""
        if not self.validation_log:
            return {'total_validated': 0, 'insights_by_category': {}}
        
        summary = {
            'total_validated': len(self.validation_log),
            'with_credible_sources': sum(1 for log in self.validation_log if log['has_credible_sources']),
            'insights_by_category': {},
            'insights_by_evidence_level': {}
        }
        
        # Count by category
        for log in self.validation_log:
            category = log['category']
            if category not in summary['insights_by_category']:
                summary['insights_by_category'][category] = 0
            summary['insights_by_category'][category] += 1
            
            # Count by evidence level
            evidence_level = log['evidence_level']
            if evidence_level not in summary['insights_by_evidence_level']:
                summary['insights_by_evidence_level'][evidence_level] = 0
            summary['insights_by_evidence_level'][evidence_level] += 1
        
        return summary