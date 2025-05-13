# Import processors
from src.analyzer.processors.rhel_processor import RhelComplianceProcessor
from src.analyzer.processors.postgres_processor import PostgresComplianceProcessor

# Registry of all available processors
PROCESSORS = [
    RhelComplianceProcessor,
    PostgresComplianceProcessor,
]

# Export for public API
__all__ = [
    'PROCESSORS',
    'RhelComplianceProcessor',
    'PostgresComplianceProcessor',
]