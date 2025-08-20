"""
Smartsheet Compliance Analyzer - Analyzer Package

This package contains the core data processing, analysis, and comparison logic
for the Smartsheet Compliance Analyzer tool. It exposes the necessary models
and processing functions for use by other parts of the application.
"""

# Import from submodules using relative imports
from .models import (
    ControlValue, 
    ClientControls, 
    ComplianceItem,
    ComplianceScanResult, 
    ComparisonResult
)

from .processor import (
    extract_client_controls,
    extract_compliance_items,
    compare_results,
    process_compliance_data
)

# Define what is publicly available when importing from the 'analyzer' package
__all__ = [
    # Processing functions from processor.py
    'extract_client_controls',
    'extract_compliance_items',
    'compare_results',
    'process_compliance_data',
    
    # Models from models.py
    'ControlValue',
    'ClientControls',
    'ComplianceItem',
    'ComplianceScanResult',
    'ComparisonResult'
]