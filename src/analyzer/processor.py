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
    Extract compliance items from Smartsheet and replace placeholders with client-specific values.
    
    This function:
    - Dynamically maps Smartsheet columns to ComplianceItem fields
    - Replaces placeholders in deviation rationales
    - Tracks which placeholders were replaced
    - Preserves original rationale text
    - Normalizes should_fix values to proper boolean types
    
    Args:
        compliance_sheet_data: Raw Smartsheet data for the Compliance ClearingHouse sheet
        client_controls: ClientControls object with placeholder mappings
    
    Returns:
        List of ComplianceItem objects with replaced placeholders
    """
    # Create placeholder mapping dict for easier lookup
    placeholder_mapping = client_controls.to_dict()
    
    # List to hold our compliance items
    compliance_items = []
    
    # Find the column IDs for columns we need
    column_ids = {}
    
    # Map common column names to our data model fields
    for column in compliance_sheet_data.get('columns', []):
        column_title = column['title'].lower()
        if 'compliance id' in column_title or 'complianceid' in column_title:
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
        elif 'deviation rationale status' in column_title or ('status' in column_title and 'deviation' in column_title):
            column_ids['deviation_status'] = column['id']
        elif 'should fix' in column_title:
            column_ids['should_fix'] = column['id']
        elif 'comments' in column_title:
            column_ids['comments'] = column['id']
    
    # Helper function to normalize boolean values
    def normalize_boolean(value):
        """Convert various representations of boolean values to Python boolean."""
        if value is None:
            return None
            
        # If it's already a boolean, return it
        if isinstance(value, bool):
            return value
            
        # Convert to string and normalize
        str_value = str(value).strip().lower()
        
        # Check for various "true" values
        true_values = ['true', 'yes', 'y', '1', 'checked', 'x', 'on', 't']
        false_values = ['false', 'no', 'n', '0', 'unchecked', '', 'off', 'f']
        
        if str_value in true_values:
            return True
        elif str_value in false_values:
            return False
        else:
            return None
    
    # Process each row and replace placeholders
    for row in compliance_sheet_data.get('rows', []):
        # Create a new compliance item for this row
        item_data = {}
        replaced_placeholders = set()
        original_rationale = None
        
        # Extract compliance ID first for better reference
        compliance_id = None
        for cell in row.get('cells', []):
            if cell.get('column_id') == column_ids.get('compliance_id'):
                compliance_id = cell.get('value')
                break
        
        # Extract all the field values
        for cell in row.get('cells', []):
            col_id = cell.get('column_id')
            
            # Go through our mapped column IDs and set the appropriate fields
            for field_name, field_col_id in column_ids.items():
                if col_id == field_col_id:
                    # For the deviation rationale, we'll store both original and updated versions
                    if field_name == 'deviation_rationale':
                        original_text = cell.get('value') or ''
                        original_rationale = original_text
                        
                        # Skip empty rationales
                        if not original_text.strip():
                            item_data[field_name] = original_text
                            break
                        
                        # Replace placeholders in the text
                        updated_text = original_text
                        for placeholder, value in placeholder_mapping.items():
                            # Match [placeholder] pattern
                            pattern = f'\\[{re.escape(placeholder)}\\]'
                            new_text = re.sub(pattern, value, updated_text, flags=re.IGNORECASE)
                            if new_text != updated_text:
                                # If we made a replacement, record which placeholder was used
                                replaced_placeholders.add(placeholder)
                            updated_text = new_text
                        
                        # Special handling for RHEL-08-010030 and cloud provider placeholder
                        if compliance_id == 'RHEL-08-010030' and '[cloud provider]' in updated_text:
                            cloud_provider_value = None
                            # Look for the 'cloud_provider' value in our mapping
                            for placeholder, value in placeholder_mapping.items():
                                if placeholder.lower() in ['cloud_provider', 'cloud provider', 'cloudprovider']:
                                    cloud_provider_value = value
                                    break
                            
                            if cloud_provider_value:
                                # Do a direct replacement
                                updated_text = updated_text.replace('[cloud provider]', cloud_provider_value)
                        
                        # Set the updated text
                        item_data[field_name] = updated_text
                    elif field_name == 'should_fix':
                        # Special handling for should_fix to normalize the value
                        raw_value = cell.get('value')
                        normalized_value = normalize_boolean(raw_value)
                        item_data[field_name] = normalized_value
                    else:
                        # For other fields, just set the value
                        item_data[field_name] = cell.get('value')
                    break
        
        # Only create items that have a compliance ID
        if 'compliance_id' in item_data and item_data['compliance_id']:
            # Add the metadata
            item_data['replaced_placeholders'] = replaced_placeholders
            item_data['original_rationale'] = original_rationale
            
            # Create and add the ComplianceItem
            compliance_items.append(ComplianceItem(**item_data))
    
    print(f"{ORANGE}Extracted {len(compliance_items)} compliance items from Smartsheet{RESET}")
    
    # Check for any unreplaced placeholders
    unreplaced_items = []
    for item in compliance_items:
        if item.deviation_rationale and re.search(r'\[.*?\]', item.deviation_rationale):
            placeholders = [p for p in re.findall(r'\[(.*?)\]', item.deviation_rationale) if p.strip()]
            if placeholders:  # Only include non-empty placeholders
                unreplaced_items.append((item.compliance_id, placeholders))
    
    if unreplaced_items:
        print(f"{ORANGE}WARNING: Found {len(unreplaced_items)} items with unreplaced placeholders{RESET}")
    
    return compliance_items


def load_scan_results(csv_path: str) -> List[ComplianceScanResult]:
    """
    Load and parse compliance scan results from a CSV file.
    
    This function supports multiple scanner formats, with special handling for:
    - Nessus compliance scan results
    - Various CSV structures with different column names
    
    Key capabilities:
    - Dynamically identify compliance ID column
    - Extract additional metadata into additional_fields
    - Handle different CSV structures and column variations
    
    Args:
        csv_path: Path to the CSV file containing scan results
    
    Returns:
        List of ComplianceScanResult objects representing scan findings
    
    Raises:
        Exception if there are critical errors in reading or parsing the CSV
    """
    try:
        print(f"{ORANGE}Analyzing CSV file structure...{RESET}")
        df = pd.read_csv(csv_path, skipinitialspace=True)
        
        # Special handling for Nessus compliance results format
        if "Unique ID" in df.columns and df["Unique ID"].str.contains("Compliance:", na=False).any():
            print(f"{ORANGE}Detected Nessus compliance scan format{RESET}")
            
            # Extract results
            results = []
            for _, row in df.iterrows():
                # Extract compliance ID from the "Unique ID" field (format: "Compliance: RHEL-08-040310 - ...")
                unique_id = row.get("Unique ID", "")
                if isinstance(unique_id, str) and "Compliance:" in unique_id:
                    # Extract the compliance ID (e.g., "RHEL-08-040310")
                    matches = re.search(r'Compliance:\s+([A-Z0-9-]+)', unique_id)
                    if matches:
                        compliance_id = matches.group(1)
                        
                        # Get severity - could be string or int
                        severity = row.get("Scanner Severity")
                        
                        # Create a result object
                        try:
                            result = ComplianceScanResult(
                                compliance_id=compliance_id,
                                status=row.get("Object", "Unknown"),
                                severity=severity,
                                hostname=row.get("Asset Identifier"),
                                description=row.get("Short Desc"),
                                details=row.get("Risk Statement")
                            )
                            
                            # Add other fields
                            for col in df.columns:
                                if col not in ["Unique ID", "Object", "Scanner Severity", "Asset Identifier", "Short Desc", "Risk Statement"]:
                                    if not pd.isna(row.get(col)):
                                        result.additional_fields[col] = row.get(col)
                            
                            results.append(result)
                        except Exception as e:
                            print(f"{ORANGE}Error processing row with compliance ID {compliance_id}: {str(e)}{RESET}")
            
            print(f"{ORANGE}Extracted {len(results)} compliance items from Nessus format{RESET}")
            return results
        
        # If not Nessus format, try to identify the compliance ID column
        compliance_id_col = None
        possible_id_cols = ['Compliance ID', 'Finding ID', 'STIG ID', 'Vulnerability ID', 'ID', 'Unique ID']
        
        for col in possible_id_cols:
            if col in df.columns:
                compliance_id_col = col
                break
        
        if not compliance_id_col:
            print(f"{ORANGE}Could not identify compliance ID column in CSV file.{RESET}")
            print(f"{ORANGE}Available columns: {', '.join(df.columns)}{RESET}")
            return []
        
        # Identify other key columns
        status_col = next((col for col in df.columns if 'status' in col.lower() or 'object' in col.lower()), None)
        severity_col = next((col for col in df.columns if any(s in col.lower() for s in ['severity', 'cat', 'category'])), None)
        hostname_col = next((col for col in df.columns if any(h in col.lower() for h in ['host', 'asset', 'hostname'])), None)
        description_col = next((col for col in df.columns if any(d in col.lower() for d in ['desc', 'finding', 'title'])), None)
        
        # Parse results
        results = []
        for _, row in df.iterrows():
            # Skip rows with empty compliance ID
            if pd.isna(row[compliance_id_col]) or not row[compliance_id_col]:
                continue
            
            # Create a result object
            try:
                result = ComplianceScanResult(
                    compliance_id=str(row[compliance_id_col]).strip(),
                    status=str(row[status_col]).strip() if status_col and not pd.isna(row[status_col]) else "Unknown",
                    severity=row[severity_col] if severity_col and not pd.isna(row[severity_col]) else None,
                    hostname=str(row[hostname_col]).strip() if hostname_col and not pd.isna(row[hostname_col]) else None,
                    description=str(row[description_col]).strip() if description_col and not pd.isna(row[description_col]) else None,
                )
                
                # Add all other columns as additional fields
                for col in df.columns:
                    if col not in [compliance_id_col, status_col, severity_col, hostname_col, description_col]:
                        if not pd.isna(row[col]):
                            result.additional_fields[col] = row[col]
                
                results.append(result)
            except Exception as e:
                print(f"{ORANGE}Error processing row: {str(e)}{RESET}")
        
        print(f"{ORANGE}Extracted {len(results)} compliance items from CSV format{RESET}")
        return results
    
    except Exception as e:
        print(f"{ORANGE}Error reading CSV file: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return []


def compare_results(scan_results: List[ComplianceScanResult], smartsheet_results: List[ComplianceItem]) -> ComparisonResult:
    """
    Compare scan results against Smartsheet results.
    
    Args:
        scan_results: List of scan results
        smartsheet_results: List of ComplianceItem objects
        
    Returns:
        ComparisonResult object
    """

    # Initialize result
    result = ComparisonResult(
        scan_count=len(scan_results),
        smartsheet_count=len(smartsheet_results)
    )

    # Create sets of compliance IDs for quick lookup
    scan_ids = {item.compliance_id for item in scan_results}
    smartsheet_ids = {item.compliance_id for item in smartsheet_results if item.compliance_id}
    
    # Find matching and non-matching items
    matching_ids = scan_ids.intersection(smartsheet_ids)
    result.match_count = len(matching_ids)
    print(f"{ORANGE}Found {result.match_count} matching compliance IDs{RESET}")
    
    # Detailed function for status analysis
    def analyze_status(status):
        """Analyze and categorize status."""
        if not status:
            return "No Status", False
        
        status_str = str(status).lower()
        
        # Comprehensive approval status detection
        approval_indicators = [
            'approved', 'a', 'accept', 'acceptable', 
            'compliant', 'comp', 'pass', 'passed'
        ]
        
        is_approved = any(indicator in status_str for indicator in approval_indicators)
        
        return status_str, is_approved
    
    # Process matched items
    for comp_id in matching_ids:
        scan_item = next(item for item in scan_results if item.compliance_id == comp_id)
        smartsheet_item = next(item for item in smartsheet_results if item.compliance_id == comp_id)

        # Get full status details
        deviation_status = smartsheet_item.deviation_status
        analyzed_status, is_approved = analyze_status(deviation_status)
        
        # Get should_fix status as a proper boolean
        should_fix_value = smartsheet_item.should_fix

        # Combine the data
        combined_item = {
            'Compliance ID': comp_id,
            'Status': scan_item.status,
            'Severity': scan_item.severity,
            'Hostname': scan_item.hostname,
            'Finding Description': smartsheet_item.finding_description or scan_item.description,
            'SRG Solution': smartsheet_item.srg_solution,
            'Deviation Type': smartsheet_item.deviation_type,
            'Deviation Rationale': smartsheet_item.deviation_rationale,
            'Supporting Documents': smartsheet_item.supporting_documents,
            # Comprehensive status information
            'Deviation Status': deviation_status,
            'Analyzed Status': analyzed_status,
            'Is Approved': is_approved,
            # Use the normalized should_fix value
            'Should Fix': should_fix_value
        }

        result.matched_items.append(combined_item)
    
    # Process unmatched scan items
    result.unmatched_scan_items = [item for item in scan_results if item.compliance_id not in matching_ids]
    
    # Process unmatched Smartsheet items
    result.unmatched_smartsheet_items = [
        item for item in smartsheet_results 
        if item.compliance_id and item.compliance_id not in matching_ids
    ]
    
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