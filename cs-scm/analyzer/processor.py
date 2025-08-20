"""
Smartsheet Compliance Analyzer - Data Processing Module

This module provides comprehensive functionality for processing and analyzing 
compliance data from multiple sources, including:
- Extracting client-specific control values
- Loading and parsing compliance scan results
- Extracting and processing compliance items from Smartsheet
- Comparing scan results with Smartsheet compliance data

Key Features:
- Dynamic placeholder replacement in compliance rationales
- Flexible CSV parsing for various scanner formats
- Detailed matching and comparison of compliance items
- Comprehensive status analysis and categorization

Workflow:
1. Extract client-specific control placeholders
2. Load and parse compliance scan results
3. Extract compliance items from Smartsheet
4. Replace placeholders in compliance rationales
5. Compare scan results with Smartsheet data
6. Generate a comprehensive comparison report

Dependencies:
- pandas for CSV parsing
- re for text manipulation
- src.cli.utils for colored console output
- src.analyzer.models for data models
"""

import re
import pandas as pd
from typing import Dict, List, Any, Set, Optional, Tuple
from datetime import datetime

from src.cli.utils import ORANGE, RESET
from src.analyzer.models import (
    ControlValue, ClientControls, ComplianceItem,
    ComplianceScanResult, ComparisonResult
)

def extract_client_controls(control_sheet_data: Dict[str, Any], selected_client: str) -> ClientControls:
    """
    Extract client-specific control values from Smartsheet Compensating Controls sheet.
    
    This function:
    - Identifies the CLIENT column in the control sheet
    - Filters rows for the specified client
    - Extracts placeholder values unique to the client
    - Stores multiple versions of each placeholder for flexible matching
    
    Args:
        control_sheet_data: Raw Smartsheet data for the Compensating Controls sheet
        selected_client: Name of the client to extract controls for
    
    Returns:
        ClientControls object containing client-specific placeholder mappings
    """
    # Create the container for our client's controls
    client_controls = ClientControls(client=selected_client)
    
    # Find the column IDs we need
    client_col_id = None
    
    # Map of column titles to their IDs
    column_map = {}
    
    # Identify CLIENT column and create column mapping
    for column in control_sheet_data.get('columns', []):
        column_map[column['title']] = column['id']
        if column['title'] == 'CLIENT':
            client_col_id = column['id']
    
    if not client_col_id:
        print(f"{ORANGE}Could not find CLIENT column in control sheet.{RESET}")
        return client_controls
        
    # Process each row that matches our client
    for row in control_sheet_data.get('rows', []):
        # Check if this row is for our client
        client_value = None
        
        # First find the client value
        for cell in row.get('cells', []):
            if cell.get('column_id') == client_col_id:
                client_value = cell.get('value')
                break
                
        # Skip if not our client
        if client_value != selected_client:
            continue
        
        # Now extract all the placeholder values
        for cell in row.get('cells', []):
            col_id = cell.get('column_id')
            
            # Skip the CLIENT column
            if col_id == client_col_id:
                continue
            
            # Find the column title for this cell
            col_title = None
            for title, id in column_map.items():
                if id == col_id:
                    col_title = title
                    break
            
            # Only process if we have both a title and a value
            if col_title and (cell.get('value') is not None):
                value = cell.get('display_value') or str(cell.get('value', ''))
                
                # Generate all possible placeholder variants based on the column title
                variants = set()
                
                # Original column title (exact as in Smartsheet)
                orig_title = col_title
                
                # 1. Lowercase version of original title (preserving spaces/underscores)
                variants.add(orig_title.lower())
                
                # 2. Lowercase with spaces (if title has underscores)
                if '_' in orig_title:
                    with_spaces = orig_title.lower().replace('_', ' ')
                    variants.add(with_spaces)
                
                # 3. Lowercase with underscores (if title has spaces)
                if ' ' in orig_title:
                    with_underscores = orig_title.lower().replace(' ', '_')
                    variants.add(with_underscores)
                
                # 4. Lowercase with no spaces or underscores
                no_spaces = orig_title.lower().replace(' ', '').replace('_', '')
                variants.add(no_spaces)
                
                # Forced variants for common patterns
                if "cloud_provider" in variants:
                    variants.add("cloud provider")
                if "cloud provider" in variants:
                    variants.add("cloud_provider")
                
                # Add all unique variants to our controls
                for variant in variants:
                    client_controls.controls.append(
                        ControlValue(
                            placeholder=variant,
                            value=value
                        )
                    )

    return client_controls


