"""
RHEL compliance benchmark processor.

This module handles processing RHEL compliance scan results from
various formats including Nessus and CSV exports.
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional

from src.analyzer.processors.base import BaseComplianceProcessor
from src.analyzer.models import ComplianceScanResult
from src.cli.utils import ORANGE, RESET


class RhelComplianceProcessor(BaseComplianceProcessor):
    """Processor for RHEL compliance benchmarks."""
    
    @classmethod
    # Check file path name for processor type
    def can_process(cls, csv_path: str, dataframe: pd.DataFrame) -> bool:
        """Check if this processor can handle the file."""
        # Check for RHEL in file name
        print(f"trying pattern detection")
        pattern = r"(rhel[_]?\d*)*"
        if re.search(pattern, csv_path, re.IGNORECASE):
            print(f"{ORANGE}Detected RHEL file based on filename{RESET}")
            return True
            
        # Check for Nessus format with RHEL compliance IDs
        if "Unique ID" in dataframe.columns:
            print(f"{ORANGE}Found 'Unique ID' column, checking for RHEL content{RESET}")
            sample = dataframe["Unique ID"].dropna().head(20)
            for item in sample:
                if isinstance(item, str) and ("Compliance: RHEL-" in item or "RHEL-" in item):
                    print(f"{ORANGE}Found RHEL compliance ID in Unique ID column{RESET}")
                    return True
                
        # If we didn't find clear RHEL identifiers but it looks like a Nessus scan
        # and has 'Unique ID', 'Object', and other key columns, treat it as RHEL
        if "Object" in dataframe.columns and "Asset Identifier" in dataframe.columns:
            print(f"{ORANGE}File appears to be a Nessus compliance scan. Treating as RHEL.{RESET}")
            return True
        
        # # Check for RHEL IDs in description
        # if "Description" in dataframe.columns:
        #     sample = dataframe["Description"].dropna().head(10)
        #     for item in sample:
        #         if isinstance(item, str) and re.search(r'RHEL-\d{2}-\d{6}', item):
        #             return True

        # Check for RHEL IDs in description
        for desc_col in ['Description', 'Short Desc', 'Risk Statement']:
            if desc_col in dataframe.columns:
                sample = dataframe[desc_col].dropna().head(20)
                for item in sample:
                    if isinstance(item, str) and re.search(r'RHEL-\d{2}-\d{6}', item):
                        print(f"{ORANGE}Found RHEL reference in {desc_col} column{RESET}")
                        return True
        return False
    
    @classmethod
    def can_process_id(cls, compliance_id: str) -> bool:
        """Check if this processor can handle the given compliance ID."""
        return compliance_id.startswith("RHEL-") or compliance_id.startswith("Plugin-")
    
    @classmethod
    def process(cls, csv_path: str, dataframe: pd.DataFrame) -> List[ComplianceScanResult]:
        """Process RHEL compliance CSV files."""
        results = []
        
        # Special handling for Nessus compliance results format
        if "Unique ID" in dataframe.columns and dataframe["Unique ID"].str.contains("Compliance:", na=False).any():
            print(f"{ORANGE}Detected Nessus compliance scan format{RESET}")
            
            has_compliance_prefix = False
            for _, row in dataframe.iterrows():
                # Extract compliance ID from the "Unique ID" field (format: "Compliance: RHEL-08-040310 - ...")
                unique_id = row.get("Unique ID", "")
                if isinstance(unique_id, str) and "Compliance:" in unique_id:
                    has_compliance_prefix = True
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
                            for col in dataframe.columns:
                                if col not in ["Unique ID", "Object", "Scanner Severity", "Asset Identifier", "Short Desc", "Risk Statement"]:
                                    if not pd.isna(row.get(col)):
                                        result.additional_fields[col] = row.get(col)
                            
                            results.append(result)
                        except Exception as e:
                            print(f"{ORANGE}Error processing row with compliance ID {compliance_id}: {str(e)}{RESET}")
            
            print(f"{ORANGE}Extracted {len(results)} compliance items from Nessus format{RESET}")
            return results
            # If no "Compliance:" prefix was found, try to extract RHEL IDs from other fields
        if not has_compliance_prefix:
            print(f"{ORANGE}No 'Compliance:' prefix found. Looking for RHEL IDs in other fields{RESET}")
            
            # Look for RHEL IDs in Short Desc or other fields
            for _, row in dataframe.iterrows():
                compliance_id = None
                
                # Try to find RHEL ID in Short Desc
                short_desc = row.get("Short Desc", "")
                if isinstance(short_desc, str):
                    rhel_matches = re.findall(r'RHEL-\d{2}-\d{6}', short_desc)
                    if rhel_matches:
                        compliance_id = rhel_matches[0]
                
                # If no RHEL ID found, use Plugin ID or Unique ID as fallback
                if not compliance_id:
                    if "Plugin ID" in dataframe.columns and not pd.isna(row.get("Plugin ID")):
                        plugin_id = str(row.get("Plugin ID")).strip()
                        compliance_id = f"Plugin-{plugin_id}"
                    elif not pd.isna(row.get("Unique ID")):
                        unique_id = str(row.get("Unique ID")).strip()
                        compliance_id = f"ID-{unique_id}"
                    else:
                        # Skip rows without any usable ID
                        continue
                
                # Create the ComplianceScanResult
                try:
                    result = ComplianceScanResult(
                        compliance_id=compliance_id,
                        status=row.get("Object", "Unknown"),
                        severity=row.get("Scanner Severity"),
                        hostname=row.get("Asset Identifier"),
                        description=row.get("Short Desc"),
                        details=row.get("Risk Statement")
                    )
                    
                    # Add all other fields
                    for col in dataframe.columns:
                        if col not in ["Unique ID", "Object", "Scanner Severity", "Asset Identifier", "Short Desc", "Risk Statement"]:
                            if not pd.isna(row.get(col)):
                                result.additional_fields[col] = row.get(col)
                    
                    results.append(result)
                except Exception as e:
                    print(f"{ORANGE}Error processing row: {str(e)}{RESET}")
        
        if results:
            print(f"{ORANGE}Extracted {len(results)} compliance items from Nessus-like format{RESET}")
            return results
           
        # Standard CSV format
        # Identify columns
        compliance_id_col = None
        possible_id_cols = ['Compliance ID', 'Finding ID', 'STIG ID', 'Vulnerability ID', 'ID', 'Unique ID']
        
        for col in possible_id_cols:
            if col in dataframe.columns:
                compliance_id_col = col
                break
                
        # If no compliance ID column was found, try to extract from Description
        if not compliance_id_col and 'Description' in dataframe.columns:
            print(f"{ORANGE}No dedicated compliance ID column found. Attempting to extract IDs from Description column...{RESET}")
            
            # Regular expression to find RHEL IDs
            rhel_pattern = r'(RHEL-\d{2}-\d{6})'
            
            # For each row in the dataframe
            for _, row in dataframe.iterrows():
                description = str(row.get('Description', ''))
                matches = re.findall(rhel_pattern, description)
                
                # If we found compliance IDs in the description
                if matches:
                    for compliance_id in matches:
                        # Create a separate result for each compliance ID found
                        try:
                            status_col = next((col for col in dataframe.columns if 'status' in col.lower() or 'object' in col.lower()), None)
                            severity_col = next((col for col in dataframe.columns if any(s in col.lower() for s in ['severity', 'cat', 'category'])), None)
                            hostname_col = next((col for col in dataframe.columns if any(h in col.lower() for h in ['host', 'asset', 'hostname'])), None)
                            
                            result = ComplianceScanResult(
                                compliance_id=compliance_id,
                                status=str(row.get(status_col)).strip() if status_col and not pd.isna(row[status_col]) else "Unknown",
                                severity=row.get(severity_col) if severity_col and not pd.isna(row[severity_col]) else None,
                                hostname=str(row.get(hostname_col)).strip() if hostname_col and not pd.isna(row[hostname_col]) else None,
                                description=description
                            )
                            
                            # Add other fields
                            for col in dataframe.columns:
                                if col not in ['Description', status_col, severity_col, hostname_col]:
                                    if col in row and not pd.isna(row.get(col)):
                                        result.additional_fields[col] = row.get(col)
                            
                            # Add the Plugin ID as an additional field for reference
                            if 'Plugin ID' in dataframe.columns:
                                result.additional_fields['Plugin ID'] = row.get('Plugin ID')
                                
                            results.append(result)
                        except Exception as e:
                            print(f"{ORANGE}Error processing compliance ID {compliance_id}: {str(e)}{RESET}")
            
            if results:
                print(f"{ORANGE}Extracted {len(results)} compliance items from Description field{RESET}")
                return results
            
        # If we have a compliance ID column, process normally
        if compliance_id_col:
            status_col = next((col for col in dataframe.columns if 'status' in col.lower() or 'object' in col.lower()), None)
            severity_col = next((col for col in dataframe.columns if any(s in col.lower() for s in ['severity', 'cat', 'category'])), None)
            hostname_col = next((col for col in dataframe.columns if any(h in col.lower() for h in ['host', 'asset', 'hostname'])), None)
            description_col = next((col for col in dataframe.columns if any(d in col.lower() for d in ['desc', 'finding', 'title'])), None)
            
            for _, row in dataframe.iterrows():
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
                    for col in dataframe.columns:
                        if col not in [compliance_id_col, status_col, severity_col, hostname_col, description_col]:
                            if not pd.isna(row[col]):
                                result.additional_fields[col] = row[col]
                    
                    results.append(result)
                except Exception as e:
                    print(f"{ORANGE}Error processing row: {str(e)}{RESET}")
            
            print(f"{ORANGE}Extracted {len(results)} compliance items from CSV format{RESET}")
            return results
        
        # If still no results, try Plugin ID as backup
        if not results and 'Plugin ID' in dataframe.columns:
            print(f"{ORANGE}Using 'Plugin ID' as backup compliance ID column{RESET}")
            
            status_col = next((col for col in dataframe.columns if 'status' in col.lower() or 'object' in col.lower()), None)
            severity_col = next((col for col in dataframe.columns if any(s in col.lower() for s in ['severity', 'cat', 'category'])), None)
            hostname_col = next((col for col in dataframe.columns if any(h in col.lower() for h in ['host', 'asset', 'hostname'])), None)
            
            for _, row in dataframe.iterrows():
                # Skip rows with empty Plugin ID
                if pd.isna(row['Plugin ID']) or not row['Plugin ID']:
                    continue
                
                # Create a result object with Plugin ID as compliance ID
                try:
                    plugin_id = str(row['Plugin ID']).strip()
                    result = ComplianceScanResult(
                        compliance_id=f"Plugin-{plugin_id}",  # Prefix to distinguish from real compliance IDs
                        status=str(row[status_col]).strip() if status_col and not pd.isna(row[status_col]) else "Unknown",
                        severity=row[severity_col] if severity_col and not pd.isna(row[severity_col]) else None,
                        hostname=str(row[hostname_col]).strip() if hostname_col and not pd.isna(row[hostname_col]) else None,
                        description=str(row['Description']).strip() if 'Description' in dataframe.columns and not pd.isna(row['Description']) else None,
                    )
                    
                    # Add all other columns as additional fields
                    for col in dataframe.columns:
                        if col not in ['Plugin ID', status_col, severity_col, hostname_col, 'Description']:
                            if not pd.isna(row[col]):
                                result.additional_fields[col] = row[col]
                    
                    results.append(result)
                except Exception as e:
                    print(f"{ORANGE}Error processing row: {str(e)}{RESET}")
            
            print(f"{ORANGE}Extracted {len(results)} compliance items using Plugin IDs{RESET}")
            
        return results
    
    @classmethod
    def get_benchmark_info(cls, compliance_id: str) -> Dict[str, str]:
        """Get additional info about RHEL benchmark items."""
        # Extract RHEL version and control category from ID
        if compliance_id.startswith("RHEL-"):
            parts = compliance_id.split("-")
            if len(parts) >= 2:
                rhel_version = parts[1]
                return {
                    "os_version": f"RHEL {rhel_version}",
                    "benchmark_type": "STIG",
                }
        
        return {}
    
    @classmethod
    def needs_review(cls, item: ComplianceScanResult) -> bool:
        """Check if a RHEL compliance item needs review."""
        if not item.status:
            return False
            
        # Convert to string in case it's not already
        status_str = str(item.status)
        
        # RHEL-specific checks
        if "[PASSED]" in status_str or "[PASS]" in status_str:
            return False
        
        if "[FAILED]" in status_str or "[WARNING]" in status_str:
            return True
            
        # For any other status, check for fail/warning keywords
        status_lower = status_str.lower()
        if any(keyword in status_lower for keyword in ['fail', 'failed', 'warning', 'warn']):
            return True
            
        # Default to false for RHEL items with unknown status
        return False