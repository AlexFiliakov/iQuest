"""
Unit tests for XML validation and error handling functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

from src.utils.xml_validator import (
    AppleHealthXMLValidator, 
    ValidationRule, 
    ValidationResult,
    validate_apple_health_xml
)
from src.utils.error_handler import DataValidationError


class TestValidationRule:
    """Test the ValidationRule dataclass."""
    
    def test_create_validation_rule(self):
        """Test creating a validation rule."""
        rule = ValidationRule(
            field_name='testField',
            required=True,
            data_type='string',
            pattern=r'^[A-Za-z]+$',
            description='Test field'
        )
        
        assert rule.field_name == 'testField'
        assert rule.required is True
        assert rule.data_type == 'string'
        assert rule.pattern == r'^[A-Za-z]+$'
        assert rule.description == 'Test field'


class TestValidationResult:
    """Test the ValidationResult dataclass."""
    
    def test_create_validation_result(self):
        """Test creating a validation result."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.record_count == 0
    
    def test_add_error(self):
        """Test adding an error."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert "Test error" in result.errors
    
    def test_add_warning(self):
        """Test adding a warning."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.add_warning("Test warning")
        
        assert result.is_valid is True
        assert "Test warning" in result.warnings
    
    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult(is_valid=True, errors=[], warnings=[], record_count=5)
        result2 = ValidationResult(is_valid=False, errors=["Error 1"], warnings=["Warning 1"], record_count=3)
        
        result1.merge(result2)
        
        assert result1.is_valid is False
        assert "Error 1" in result1.errors
        assert "Warning 1" in result1.warnings
        assert result1.record_count == 8


class TestAppleHealthXMLValidator:
    """Test the main XML validator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = AppleHealthXMLValidator()
    
    def test_default_rules_loaded(self):
        """Test that default validation rules are loaded."""
        rules = self.validator.validation_rules
        
        assert 'creationDate' in rules
        assert 'sourceName' in rules
        assert 'type' in rules
        assert 'value' in rules
        
        # Check specific rule properties
        assert rules['creationDate'].required is True
        assert rules['creationDate'].data_type == 'datetime'
        assert rules['value'].data_type == 'float'
    
    def test_custom_rules_override(self):
        """Test that custom rules override defaults."""
        custom_rules = {
            'customField': ValidationRule(
                field_name='customField',
                required=True,
                data_type='integer'
            )
        }
        
        validator = AppleHealthXMLValidator(custom_rules)
        
        assert 'customField' in validator.validation_rules
        assert validator.validation_rules['customField'].data_type == 'integer'
    
    def create_test_xml_file(self, content: str) -> str:
        """Helper to create a temporary XML file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(content)
            return f.name
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        result = self.validator.validate_xml_file("nonexistent.xml")
        
        assert result.is_valid is False
        assert any("does not exist" in error for error in result.errors)
    
    def test_validate_invalid_xml_format(self):
        """Test validation of invalid XML format."""
        invalid_xml = "This is not XML content"
        xml_file = self.create_test_xml_file(invalid_xml)
        
        try:
            result = self.validator.validate_xml_file(xml_file)
            
            assert result.is_valid is False
            assert any("does not appear to be a valid XML file" in error for error in result.errors)
        finally:
            os.unlink(xml_file)
    
    def test_validate_wrong_root_element(self):
        """Test validation of XML with wrong root element."""
        wrong_root_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <WrongRoot>
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00" 
                    value="1000"/>
        </WrongRoot>'''
        
        xml_file = self.create_test_xml_file(wrong_root_xml)
        
        try:
            result = self.validator.validate_xml_file(xml_file)
            
            assert result.is_valid is False
            assert any("Expected root element 'HealthData'" in error for error in result.errors)
        finally:
            os.unlink(xml_file)
    
    def test_validate_no_records(self):
        """Test validation of XML with no health records."""
        no_records_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(no_records_xml)
        
        try:
            result = self.validator.validate_xml_file(xml_file)
            
            assert result.is_valid is False
            assert any("No health records found" in error for error in result.errors)
        finally:
            os.unlink(xml_file)
    
    def test_validate_valid_xml(self):
        """Test validation of valid Apple Health XML."""
        valid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00" 
                    value="1000"
                    unit="count"/>
            <Record type="HKQuantityTypeIdentifierHeartRate" 
                    sourceName="Apple Watch" 
                    creationDate="2024-01-01T10:01:00+00:00" 
                    value="65"
                    unit="count/min"/>
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(valid_xml)
        
        try:
            result = self.validator.validate_xml_file(xml_file)
            
            assert result.is_valid is True
            assert result.record_count == 2
            assert len(result.errors) == 0
        finally:
            os.unlink(xml_file)
    
    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields."""
        missing_fields_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone"/>
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(missing_fields_xml)
        
        try:
            result = self.validator.validate_xml_file(xml_file)
            
            assert result.is_valid is False
            assert any("Missing required field 'creationDate'" in error for error in result.errors)
            assert any("Missing required field 'value'" in error for error in result.errors)
        finally:
            os.unlink(xml_file)
    
    def test_validate_invalid_datetime(self):
        """Test validation with invalid datetime format."""
        invalid_date_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="invalid-date" 
                    value="1000"/>
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(invalid_date_xml)
        
        try:
            result = self.validator.validate_xml_file(xml_file)
            
            assert result.is_valid is False
            assert any("Invalid datetime format" in error for error in result.errors)
        finally:
            os.unlink(xml_file)
    
    def test_validate_invalid_numeric_value(self):
        """Test validation with invalid numeric value."""
        invalid_value_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00" 
                    value="not-a-number"/>
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(invalid_value_xml)
        
        try:
            result = self.validator.validate_xml_file(xml_file)
            
            assert result.is_valid is False
            assert any("Invalid numeric value" in error for error in result.errors)
        finally:
            os.unlink(xml_file)
    
    def test_get_user_friendly_summary_valid(self):
        """Test user-friendly summary for valid results."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], record_count=100)
        
        summary = self.validator.get_user_friendly_summary(result)
        
        assert "✅ Validation successful" in summary
        assert "100" in summary
    
    def test_get_user_friendly_summary_invalid(self):
        """Test user-friendly summary for invalid results."""
        result = ValidationResult(is_valid=False, errors=["Error 1", "Error 2"], warnings=["Warning 1"])
        
        summary = self.validator.get_user_friendly_summary(result)
        
        assert "❌ Validation failed" in summary
        assert "2 error(s)" in summary
        assert "1 warning(s)" in summary
        assert "Error 1" in summary
        assert "Suggested Actions:" in summary


class TestValidationIntegration:
    """Integration tests for the validation system."""
    
    def test_validate_apple_health_xml_convenience_function(self):
        """Test the convenience function for validation."""
        valid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00" 
                    value="1000"/>
        </HealthData>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(valid_xml)
            xml_file = f.name
        
        try:
            result = validate_apple_health_xml(xml_file)
            
            assert result.is_valid is True
            assert result.record_count == 1
        finally:
            os.unlink(xml_file)
    
    def test_validate_with_custom_rules(self):
        """Test validation with custom rules."""
        custom_rules = {
            'customField': ValidationRule(
                field_name='customField',
                required=True,
                data_type='string'
            )
        }
        
        xml_with_custom = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00" 
                    value="1000"
                    customField="test"/>
        </HealthData>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_with_custom)
            xml_file = f.name
        
        try:
            result = validate_apple_health_xml(xml_file, custom_rules)
            
            assert result.is_valid is True
        finally:
            os.unlink(xml_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])