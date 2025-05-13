"""
Base class for compliance benchmark processors.

This module defines the abstract base class that all benchmark-specific
processors must implement. It ensures a consistent interface across
different benchmark types (RHEL, PostgreSQL, Windows, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd

from src.analyzer.models import ComplianceScanResult


class BaseComplianceProcessor(ABC):
    """
    Abstract base class for compliance benchmark processors.
    
    All benchmark-specific processors must inherit from this class and
    implement its abstract methods.
    """
    
    @classmethod
    @abstractmethod
    def can_process(cls, csv_path: str, dataframe: pd.DataFrame) -> bool:
        """
        Determine if this processor can handle the given CSV file.
        
        Args:
            csv_path: Path to the CSV file
            dataframe: Pandas DataFrame of the loaded CSV
            
        Returns:
            True if this processor can handle the file, False otherwise
        """
        pass
    
    @classmethod
    @abstractmethod
    def can_process_id(cls, compliance_id: str) -> bool:
        """
        Check if this processor can handle the given compliance ID.
        
        Args:
            compliance_id: A compliance identifier (e.g., 'RHEL-08-010030', 'PG-1.1')
            
        Returns:
            True if this processor can handle the compliance ID, False otherwise
        """
        pass
    
    @classmethod
    @abstractmethod
    def process(cls, csv_path: str, dataframe: pd.DataFrame) -> List[ComplianceScanResult]:
        """
        Process the CSV file and extract compliance results.
        
        Args:
            csv_path: Path to the CSV file
            dataframe: Pandas DataFrame of the loaded CSV
            
        Returns:
            List of ComplianceScanResult objects
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_benchmark_info(cls, compliance_id: str) -> Dict[str, str]:
        """
        Get additional benchmark information for a compliance ID.
        
        Args:
            compliance_id: The compliance ID to get info for
            
        Returns:
            Dictionary of additional information about the benchmark item
        """
        pass
    
    @classmethod
    @abstractmethod
    def needs_review(cls, item: ComplianceScanResult) -> bool:
        """
        Determine if a compliance item needs review (failed/warning).
        
        Args:
            item: The compliance item to check
            
        Returns:
            True if the item needs review, False otherwise
        """
        pass