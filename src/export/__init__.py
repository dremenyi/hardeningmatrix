"""
Smartsheet Compliance Analyzer - Export Package

This package provides functionality for exporting compliance analysis results
to structured, formatted reports. It currently supports Excel export with
multiple sheets, conditional formatting, and data organization.

Key Features:
- Multiple sheet export for different data categories
- Conditional formatting based on compliance status and severity
- Summary statistics and detailed findings
- Visual organization with color coding and tab colors
"""

from src.export.excel_export import export_to_excel

__all__ = [
    'export_to_excel'  # Main export function
]