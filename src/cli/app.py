"""
Smartsheet Compliance Analyzer - Main Application Logic

This module contains the core application logic for the Smartsheet Compliance Analyzer tool.
It handles the command-line interface, data retrieval from Smartsheet, client selection,
and compliance data comparison and reporting process.

Key functionality:
- Parses command-line arguments to determine operations
- Authenticates with the Smartsheet API using user-provided tokens
- Retrieves and processes workspace, sheet, and client data
- Coordinates the comparison of compliance scan results with Smartsheet data
- Generates detailed Excel reports of findings

The application follows a step-by-step workflow:
1. Parse command-line arguments
2. Search for and select Smartsheet workspaces
3. Select the appropriate Compensating Controls and Compliance ClearingHouse sheets
4. Extract and filter data for the selected client
5. Process the scan results and compare with Smartsheet data
6. Generate an Excel report with matched and unmatched compliance items
"""

from src.cli.parsers import parse_args
from src.cli.utils import ORANGE, RESET
from src.analyzer.processor import load_scan_results, process_compliance_data
from src.export.excel_export import export_to_excel
from getpass import getpass
import os
from datetime import datetime
from src.smartsheet.api import SmartsheetClient
from src.cli.utils import print_header, select_from_list


def run_app():
    """Main application logic, directly running the comparison."""
    try:
        args = parse_args()

        print_header("Loading Compliance Scan Results")
        scan_results = load_scan_results(args.scan_csv)
        print(f"{ORANGE}Loaded {len(scan_results)} scan results from {args.scan_csv}{RESET}")
        
        if not scan_results:
            print(f"{ORANGE}No scan results found. Exiting.{RESET}")
            return 1
        
        # Get Smartsheet data directly from API
        print_header("Fetching Smartsheet Data")
        
        # Get the token, prompting if necessary
        token = args.token or os.environ.get("SMARTSHEET_TOKEN")
        if not token:
            token = getpass(f"{ORANGE}Enter your Smartsheet Personal Access Token:{RESET} ")
        
        # Create client
        client = SmartsheetClient(token)
        
        # Search for workspaces
        print(f"{ORANGE}Searching for workspaces matching '{args.query}'...{RESET}")
        workspaces = client.search_workspaces(args.query)
        
        if not workspaces:
            print(f"{ORANGE}No workspaces found matching '{args.query}'.{RESET}")
            return 1
        
        # Select workspace
        selected_workspace = None
        if len(workspaces) == 1:
            selected_workspace = workspaces[0]
            print(f"{ORANGE}Found workspace: {selected_workspace['name']}{RESET}")
        else:
            print(f"{ORANGE}Found {len(workspaces)} workspaces matching '{args.query}'.{RESET}")
            selected_workspace = select_from_list(
                workspaces,
                lambda w: f"{w['name']} ({w['id']})",
                "Select a workspace:"
            )
        
        if not selected_workspace:
            print(f"{ORANGE}No workspace selected. Exiting.{RESET}")
            return 1
        
        # Get sheets
        print(f"{ORANGE}Getting sheets from workspace: {selected_workspace['name']}{RESET}")
        all_sheets = client.list_sheets(selected_workspace['id'])
        
        if not all_sheets:
            print(f"{ORANGE}No sheets found in workspace.{RESET}")
            return 1
        
        # Filter sheets
        control_sheets = [s for s in all_sheets if s['name'].startswith("Compensating Controls")]
        compliance_sheets = [s for s in all_sheets if s['name'].startswith("Compliance ClearingHouse")]
        
        if not control_sheets:
            print(f"{ORANGE}No Compensating Controls sheets found.{RESET}")
            return 1
            
        if not compliance_sheets:
            print(f"{ORANGE}No Compliance ClearingHouse sheets found.{RESET}")
            return 1
        
        # Select control sheet
        print(f"{ORANGE}Found {len(control_sheets)} Compensating Controls sheets.{RESET}")
        selected_control_sheet = select_from_list(
            control_sheets,
            lambda s: f"{s['name']} (Modified: {s['modified_at'] or 'Unknown'})",
            "Select a Compensating Controls sheet:"
        )
        
        if not selected_control_sheet:
            print(f"{ORANGE}No Compensating Controls sheet selected. Exiting.{RESET}")
            return 1
        
        # Select compliance sheet
        print(f"{ORANGE}Found {len(compliance_sheets)} Compliance ClearingHouse sheets.{RESET}")
        selected_compliance_sheet = select_from_list(
            compliance_sheets,
            lambda s: f"{s['name']} (Modified: {s['modified_at'] or 'Unknown'})",
            "Select a Compliance ClearingHouse sheet:"
        )
        
        if not selected_compliance_sheet:
            print(f"{ORANGE}No Compliance ClearingHouse sheet selected. Exiting.{RESET}")
            return 1
        
        # Retrieve sheet data
        print(f"{ORANGE}Retrieving sheet data...{RESET}")
        control_sheet_data = client.get_sheet(selected_control_sheet['id'])
        compliance_sheet_data = client.get_sheet(selected_compliance_sheet['id'])
        
        # Extract clients
        clients = set()
        client_column_id = None
        
        # Find the CLIENT column ID
        for column in control_sheet_data.get('columns', []):
            if column['title'] == 'CLIENT':
                client_column_id = column['id']
                break
                
        if client_column_id:
            # Extract all unique client values
            for row in control_sheet_data.get('rows', []):
                for cell in row.get('cells', []):
                    if cell.get('column_id') == client_column_id and cell.get('value'):
                        clients.add(cell.get('value'))
        
        # Convert to list and sort
        client_list = sorted(list(clients))
        
        if not client_list:
            print(f"{ORANGE}No clients found in the Compensating Controls sheet.{RESET}")
            return 1
        
        # Select client or use provided one
        selected_client = args.client
        if selected_client and selected_client not in client_list:
            print(f"{ORANGE}Warning: Specified client '{selected_client}' not found in sheet.{RESET}")
            selected_client = None
            
        if not selected_client:
            print(f"{ORANGE}Found {len(client_list)} clients in the sheet.{RESET}")
            selected_client = select_from_list(
                client_list,
                lambda c: c,
                "Select a CLIENT:"
            )
        
        if not selected_client:
            print(f"{ORANGE}No client selected. Exiting.{RESET}")
            return 1
            
        print(f"{ORANGE}Selected CLIENT: {selected_client}{RESET}")
        
        # Filter control sheet data for the selected client
        filtered_control_rows = []
        for row in control_sheet_data.get('rows', []):
            client_value = None
            for cell in row.get('cells', []):
                if cell.get('column_id') == client_column_id:
                    client_value = cell.get('value')
                    break
                    
            if client_value == selected_client:
                filtered_control_rows.append(row)
                
        # Update the control sheet data with filtered rows
        control_sheet_data['rows'] = filtered_control_rows
        
        # Process the data directly using the process.py
        comparison = process_compliance_data(
            control_sheet_data,
            compliance_sheet_data,
            selected_client,
            scan_results,
            args.scan_csv  # Pass the CSV path
)
        
        if not comparison:
            print(f"{ORANGE}No Smartsheet results found. Exiting.{RESET}")
            return 1
    
        print(f"{ORANGE}Summary:{RESET}")
        print(f"  - Scan items: {comparison.scan_count}")
        print(f"  - Smartsheet items: {comparison.smartsheet_count}")
        print(f"  - Matched items: {comparison.match_count}")
        print(f"  - Unmatched scan items: {len(comparison.unmatched_scan_items)}")
        print(f"  - Unmatched Smartsheet items: {len(comparison.unmatched_smartsheet_items)}")
        
        # Export to Excel
        print_header("Exporting to Excel")
        
        # Determine output filename
        if args.output:
            output_filename = args.output
        else:
            # Generate default filename
            default_filename = f"compliance_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_filename = input(f"{ORANGE}Enter filename to save Excel data (default: {default_filename}):{RESET} ").strip()
            if not output_filename:
                output_filename = default_filename
        
        # Ensure filename has .xlsx extension
        if not output_filename.endswith('.xlsx'):
            output_filename += '.xlsx'
        
        # Export to Excel
        print(f"{ORANGE}Exporting to Excel file: {output_filename}{RESET}")
        if export_to_excel(comparison, output_filename):
            print(f"{ORANGE}Export completed successfully!{RESET}")
        else:
            print(f"{ORANGE}Error exporting to Excel.{RESET}")
            return 1
        
        return 0
            
    except KeyboardInterrupt:
        print(f"\n{ORANGE}Operation cancelled by user. Exiting.{RESET}")
        return 1
    except Exception as e:
        print(f"\n{ORANGE}Error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return 1