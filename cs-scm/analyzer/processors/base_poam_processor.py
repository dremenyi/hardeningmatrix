
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from src.analyzer.models import ComplianceScanResult

class BasePoamProcessor(ABC):
    """
    Abstract base class for POAM row processors.
    """
    # Add a class attribute to identify the benchmark
    benchmark_name: str = "Unknown"

    @staticmethod
    @abstractmethod
    def can_process(row: List[Any]) -> bool:
        """
        Determines if this processor can handle the given POAM row.
        """
        pass

    @staticmethod
    @abstractmethod
    def process(row: List[Any]) -> Optional[ComplianceScanResult]:
        """
        Processes a single POAM row and returns a standardized result.
        """
        pass