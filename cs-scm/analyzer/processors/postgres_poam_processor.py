import re
from typing import List, Optional, Any
from .base_poam_processor import BasePoamProcessor
from src.analyzer.models import ComplianceScanResult

class PostgresPoamProcessor(BasePoamProcessor):
    """Processes PostgreSQL compliance findings from a POAM row."""

    _psql_id_pattern = re.compile(r'^(\d+(\.\d+)+)')
    _managed_db_domains = ['.sql.goog', 'rds.amazonaws.com', '.database.azure.com']

    @staticmethod
    def can_process(row: List[Any]) -> bool:
        """
        Checks for a PostgreSQL compliance ID and a managed database asset.
        """
        if len(row) > 6 and isinstance(row[2], str) and isinstance(row[6], str):
            weakness_name = row[2]
            asset_identifier = row[6]
            
            has_psql_id = bool(PostgresPoamProcessor._psql_id_pattern.search(weakness_name))
            is_managed_db = any(domain in asset_identifier for domain in PostgresPoamProcessor._managed_db_domains)
            
            return has_psql_id and is_managed_db
        return False
    
    @staticmethod
    def process(row: List[Any]) -> Optional[ComplianceScanResult]:
        """Extracts the PostgreSQL compliance ID and creates a result object."""
        weakness_name = row[2]
        match = PostgresPoamProcessor._psql_id_pattern.search(weakness_name)
        
        if not match:
            return None

        compliance_id = match.group(1)
        poam_id = row[0] if len(row) > 0 else "Unknown"
        asset_identifier = row[6]
        remediation_plan = row[9] if len(row) > 9 else None

        return ComplianceScanResult(
            compliance_id=compliance_id,
            poam_id=str(poam_id),
            status="Fail",
            hostname=str(asset_identifier),
            os_type="PostgreSQL",
            srg_solution=remediation_plan,
            details=f"From POAM: {weakness_name}"
        )