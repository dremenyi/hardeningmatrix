"""
Smartsheet Compliance Analyzer - Command Line Argument Parsing

This module provides argument parsing functionality for the Smartsheet Compliance Analyzer.
It defines the command-line interface structure, argument validation, and
handling of default values.

The parser is focused on a streamlined workflow for comparing compliance scan results
with Smartsheet data, requiring minimal setup from the user.

Command-line arguments:
--scan-csv, -s    : Path to compliance scan results CSV file (required)
--token, -t       : Smartsheet API token (defaults to SMARTSHEET_TOKEN env variable)
--query, -q       : Search query for Smartsheet workspace (defaults to "SCM Program")
--client, -c      : Client name to use (skips interactive selection if provided)
--output, -o      : Custom output file path for Excel report

Example usage:
    pipenv run python main.py --scan-csv scan_results.csv --token YOUR_TOKEN --client CLIENT_NAME
"""

import argparse
import os
from src.cli.utils import ORANGE, RESET


def parse_args():
    """Parse command line arguments with a single command structure."""
    parser = argparse.ArgumentParser(
        description=f"{ORANGE}Smartsheet Compliance Comparison Tool{RESET}"
    )

    parser.add_argument(
        "--scan-csv", "-s",
        required=True,
        help="Path to compliance scan results CSV file"
    )
    
    parser.add_argument(
        "--token", "-t",
        default=os.environ.get("SMARTSHEET_TOKEN"),
        help="Smartsheet API token (defaults to SMARTSHEET_TOKEN env variable)"
    )
    
    parser.add_argument(
        "--query", "-q",
        default="SCM Program",
        help="Search query for workspace (defaults to 'SCM Program')"
    )
    
    parser.add_argument(
        "--client", "-c",
        default=None,
        help="Client name to use (skips selection prompt if provided)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (will export in XLSX format)"
    )
    
    return parser.parse_args()