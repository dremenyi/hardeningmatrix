"""
Processor registry for compliance benchmark processors.

This module serves as a registry for all available benchmark processors
and provides easy access to them.
"""

# Import processors here - we'll add them as we create them
# from src.analyzer.processors.rhel_processor import RhelComplianceProcessor
# from src.analyzer.processors.postgres_processor import PostgresComplianceProcessor

# Registry of all available processors - we'll add them as we create them
PROCESSORS = [
    # RhelComplianceProcessor,
    # PostgresComplianceProcessor,
]

# Export for public API - we'll add them as we create them
__all__ = [
    'PROCESSORS',
    'RhelComplianceProcessor',
    # 'PostgresComplianceProcessor',
]