"""
Smartsheet Compliance Analyzer - Data Models Module

This module defines the core data models used throughout the Smartsheet Compliance Analyzer.
It provides standardized structures for representing client controls, compliance items,
scan results, and comparison outcomes using Pydantic models for robust data validation.

Key Components:
- ControlValue: Maps placeholder variables to client-specific values
- ClientControls: Collection of control values for a specific client
- ComplianceItem: Represents compliance entries from Smartsheet with enhanced metadata
- ComplianceScanResult: Represents findings from external compliance scan tools
- ComparisonResult: Contains the matching logic outcomes and statistics

These models ensure consistent data handling across the application and provide
built-in validation through Pydantic's type checking system.
"""

from typing import Dict, List, Optional, Any, Set, Union
from pydantic import BaseModel, Field
from datetime import datetime


class ControlValue(BaseModel):
    """
    Represents a control placeholder and its client-specific value.
    
    These values are extracted from the Compensating Controls sheet and are used
    to replace placeholders in deviation rationales with client-specific information.
    
    Attributes:
        placeholder (str): The placeholder variable name (e.g., 'cloud_provider')
        value (str): The client-specific value (e.g., 'AWS')
    """
    placeholder: str
    value: str


class ClientControls(BaseModel):
    """
    Collection of all control placeholders and their values for a specific client.
    
    This model represents the complete set of client-specific values that will be
    used for placeholder substitution in compliance items.
    
    Attributes:
        client (str): The name of the client (e.g., 'Acme Corp')
        controls (List[ControlValue]): List of placeholder-value pairs for this client
        
    Methods:
        to_dict(): Converts the controls list to a simple dictionary for easier lookup
    """
    client: str
    controls: List[ControlValue] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert controls to a simple placeholder mapping dictionary.
        
        Returns:
            Dict[str, str]: Dictionary with placeholders as keys and client values as values
        """
        return {control.placeholder: control.value for control in self.controls}


class ComplianceItem(BaseModel):
    """
    Represents a compliance item from Smartsheet with processed placeholders.
    
    This model captures all relevant fields from the Compliance ClearingHouse sheet,
    including any processed deviation rationales where placeholders have been
    replaced with client-specific values.
    
    Attributes:
        compliance_id (Optional[str]): Unique identifier for the compliance item (e.g., 'RHEL-08-010030')
        finding_description (Optional[str]): Description of the compliance finding
        srg_solution (Optional[str]): Recommended Security Requirements Guide solution
        deviation_type (Optional[str]): Type of compliance deviation (e.g., 'Technical', 'Procedural')
        deviation_rationale (Optional[str]): Justification for deviation with replaced placeholders
        supporting_documents (Optional[str]): References to supporting documentation
        deviation_status (Optional[str]): Approval status of the deviation
        should_fix (Optional[bool]): Flag indicating if the item should be fixed
        comments (Optional[str]): Additional notes or comments
        status (Optional[str]): Status from scan results (if matched)
        severity (Optional[Union[str, int]]): Severity level from scan results
        hostname (Optional[str]): Host identifier from scan results
        
        # Metadata fields
        replaced_placeholders (Set[str]): Set of placeholders that were replaced in the rationale
        original_rationale (Optional[str]): The original rationale text before placeholder replacement
    """
    compliance_id: Optional[str] = None
    finding_description: Optional[str] = None
    srg_solution: Optional[str] = None
    deviation_type: Optional[str] = None
    deviation_rationale: Optional[str] = None
    supporting_documents: Optional[str] = None
    deviation_status: Optional[str] = None
    should_fix: Optional[bool] = None
    comments: Optional[str] = None
    status: Optional[str] = None  # From scan results
    severity: Optional[Union[str, int]] = None  # From scan results
    hostname: Optional[str] = None  # From scan results
    
    # Metadata fields
    replaced_placeholders: Set[str] = Field(
        default_factory=set, 
        description="Set of placeholders replaced in the rationale. When exported to Excel, this will be converted to a comma-separated string."
    )
    original_rationale: Optional[str] = None


class ComplianceScanResult(BaseModel):
    """
    Model for a single compliance scan result from external scanning tools.
    
    This model represents findings from compliance scans (e.g., Nessus, OpenSCAP)
    and normalizes the data into a consistent format regardless of the source.
    
    Attributes:
        compliance_id (str): Unique identifier for the compliance check (e.g., 'RHEL-08-010030')
        status (str): Status of the compliance check (e.g., 'Failed', 'Passed')
        severity (Optional[Union[str, int]]): Severity level of the finding
        hostname (Optional[str]): Identifier for the host or asset scanned
        description (Optional[str]): Description of the finding
        details (Optional[str]): Additional details about the finding
        additional_fields (Dict[str, Any]): Extra fields from the scan that don't map to standard fields
    """
    compliance_id: str
    status: str
    severity: Optional[Union[str, int]] = None
    hostname: Optional[str] = None
    description: Optional[str] = None
    details: Optional[str] = None
    additional_fields: Dict[str, Any] = Field(default_factory=dict)


class ComparisonResult(BaseModel):
    """
    Container for the results of comparing scan data with Smartsheet data.
    
    This model holds the final comparison results, including matched items,
    unmatched items from both sources, and overall statistics. It serves as
    the basis for generating the Excel report.
    
    Attributes:
        matched_items (List[ComplianceItem]): Compliance items found in both scan and Smartsheet
        unmatched_scan_items (List[ComplianceScanResult]): Items found only in scan results
        unmatched_smartsheet_items (List[ComplianceItem]): Items found only in Smartsheet
        comparison_date (datetime): Timestamp when the comparison was performed
        scan_count (int): Total number of items in scan results
        smartsheet_count (int): Total number of items in Smartsheet
        match_count (int): Number of items with matching compliance IDs
    """
    matched_items: List[Dict[str, Any]] = Field(default_factory=list)
    unmatched_scan_items: List[ComplianceScanResult] = Field(default_factory=list)
    unmatched_smartsheet_items: List[ComplianceItem] = Field(default_factory=list)
    comparison_date: datetime = Field(default_factory=datetime.now)
    scan_count: int = 0
    smartsheet_count: int = 0
    match_count: int = 0