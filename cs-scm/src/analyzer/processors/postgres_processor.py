"""
PostgreSQL compliance benchmark processor.

This module handles processing PostgreSQL compliance scan results from
various formats including Nessus and CSV exports.
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional

from src.analyzer.processors.base import BaseComplianceProcessor
from src.analyzer.models import ComplianceScanResult
from src.cli.utils import ORANGE, RESET


class PostgresComplianceProcessor(BaseComplianceProcessor):
    """Processor for PostgreSQL compliance benchmarks."""
    
    @classmethod
    def can_process(cls, csv_path: str, dataframe: pd.DataFrame) -> bool:
        """Check if this processor can handle the file."""
        # Check for PostgreSQL in file name
        pattern = r"postgres|postgresql|pg[_-]?\d+"
        if re.search(pattern, csv_path, re.IGNORECASE):
            print(f"{ORANGE}Detected PostgreSQL file based on filename{RESET}")
            return True
        
        # Check for PostgreSQL IDs in the data
        for id_col in ['Compliance ID', 'Finding ID', 'STIG ID', 'Vulnerability ID', 'ID', 'Unique ID']:
            if id_col in dataframe.columns:
                sample = dataframe[id_col].dropna().head(20)
                for item in sample:
                    if isinstance(item, str) and re.search(r'PG[_-]?\d+|PostgreSQL', item, re.IGNORECASE):
                        print(f"{ORANGE}Found PostgreSQL compliance ID in {id_col} column{RESET}")
                        return True
        
        # Check content in description or other columns for PostgreSQL-specific terms
        for desc_col in ['Description', 'Short Desc', 'Risk Statement']:
            if desc_col in dataframe.columns:
                sample = dataframe[desc_col].dropna().head(20)
                for item in sample:
                    if isinstance(item, str) and re.search(r'PostgreSQL|Postgres\s+\d+', item, re.IGNORECASE):
                        print(f"{ORANGE}Found PostgreSQL reference in {desc_col} column{RESET}")
                        return True
        
        return False
    
    @classmethod
    def can_process_id(cls, compliance_id: str) -> bool:
        """Check if this processor can handle the given compliance ID."""
        return compliance_id.startswith("PG-") or \
               re.match(r"PostgreSQL-\d+", compliance_id) or \
               compliance_id.startswith("CCI-")  # Common Controls Identifier related to PostgreSQL
    
    @classmethod
    def process(cls, csv_path: str, dataframe: pd.DataFrame) -> List[ComplianceScanResult]:
        """Process PostgreSQL compliance CSV files."""
        results = []
        print(f"{ORANGE}Processing PostgreSQL compliance scan{RESET}")
        
        # Similar to RHEL processor but with PostgreSQL-specific patterns
        # Try to identify the compliance ID column
        compliance_id_col = None
        for col in ['Compliance ID', 'Finding ID', 'STIG ID', 'Vulnerability ID', 'ID', 'Unique ID']:
            if col in dataframe.columns:
                compliance_id_col = col
                break
        
        # If we found a compliance ID column
        if compliance_id_col:
            status_col = next((col for col in dataframe.columns if 'status' in col.lower() or 'object' in col.lower()), None)
            severity_col = next((col for col in dataframe.columns if any(s in col.lower() for s in ['severity', 'cat', 'category'])), None)
            hostname_col = next((col for col in dataframe.columns if any(h in col.lower() for h in ['host', 'asset', 'hostname'])), None)
            description_col = next((col for col in dataframe.columns if any(d in col.lower() for d in ['desc', 'finding', 'title'])), None)
            
            for _, row in dataframe.iterrows():
                # Skip rows with empty compliance ID
                if pd.isna(row[compliance_id_col]) or not row[compliance_id_col]:
                    continue
                
                compliance_id = str(row[compliance_id_col]).strip()
                
                # Normalize PostgreSQL IDs (convert variations to a standard format)
                # e.g., "PostgreSQL 9.5-1.1.2" -> "PG-9.5-1.1.2"
                if re.match(r'PostgreSQL\s+\d+', compliance_id, re.IGNORECASE):
                    compliance_id = re.sub(r'PostgreSQL\s+', 'PG-', compliance_id, flags=re.IGNORECASE)
                
                # Create a result object
                try:
                    result = ComplianceScanResult(
                        compliance_id=compliance_id,
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
        
        # If no compliance ID column was found, try to extract from Description
        elif 'Description' in dataframe.columns:
            print(f"{ORANGE}No dedicated compliance ID column found. Attempting to extract IDs from Description column...{RESET}")
            
            # Regular expression to find PostgreSQL IDs
            pg_pattern = r'(PG-\d+[\.\d-]*|\bPostgreSQL\s+\d+[\.\d-]*\b)'
            
            # For each row in the dataframe
            for _, row in dataframe.iterrows():
                description = str(row.get('Description', ''))
                matches = re.findall(pg_pattern, description)
                
                # If we found compliance IDs in the description
                if matches:
                    for match in matches:
                        # Normalize the ID
                        compliance_id = match
                        if re.match(r'PostgreSQL\s+\d+', compliance_id, re.IGNORECASE):
                            compliance_id = re.sub(r'PostgreSQL\s+', 'PG-', compliance_id, flags=re.IGNORECASE)
                        
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
                            
                            results.append(result)
                        except Exception as e:
                            print(f"{ORANGE}Error processing compliance ID {compliance_id}: {str(e)}{RESET}")
        
        # If no results found yet, try using Plugin ID as a fallback
        if not results and 'Plugin ID' in dataframe.columns:
            print(f"{ORANGE}Using 'Plugin ID' as backup compliance ID column{RESET}")
            
            status_col = next((col for col in dataframe.columns if 'status' in col.lower() or 'object' in col.lower()), None)
            severity_col = next((col for col in dataframe.columns if any(s in col.lower() for s in ['severity', 'cat', 'category'])), None)
            hostname_col = next((col for col in dataframe.columns if any(h in col.lower() for h in ['host', 'asset', 'hostname'])), None)
            
            for _, row in dataframe.iterrows():
                # Skip rows with empty Plugin ID
                if pd.isna(row['Plugin ID']) or not row['Plugin ID']:
                    continue
                
                # Check if this is a PostgreSQL-related plugin by looking at the description
                if 'Description' in dataframe.columns and not pd.isna(row['Description']):
                    description = str(row['Description'])
                    if not re.search(r'PostgreSQL|Postgres', description, re.IGNORECASE):
                        continue  # Skip non-PostgreSQL plugins
                
                # Create a result object with Plugin ID as compliance ID
                try:
                    plugin_id = str(row['Plugin ID']).strip()
                    result = ComplianceScanResult(
                        compliance_id=f"PG-Plugin-{plugin_id}",  # Prefix to distinguish from real compliance IDs
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
        
        print(f"{ORANGE}Extracted {len(results)} PostgreSQL compliance items{RESET}")
        return results
    
    @classmethod
    def get_benchmark_info(cls, compliance_id: str) -> Dict[str, str]:
        """Get additional info about PostgreSQL benchmark items."""
        # Extract PostgreSQL version and control number from ID if possible
        if compliance_id.startswith("PG-"):
            parts = compliance_id.split("-")
            if len(parts) >= 2:
                # Try to extract version number
                version_match = re.search(r'(\d+\.\d+)', parts[1])
                version = version_match.group(1) if version_match else "Unknown"
                return {
                    "db_version": f"PostgreSQL {version}",
                    "benchmark_type": "STIG" if len(parts) > 2 else "CIS",
                }
        
        return {"benchmark_type": "PostgreSQL Compliance"}
    
    @classmethod
    def needs_review(cls, item: ComplianceScanResult) -> bool:
        """Check if a PostgreSQL compliance item needs review."""
        if not item.status:
            return False
            
        # Convert to string in case it's not already
        status_str = str(item.status)
        
        # PostgreSQL-specific checks for pass/fail status
        status_lower = status_str.lower()
        
        # Check for explicit pass indicators
        if any(keyword in status_lower for keyword in ['pass', 'compliant', 'satisfied']):
            return False
            
        # Check for explicit fail indicators
        if any(keyword in status_lower for keyword in ['fail', 'non-compliant', 'not satisfied', 'warning']):
            return True
            
        # Default to true for PostgreSQL items with unknown or ambiguous status
        # This is more cautious than the RHEL approach, ensuring items are reviewed if we're unsure
        return True