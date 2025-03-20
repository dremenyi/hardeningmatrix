#!/usr/bin/env python3
"""
Smartsheet Compliance Analyzer - Main Entry Point

This tool automates the comparison between compliance scan results and
Smartsheet data. It extracts compliance information, processes deviation
rationales with client-specific values, and generates Excel reports
showing matched and unmatched compliance items.

Usage:
    python main.py --scan-csv <scan_file.csv> --token <smartsheet_token> [options]

Options:
    --scan-csv, -s     Path to the compliance scan CSV file (required)
    --token, -t        Smartsheet API token (or set SMARTSHEET_TOKEN env variable)
    --query, -q        Search query for workspace (default: "SCM Program")
    --client, -c       Client name to filter results (will skip selection if provided)
    --output, -o       Custom output filename for the Excel report

For detailed information, see the README.md file.
"""

from src.cli.app import run_app

if __name__ == "__main__":
    # Execute the main application logic and capture the exit code.
    exit_code = run_app()
    # Use the exit code to indicate success (0) or failure (non-zero)
    exit(exit_code)