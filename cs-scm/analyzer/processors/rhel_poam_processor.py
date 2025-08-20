
import re
from typing import List, Optional, Any
from .base_poam_processor import BasePoamProcessor
from src.analyzer.models import ComplianceScanResult

class RhelPoamProcessor(BasePoamProcessor):
    """Processes RHEL compliance findings from a POAM row."""
    benchmark_name: str = "RHEL"

    # This pattern is specific and only looks for RHEL-XX-XXXXXX
    _rhel_pattern = re.compile(r'\b(RHEL-\d{2}-\d{6})\b')

    @staticmethod
    def can_process(row: List[Any]) -> bool:
        """
        Checks for a RHEL-style compliance ID in the 'Weakness Name' column.
        This is the most reliable way to identify a RHEL row.
        """
        # "Weakness Name" is in Column C (index 2)
        if len(row) > 2 and isinstance(row[2], str):
            # If the specific RHEL ID pattern is found, this is a RHEL row.
            return bool(RhelPoamProcessor._rhel_pattern.search(row[2]))
        return False

    @staticmethod
    def process(row: List[Any]) -> Optional[ComplianceScanResult]:
        """Extracts the RHEL compliance ID and creates a result object."""
        weakness_name = row[2]
        match = RhelPoamProcessor._rhel_pattern.search(weakness_name)
        
        if not match:
            return None

        compliance_id = match.group(1)
        poam_id = row[0] if len(row) > 0 else "Unknown"
        asset_identifier = row[6] if len(row) > 6 else "Unknown"
        remediation_plan = row[9] if len(row) > 9 else None

        return ComplianceScanResult(
            compliance_id=compliance_id,
            poam_id=str(poam_id),
            status="Fail",
            hostname=str(asset_identifier),
            os_type="RHEL",
            srg_solution=remediation_plan,
            details=f"From POAM: {weakness_name}"
        )