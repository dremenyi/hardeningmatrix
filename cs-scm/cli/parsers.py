import argparse
from typing import List

class Colors:
    """A class to hold ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def parse_args(args: List[str] = None) -> argparse.Namespace:
    """
    Parses command-line arguments for the Smartsheet Compliance Analyzer.
    """
    parser = argparse.ArgumentParser(
        description=(
            f"\n{Colors.BOLD}{Colors.OKBLUE}"
            "Smartsheet Compliance Analyzer"
            f"{Colors.ENDC}\n"
            f"{Colors.OKBLUE}----------------------------------------{Colors.ENDC}\n"
            "This tool automates the compliance analysis process by comparing "
            "scan results with Smartsheet data.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Group for mutually exclusive input files
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "-p", "--poam",
        type=str,
        help="The path to the POAM (.xlsm) file.",
    )

    # All other arguments
    parser.add_argument(
        "-t", "--token",
        type=str,
        required=True,
        help="The Smartsheet API token.",
    )
    
    parser.add_argument(
        "-q", "--query",
        type=str,
        default="SCM Program",
        help='Search query for Smartsheet workspace (defaults to "SCM Program").'
    )

    parser.add_argument(
        "--client",
        type=str,
        help="The name of the client to analyze (alternative to --client-name). Skips interactive selection.",
    )

    parser.add_argument(
        "--scm-sheet",
        nargs='+',  # This allows for one or more values
        type=str,
        help='One or more SCM sheet names to analyze (e.g., "SCM: RHEL 8.X" "SCM:PostgreSQL15_CIS1.1.0"). Use "All" to run against all found SCM sheets.'
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="The name of the output Excel file.",
    )
    
    # THE ARGUMENTS BELOW ARE FOR NON-INTERACTIVE RUNS, SO THEY DON'T NEED DEFAULTS.
    parser.add_argument(
        "--workspace-name",
        type=str,
        help="The name of the Smartsheet workspace. Skips interactive workspace selection.",
    )
    
    parser.add_argument(
        "--clearinghouse-sheet-name",
        type=str,
        help="The name of the Compliance ClearingHouse sheet. Skips interactive sheet selection.",
    )
    
    parser.add_argument(
        "--compensating-controls-sheet-name",
        type=str,
        help="The name of the Compensating Controls sheet. Skips interactive sheet selection.",
    )

    return parser.parse_args(args)