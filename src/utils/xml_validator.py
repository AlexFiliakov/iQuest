"""
XML Data Validation and Error Handling for Apple Health Monitor

This module provides comprehensive validation for Apple Health XML imports,
ensuring data integrity and providing clear error messages for users.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import re

from .logging_config import get_logger
from .error_handler import DataValidationError, ErrorContext

logger = get_logger(__name__)


@dataclass
class ValidationRule:
    """Defines a validation rule for XML elements.
    
    Encapsulates validation criteria for health data fields including
    data type constraints, value ranges, and format requirements.
    
    Attributes:
        field_name (str): Name of the field to validate.
        required (bool): Whether the field is required. Defaults to True.
        data_type (str): Expected data type ('string', 'datetime', 'float', 'integer').
        pattern (Optional[str]): Regex pattern for string validation.
        min_value (Optional[float]): Minimum allowed numeric value.
        max_value (Optional[float]): Maximum allowed numeric value.
        allowed_values (Optional[List[str]]): List of allowed string values.
        description (str): Human-readable description of the rule.
    """
    field_name: str
    required: bool = True
    data_type: str = "string"  # string, datetime, float, integer
    pattern: Optional[str] = None  # regex pattern for string validation
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None
    description: str = ""


@dataclass
class ValidationResult:
    """Result of validation operations.
    
    Contains the outcome of XML validation including errors, warnings,
    and statistics about the validation process.
    
    Attributes:
        is_valid (bool): Whether validation passed overall.
        errors (List[str]): List of validation error messages.
        warnings (List[str]): List of non-fatal warning messages.
        record_count (int): Total number of records processed.
        validated_records (int): Number of successfully validated records.
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    record_count: int = 0
    validated_records: int = 0
    
    def add_error(self, message: str):
        """Add an error message.
        
        Args:
            message (str): The error message to add.
        """
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message.
        
        Args:
            message (str): The warning message to add.
        """
        self.warnings.append(message)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.record_count += other.record_count
        self.validated_records += other.validated_records
        if not other.is_valid:
            self.is_valid = False


class AppleHealthXMLValidator:
    """Validator for Apple Health XML exports."""
    
    def __init__(self, configurable_rules: Optional[Dict[str, ValidationRule]] = None):
        """
        Initialize the validator with validation rules.
        
        Args:
            configurable_rules: Optional custom validation rules
        """
        self.logger = get_logger(__name__)
        self.validation_rules = self._get_default_rules()
        
        # Override with configurable rules if provided
        if configurable_rules:
            self.validation_rules.update(configurable_rules)
    
    def _get_default_rules(self) -> Dict[str, ValidationRule]:
        """Get the default validation rules for Apple Health data."""
        return {
            'creationDate': ValidationRule(
                field_name='creationDate',
                required=True,
                data_type='datetime',
                description='Date when the health record was created'
            ),
            'sourceName': ValidationRule(
                field_name='sourceName',
                required=True,
                data_type='string',
                pattern=r'^.{1,255}$',  # 1-255 characters
                description='Name of the device or app that created the record'
            ),
            'type': ValidationRule(
                field_name='type',
                required=True,
                data_type='string',
                pattern=r'^HK(Quantity|Category)TypeIdentifier.+',
                description='Apple Health data type identifier'
            ),
            'unit': ValidationRule(
                field_name='unit',
                required=False,
                data_type='string',
                description='Unit of measurement for the health data'
            ),
            'value': ValidationRule(
                field_name='value',
                required=True,
                data_type='float',
                min_value=0.0,
                description='Numeric value of the health measurement'
            ),
            'startDate': ValidationRule(
                field_name='startDate',
                required=False,
                data_type='datetime',
                description='Start date of the health measurement period'
            ),
            'endDate': ValidationRule(
                field_name='endDate',
                required=False,
                data_type='datetime',
                description='End date of the health measurement period'
            )
        }
    
    def validate_xml_file(self, xml_path: str) -> ValidationResult:
        """
        Validate an Apple Health XML file.
        
        Args:
            xml_path: Path to the XML file
            
        Returns:
            ValidationResult with validation outcomes
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        with ErrorContext("XML file validation", reraise=False) as ctx:
            # Check file existence and basic format
            file_result = self._validate_file_format(xml_path)
            result.merge(file_result)
            
            if not file_result.is_valid:
                return result
            
            # Parse and validate XML structure
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                structure_result = self._validate_xml_structure(root)
                result.merge(structure_result)
                
                if structure_result.is_valid:
                    # Validate individual records
                    records_result = self._validate_health_records(root)
                    result.merge(records_result)
                
            except ET.ParseError as e:
                result.add_error(f"XML parsing failed: {str(e)}")
            except Exception as e:
                result.add_error(f"Unexpected error during validation: {str(e)}")
        
        return result
    
    def _validate_file_format(self, xml_path: str) -> ValidationResult:
        """Validate basic file format and accessibility."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        file_path = Path(xml_path)
        
        # Check file existence
        if not file_path.exists():
            result.add_error(f"XML file does not exist: {xml_path}")
            return result
        
        # Check file size (warn if very large)
        file_size = file_path.stat().st_size
        if file_size > 500 * 1024 * 1024:  # 500MB
            result.add_warning(f"Large file detected ({file_size / (1024*1024):.1f}MB). Processing may take longer.")
        
        # Check file extension
        if file_path.suffix.lower() not in ['.xml']:
            result.add_warning(f"File extension '{file_path.suffix}' is not typical for XML files")
        
        # Try to read the file
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line.startswith('<?xml'):
                    result.add_error("File does not appear to be a valid XML file (missing XML declaration)")
        except UnicodeDecodeError:
            result.add_error("File encoding is not UTF-8 or is corrupted")
        except Exception as e:
            result.add_error(f"Cannot read file: {str(e)}")
        
        return result
    
    def _validate_xml_structure(self, root: ET.Element) -> ValidationResult:
        """Validate the overall XML structure for Apple Health format."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Check root element
        if root.tag != 'HealthData':
            result.add_error(f"Expected root element 'HealthData', found '{root.tag}'")
            return result
        
        # Check for required attributes on root
        if 'locale' not in root.attrib:
            result.add_warning("Root element missing 'locale' attribute")
        
        # Count Record elements
        record_elements = root.findall('.//Record')
        result.record_count = len(record_elements)
        
        if result.record_count == 0:
            result.add_error("No health records found in XML file")
        elif result.record_count > 1000000:  # 1M records
            result.add_warning(f"Large number of records ({result.record_count:,}). Processing may be slow.")
        
        self.logger.info(f"Found {result.record_count:,} health records in XML")
        
        return result
    
    def _validate_health_records(self, root: ET.Element) -> ValidationResult:
        """Validate individual health record elements."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        record_elements = root.findall('.//Record')
        sample_size = min(1000, len(record_elements))  # Validate first 1000 records for performance
        
        validation_stats = {
            'total_errors': 0,
            'total_warnings': 0,
            'field_errors': {},
            'missing_fields': set(),
            'invalid_types': set()
        }
        
        for i, record in enumerate(record_elements[:sample_size]):
            record_result = self._validate_single_record(record, i + 1)
            
            # Track statistics
            validation_stats['total_errors'] += len(record_result.errors)
            validation_stats['total_warnings'] += len(record_result.warnings)
            
            # If too many errors in sample, stop early
            if validation_stats['total_errors'] > 100:
                result.add_error(f"Too many validation errors in sample (>{validation_stats['total_errors']}). File may be severely corrupted.")
                break
            
            result.merge(record_result)
        
        result.validated_records = sample_size
        
        # Summary statistics
        if sample_size < len(record_elements):
            result.add_warning(f"Validated sample of {sample_size:,} records out of {len(record_elements):,} total")
        
        return result
    
    def _validate_single_record(self, record: ET.Element, record_number: int) -> ValidationResult:
        """Validate a single health record element."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Check that it's a Record element
        if record.tag != 'Record':
            result.add_error(f"Record {record_number}: Expected 'Record' element, found '{record.tag}'")
            return result
        
        # Validate each field according to rules
        for field_name, rule in self.validation_rules.items():
            field_value = record.attrib.get(field_name)
            
            # Check required fields
            if rule.required and field_value is None:
                result.add_error(f"Record {record_number}: Missing required field '{field_name}'")
                continue
            
            # Skip validation if field is optional and missing
            if field_value is None:
                continue
            
            # Validate field value
            field_result = self._validate_field_value(field_name, field_value, rule, record_number)
            result.merge(field_result)
        
        return result
    
    def _validate_field_value(self, field_name: str, value: str, rule: ValidationRule, record_number: int) -> ValidationResult:
        """Validate a single field value against its rule."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            # Data type validation
            if rule.data_type == 'datetime':
                try:
                    parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    # Check for reasonable date ranges
                    if parsed_date.year < 1900 or parsed_date.year > 2100:
                        result.add_warning(f"Record {record_number}: Unusual date in '{field_name}': {value}")
                except ValueError:
                    result.add_error(f"Record {record_number}: Invalid datetime format in '{field_name}': {value}")
            
            elif rule.data_type == 'float':
                try:
                    float_value = float(value)
                    if rule.min_value is not None and float_value < rule.min_value:
                        result.add_error(f"Record {record_number}: '{field_name}' value {float_value} below minimum {rule.min_value}")
                    if rule.max_value is not None and float_value > rule.max_value:
                        result.add_error(f"Record {record_number}: '{field_name}' value {float_value} above maximum {rule.max_value}")
                except ValueError:
                    result.add_error(f"Record {record_number}: Invalid numeric value in '{field_name}': {value}")
            
            elif rule.data_type == 'integer':
                try:
                    int_value = int(value)
                    if rule.min_value is not None and int_value < rule.min_value:
                        result.add_error(f"Record {record_number}: '{field_name}' value {int_value} below minimum {rule.min_value}")
                    if rule.max_value is not None and int_value > rule.max_value:
                        result.add_error(f"Record {record_number}: '{field_name}' value {int_value} above maximum {rule.max_value}")
                except ValueError:
                    result.add_error(f"Record {record_number}: Invalid integer value in '{field_name}': {value}")
            
            # String validation
            elif rule.data_type == 'string':
                if rule.pattern and not re.match(rule.pattern, value):
                    result.add_error(f"Record {record_number}: '{field_name}' value '{value}' does not match required pattern")
                
                if rule.allowed_values and value not in rule.allowed_values:
                    result.add_error(f"Record {record_number}: '{field_name}' value '{value}' not in allowed values: {rule.allowed_values}")
        
        except Exception as e:
            result.add_error(f"Record {record_number}: Unexpected error validating '{field_name}': {str(e)}")
        
        return result
    
    def get_user_friendly_summary(self, validation_result: ValidationResult) -> str:
        """
        Generate a user-friendly summary of validation results.
        
        Args:
            validation_result: The validation result to summarize
            
        Returns:
            Formatted summary message
        """
        if validation_result.is_valid:
            return f"✅ Validation successful! Processed {validation_result.record_count:,} health records."
        
        summary_lines = [
            f"❌ Validation failed with {len(validation_result.errors)} error(s)"
        ]
        
        if validation_result.warnings:
            summary_lines.append(f"⚠️  {len(validation_result.warnings)} warning(s)")
        
        # Show first few errors
        if validation_result.errors:
            summary_lines.append("\nKey Issues:")
            for error in validation_result.errors[:5]:
                summary_lines.append(f"  • {error}")
            
            if len(validation_result.errors) > 5:
                summary_lines.append(f"  ... and {len(validation_result.errors) - 5} more errors")
        
        # Provide actionable suggestions
        summary_lines.append("\nSuggested Actions:")
        if any("Missing required field" in error for error in validation_result.errors):
            summary_lines.append("  • Ensure your XML export includes all required fields")
        if any("Invalid datetime format" in error for error in validation_result.errors):
            summary_lines.append("  • Check that date fields are in ISO format (YYYY-MM-DDTHH:MM:SS)")
        if any("XML parsing failed" in error for error in validation_result.errors):
            summary_lines.append("  • Verify the XML file is not corrupted and is properly formatted")
        
        return "\n".join(summary_lines)


def validate_apple_health_xml(xml_path: str, custom_rules: Optional[Dict[str, ValidationRule]] = None) -> ValidationResult:
    """
    Convenience function to validate an Apple Health XML file.
    
    Args:
        xml_path: Path to the XML file
        custom_rules: Optional custom validation rules
        
    Returns:
        ValidationResult with validation outcomes
    """
    validator = AppleHealthXMLValidator(custom_rules)
    return validator.validate_xml_file(xml_path)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python xml_validator.py <path_to_xml_file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    result = validate_apple_health_xml(xml_file)
    
    print(AppleHealthXMLValidator().get_user_friendly_summary(result))