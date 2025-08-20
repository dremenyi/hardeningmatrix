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
import sys
from typing import List
# This new import is required for the POAM parsing functionality
from src.analyzer.processors.poam_processor import parse_poam
from src.cli.parsers import parse_args
from src.cli.utils import ORANGE, RESET
from src.analyzer.processor import  process_compliance_data
from src.export.excel_export import export_to_excel
from getpass import getpass
import os
from datetime import datetime
from src.smartsheet.api import SmartsheetClient
from src.cli.utils import print_header, select_from_list

def run_app():
    """Main application logic, using a dynamic, 'Smartsheet-first' approach."""
    try:
        args = parse_args()

        # 1. CONNECT TO SMARTSHEET AND GET SHEETS
        print_header("Connecting to Smartsheet")
        token = args.token or os.environ.get("SMARTSHEET_TOKEN")
        if not token:
            token = getpass(f"{ORANGE}Enter your Smartsheet Personal Access Token:{RESET} ")
        
        client = SmartsheetClient(token)

        # --- START: WORKSPACE SELECTION ARGUMENT ---
        selected_workspace = None
        if args.workspace_name:
            print(f"{ORANGE}Searching for specified workspace: '{args.workspace_name}'...{RESET}")
            workspaces = client.search_workspaces(args.workspace_name)
            # Find the exact match from the search results
            selected_workspace = next((ws for ws in workspaces if ws['name'] == args.workspace_name), None)
            if not selected_workspace:
                 print(f"{ORANGE}Error: Workspace '{args.workspace_name}' not found.{RESET}")
                 return 1
            print(f"{ORANGE}Found workspace: {selected_workspace['name']}{RESET}")
        else:
            print(f"{ORANGE}Searching for workspaces matching query: '{args.query}'...{RESET}")
            workspaces = client.search_workspaces(args.query)
            selected_workspace = select_from_list(workspaces, lambda w: w['name'], "Select a workspace:")
        # --- END: WORKSPACE SELECTION ARGUMENT ---
        
        if not selected_workspace:
            print(f"{ORANGE}No workspace selected. Exiting.{RESET}")
            return 1

        print(f"{ORANGE}Getting all sheets from workspace: {selected_workspace['name']}{RESET}")
        all_sheets = client.list_sheets(selected_workspace['id'])

        # 2. IDENTIFY AND SELECT BENCHMARK SHEETS
        available_compliance_sheets = {s['name']: s for s in all_sheets if s['name'].startswith("SCM:")}
        if not available_compliance_sheets:
            print(f"{ORANGE}Error: No sheets with the 'SCM:' prefix found.{RESET}")
            return 1

        sheet_names_to_run = []
        if args.scm_sheet:
            # Handle the "All" case first
            if "All" in args.scm_sheet or "all" in [s.lower() for s in args.scm_sheet]:
                sheet_names_to_run = list(available_compliance_sheets.keys())
            else:
                # Create a mapping of normalized names to original names for flexible matching
                # This handles differences in case, spaces, and underscores
                normalized_map = {
                    name.lower().replace(" ", "").replace("_", ""): name 
                    for name in available_compliance_sheets.keys()
                }
                
                missing_sheets = []
                for requested_name in args.scm_sheet:
                    # Normalize the user's input in the same way
                    normalized_requested = requested_name.lower().replace(" ", "").replace("_", "")
                    
                    # Find the original sheet name from our map
                    original_name = normalized_map.get(normalized_requested)
                    if original_name:
                        sheet_names_to_run.append(original_name)
                    else:
                        missing_sheets.append(requested_name)
                
                if missing_sheets:
                    print(f"{ORANGE}Warning: The following SCM sheets were not found and will be skipped: {', '.join(missing_sheets)}{RESET}")
        else:
            # Fallback to the existing interactive selection
            if len(available_compliance_sheets) > 1:
                options = list(available_compliance_sheets.keys()) + ["All"]
                choice = select_from_list(options, lambda x: x, "Which SCM sheet would you like to use?")
                if choice == "All":
                    sheet_names_to_run = list(available_compliance_sheets.keys())
                elif choice:
                    sheet_names_to_run = [choice]
            else:
                sheet_names_to_run = list(available_compliance_sheets.keys())
        
        if not sheet_names_to_run:
            print(f"{ORANGE}No SCM sheets selected for analysis. Exiting.{RESET}")
            return 1
        print(f"{ORANGE}Analyzing against sheet(s): {', '.join(sheet_names_to_run)}{RESET}")

        # 3. GET COMPENSATING CONTROLS AND CLIENT INFO (ONCE)
        control_sheets = [s for s in all_sheets if s['name'].startswith("Compensating Controls")]
        
        # --- START: COMPENSATING CONTROLS SHEET ARGUMENT ---
        selected_control_sheet = None
        if args.compensating_controls_sheet_name:
             selected_control_sheet = next((s for s in control_sheets if s['name'] == args.compensating_controls_sheet_name), None)
             if not selected_control_sheet:
                 print(f"{ORANGE}Error: Compensating Controls sheet '{args.compensating_controls_sheet_name}' not found.{RESET}")
                 return 1
        else:
            selected_control_sheet = select_from_list(control_sheets, lambda s: s['name'], "Select the Compensating Controls sheet:")
        # --- END: COMPENSATING CONTROLS SHEET ARGUMENT---

        control_sheet_data = client.get_sheet(selected_control_sheet['id'])
        
        # --- START: CLIENT ARGUMENT ---
        selected_client = None
        if args.client:
            selected_client = args.client
            print(f"{ORANGE}Using specified client: {selected_client}{RESET}")
        else:
            client_column_id = next((col.get('id') for col in control_sheet_data.get('columns', []) if col.get('title') == 'CLIENT'), None)
            clients = sorted(list(set(cell['value'] for row in control_sheet_data.get('rows', []) for cell in row.get('cells', []) if cell.get('column_id') == client_column_id and cell.get('value')))) if client_column_id else []
            if not clients:
                print(f"{ORANGE}No clients found in the selected sheet. Exiting.{RESET}")
                return 1
            selected_client = select_from_list(clients, lambda c: c, "Select a CLIENT:")
        # --- END: CLIENT ARGUEMENT ---

        if not selected_client:
            print(f"{ORANGE}No client selected. Exiting.{RESET}")
            return 1

        # 4. PROCESS EACH SELECTED BENCHMARK
        all_comparison_results = {}
        for sheet_name in sheet_names_to_run:
            benchmark_name_from_sheet = sheet_name.replace("SCM:", "").strip()
            print_header(f"Processing Benchmark: {benchmark_name_from_sheet}")

            grouped_findings = parse_poam(args.poam, [benchmark_name_from_sheet])
            if not grouped_findings:
                print(f"{ORANGE}No relevant findings found in POAM for '{benchmark_name_from_sheet}'. Skipping.{RESET}")
                continue
            
            scan_results = list(grouped_findings.values())[0]
            
            target_sheet = available_compliance_sheets.get(sheet_name)
            print(f"{ORANGE}Using sheet: {target_sheet['name']}{RESET}")
            compliance_sheet_data = client.get_sheet(target_sheet['id'])
            
            comparison = process_compliance_data(control_sheet_data, compliance_sheet_data, selected_client, scan_results)
            
            if comparison:
                comparison.unmatched_smartsheet_items = []
                comparison.smartsheet_count = comparison.match_count
                all_comparison_results[benchmark_name_from_sheet] = comparison

        # 5. GENERATE FINAL REPORT
        if not all_comparison_results:
            print(f"{ORANGE}No data to report. Exiting.{RESET}")
            return 1
            
        print_header("Exporting to Excel")
        
        if args.output:
            output_filename = args.output
        else:
            default_filename = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_filename = input(f"{ORANGE}Enter filename to save Excel data (default: {default_filename}):{RESET} ").strip()
            if not output_filename:
                output_filename = default_filename
        
        if not output_filename.endswith('.xlsx'):
            output_filename += '.xlsx'
        
        print(f"{ORANGE}Exporting to Excel file: {output_filename}{RESET}")
        if export_to_excel(all_comparison_results, output_filename):
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