def extract_compliance_items(compliance_sheet_data: Dict[str, Any], client_controls: ClientControls) -> List[ComplianceItem]:
    """
    Extracts compliance items from Smartsheet, including "Additional Context",
    and replaces placeholders with client-specific values.
    """
    placeholder_mapping = client_controls.to_dict()
    compliance_items = []
    column_ids = {}
    
    # Map all required column names to our data model fields
    for column in compliance_sheet_data.get('columns', []):
        column_title = column['title'].lower().strip()
        if 'compliance id' in column_title:
            column_ids['compliance_id'] = column['id']
        elif 'finding description' in column_title:
            column_ids['finding_description'] = column['id']
        elif 'srg solution' in column_title:
            column_ids['srg_solution'] = column['id']
        elif 'deviation type' in column_title:
            column_ids['deviation_type'] = column['id']
        elif 'deviation rationale' in column_title and 'status' not in column_title:
            column_ids['deviation_rationale'] = column['id']
        elif 'supporting documents' in column_title:
            column_ids['supporting_documents'] = column['id']
        elif 'deviation rationale status' in column_title:
            column_ids['deviation_status'] = column['id']
        elif 'should fix' in column_title:
            column_ids['should_fix'] = column['id']
        elif 'comments' in column_title:
            column_ids['comments'] = column['id']
        elif 'additional context' in column_title:
            column_ids['additional_context'] = column['id']

    def normalize_boolean(value):
        if value is None: return None
        if isinstance(value, bool): return value
        str_value = str(value).strip().lower()
        if str_value in ['true', 'yes', 'y', '1', 'checked', 'x', 'on', 't']: return True
        if str_value in ['false', 'no', 'n', '0', 'unchecked', '', 'off', 'f']: return False
        return None

    # Process each row
    for row in compliance_sheet_data.get('rows', []):
        item_data = {}
        
        # Create a mapping of columnId -> cell value for the current row for easier access
        row_values_by_col_id = {cell.get('column_id'): cell.get('value') for cell in row.get('cells', [])}

        # Populate item_data using the mapped column IDs
        for field_name, col_id in column_ids.items():
            cell_value = row_values_by_col_id.get(col_id)
            
            if field_name == 'should_fix':
                item_data[field_name] = normalize_boolean(cell_value)
            elif field_name == 'deviation_rationale':
                original_text = cell_value or ''
                updated_text = original_text
                # Replace placeholders
                for placeholder, value in placeholder_mapping.items():
                    pattern = f'\\[{re.escape(placeholder)}\\]'
                    updated_text = re.sub(pattern, value, updated_text, flags=re.IGNORECASE)
                item_data[field_name] = updated_text
            else:
                # For all other fields, including 'additional_context', just get the value
                item_data[field_name] = cell_value

        # Only create a compliance item if it has a compliance ID
        if item_data.get('compliance_id') is not None:
            try:
                item_data['compliance_id'] = str(item_data['compliance_id'])
                compliance_items.append(ComplianceItem(**item_data))
            except Exception as e:
                print(f"{ORANGE}Error creating ComplianceItem with ID '{item_data.get('compliance_id')}': {str(e)}{RESET}")

    print(f"{ORANGE}Extracted {len(compliance_items)} compliance items from Smartsheet{RESET}")
    
    return compliance_items

def compare_results(scan_results: List[ComplianceScanResult], smartsheet_results: List[ComplianceItem]) -> ComparisonResult:
    """
    Compares scan results against Smartsheet results, ensuring all necessary
    fields, including the SRG Solution from the POAM, are passed for reporting.
    """
    result = ComparisonResult(
        scan_count=len(scan_results),
        smartsheet_count=len(smartsheet_results)
    )

    scan_ids = {str(item.compliance_id).strip() for item in scan_results if item.compliance_id}
    smartsheet_ids = {str(item.compliance_id).strip() for item in smartsheet_results if item.compliance_id}
    
    matching_ids = scan_ids.intersection(smartsheet_ids)
    result.match_count = len(matching_ids)
    print(f"{ORANGE}Found {result.match_count} matching compliance IDs{RESET}")

    for comp_id in matching_ids:
        scan_item = next((item for item in scan_results if str(item.compliance_id).strip() == comp_id), None)
        smartsheet_item = next((item for item in smartsheet_results if str(item.compliance_id).strip() == comp_id), None)

        if scan_item and smartsheet_item:
            combined_item = smartsheet_item.dict()
            
            combined_item.update({
                'Status': scan_item.status,
                'Severity': scan_item.severity,
                'Hostname': scan_item.hostname,
                'POAM ID': scan_item.poam_id,
                'Finding Description': smartsheet_item.finding_description or scan_item.description,
                # Use the SRG Solution from the POAM scan data
                'srg_solution': scan_item.srg_solution
            })
            result.matched_items.append(combined_item)
    
    result.unmatched_scan_items = [item for item in scan_results if str(item.compliance_id).strip() not in matching_ids]
    result.unmatched_smartsheet_items = [item for item in smartsheet_results if str(item.compliance_id).strip() not in matching_ids]
    
    return result


def process_compliance_data(
    control_sheet_data: Dict[str, Any],
    compliance_sheet_data: Dict[str, Any],
    selected_client: str,
    scan_results: List[ComplianceScanResult]
) -> ComparisonResult:
    """
    Process all compliance data and generate comparison results.
    
    Args:
        control_sheet_data: Data from the Compensating Controls sheet
        compliance_sheet_data: Data from the Compliance ClearingHouse sheet
        selected_client: The client selected by the user
        scan_results: List of scan results from CSV
        
    Returns:
        ComparisonResult with all matched and unmatched items
    """
    # 1. Extract client controls
    client_controls = extract_client_controls(control_sheet_data, selected_client)
    
    # 2. Extract compliance items with replaced placeholders
    compliance_items = extract_compliance_items(compliance_sheet_data, client_controls)
    
    # 3. Compare with scan results
    comparison = compare_results(scan_results, compliance_items)
    
    return comparison
