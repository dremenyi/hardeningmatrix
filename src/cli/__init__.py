"""
Command-line interface package for Smartsheet Compliance Analyzer.

This package contains all the components needed for the CLI functionality:
- Command argument parsing
- User interaction utilities
- Main application runner
- Terminal color formatting
"""

from src.cli.app import run_app
from src.cli.parsers import parse_args
from src.cli.utils import (
    print_header, select_from_list, get_key_press,
    ORANGE, WHITE, BOLD, RESET, ORANGE_BG, BLACK
)

__all__ = [
    # Main functions
    'run_app',          # Main application entry point
    'parse_args',       # Command-line argument parser
    'print_header',     # Utility for printing formatted headers
    'select_from_list', # Interactive list selection
    'get_key_press',    # Utility for getting keypresses
    
    # Terminal colors and styles
    'ORANGE',           # Primary theme color
    'WHITE',            # White text
    'BOLD',             # Bold text
    'RESET',            # Reset all formatting
    'ORANGE_BG',        # Orange background
    'BLACK',            # Black text (for use with colored backgrounds)
]