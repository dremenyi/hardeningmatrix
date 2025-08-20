# Smartsheet Compliance Analyzer

A powerful command-line tool for automating compliance analysis by comparing findings from a Plan of Action and Milestones (POAM) with an organization's compliance documentation stored in Smartsheet.

## Overview

The **Smartsheet Compliance Analyzer** is a specialized tool designed to streamline the compliance analysis process. It automates the comparison between findings in a POAM file and client-specific compliance documentation in Smartsheet, saving security and compliance professionals significant time and reducing manual errors.

### Supported Benchmarks

-   **Red Hat Enterprise Linux 8.x**
-   **PostgreSQL 15.x** (for managed cloud instances like AWS RDS, Google Cloud SQL, and Azure Database)
-   *Future support is planned for Windows, Ubuntu, RHEL 9, and AL2023.*

### Prerequisites

-   **POAM File**: Must be in `.xlsm` format and contain a tab named "Configuration Findings".
-   **Smartsheet Naming Convention**:
    -   Your "SCM" sheets must follow the naming convention `SCM: [Benchmark Name]`, for example:
        -   `SCM: RHEL 8.X`
        -   `SCM: PostgreSQL15_CIS1.1.0`
    -   Your "Compensating Controls" sheet must start with the name `Compensating Controls`.
-   **Smartsheet Access**: You must have a valid API Access Token for your Smartsheet account.
  
          -  To create a Smartsheet API Key:
          -  Login to Smartsheet via the MyApps tile.
          -  Click the avatar icon in the bottom left corner.
          -  Select Personal Settings.
          -  Select API Access in the new window.
          -  Click 'Generate new access token'.
          -  Give the token a name specific to the SCM tool, ex: cs-scm.
          -  Copy the token into a secure password manager for use later. 
-   **Python 3.9+**
-   **pipenv** for managing the project's virtual environment.

---
## Installation

This project uses `pipenv` for dependency management.

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd cs-scm
    ```
2.  **Install dependencies**:
    This command will create a virtual environment and install all necessary packages from the `Pipfile`.
    ```bash
    pipenv install
    ```

---
## Usage

### Interactive Mode (Recommended)

1.  **Activate the virtual environment**:
    ```bash
    pipenv shell
    ```

2.  **Run the program**:
    The only required arguments are the path to your POAM file and your Smartsheet API token.
    ```bash
    python main.py --poam "/path/to/your/poam.xlsm" --token "YOUR_SMARTSHEET_TOKEN"
    ```
    The script will then guide you through selecting your workspace, which SCM sheet(s) to analyze, your compensating controls sheet, and the specific client.

### Non-Interactive Mode (for Automation)

You can bypass all interactive prompts by providing the names as command-line arguments.

```bash
pipenv run python main.py \
    --poam "/path/to/poam.xlsm" \
    --token "YOUR_SMARTSHEET_TOKEN" \
    --workspace-name "SCM Program" \
    --scm-sheet "SCM: RHEL 8.X" "SCM:PostgreSQL15_CIS1.1.0" \
    --compensating-controls-sheet-name "Compensating Controls Tooling List" \
    --client "Your Client Name" \
    --output "my_report.xlsx"
```

### Command-Line Arguments

| Argument                                    | Short | Description                                            | Required | Skips Interaction Selection | Examples                                                  |
| ------------------------------------------- | ----- | ------------------------------------------------------ | -------- | ----------------------------|-----------------------------------------------------------|
| `--poam <path>`                             | `-p`  | The path to the POAM (`.xlsm`) file.                   | **Yes**  |       **No**                |                                                           |
| `--token <token>`                           | `-t`  | The Smartsheet API token.                              | **Yes**  |       **No**                |                                                           |
| `--workspace-name <name>`                   |       | The name of the Smartsheet workspace.                  |   No     |       **No**                |                                                           |
| `--scm-sheet <name>`                        |       | One or more SCM sheet names to analyze.                |   No     |       **Yes**               |**All**, **SCM: RHEL 8.x**, **SCM: PostgreSQL15_CIS1.1.0** |    
| `--compensating-controls-sheet-name <name>` |       | The name of the Compensating Controls sheet.           |   No     |       **Yes**               |                                                           |
| `--client <name>`                           | `-c`  | The name of the client to analyze.                     |   No     |       **Yes**               |                                                           |      
| `--output <filename>`                       | `-o`  | The name of the output Excel file.                     |   No     |       **Yes**               |                                                           |


## Architecture Deep Dive

This section provides a verbose breakdown of the project's architecture and modules for developers and contributors.

### `main.py` - The Entry Point

The `main.py` script is the primary entry point for the entire application:

-   **Path Setup**: It modifies the system path to ensure that Python can correctly locate and import all modules within the `src` directory. This prevents `ModuleNotFoundError` issues, regardless of how the script is executed.
-   **Execution**: It imports and calls the `run_app` function from `src.cli.app` and exits with the return code from that function.

### `src/smartsheet` - API Integration

This package isolates all direct communication with the Smartsheet API.

-   **`api.py`**: Contains the `SmartsheetClient` class, which is a wrapper around the official `smartsheet-python` library. It simplifies API calls for actions like listing workspaces, searching for sheets, and getting sheet data.
-   **`models.py`**: Defines Pydantic models that represent objects from the Smartsheet API (like workspaces and sheets), ensuring that the data received from the API is in a predictable and validated format.

### `src/cli` - Command-Line Interface

This package handles all user interaction, from parsing arguments to displaying interactive menus.

-   **`parsers.py`**: This module uses Python's `argparse` library to define and manage all command-line arguments. It sets up which arguments are required (like `--poam` and `--token`), which are optional, and which can accept multiple values (like `--scm-sheet`). This file contains all of the application's command-line API arguements.
-   **`utils.py`**: A collection of helper functions to enhance the user experience. This includes the logic for creating interactive, navigable menus (`select_from_list`) and for printing colored and formatted text to the console.
-   **`app.py`**: This is the orchestrator of the entire application workflow. The `run_app` function within this module executes the primary logic in a sequential manner:
    1.  Parses command-line arguments.
    2.  Connects to the Smartsheet API.
    3.  Handles workspace, sheet, and client selection, using either the provided command-line arguments or falling back to interactive prompts.
    4.  Calls the POAM parser to get a grouped dictionary of compliance findings.
    5.  Loops through each selected benchmark, calling the main `process_compliance_data` function to perform the analysis.
    6.  Calls the Excel exporter to generate the final report.

### `src/analyzer` - The Core Engine

This package contains all of the logic for data processing, modeling, and comparison.

-   **`models.py`**: Defines the application's data structures using `Pydantic`. These models (`ComplianceItem`, `ComplianceScanResult`, `ComparisonResult`, etc.) ensure data is valid and consistent as it moves through the application. They enforce data types and prevent common errors.
-   **`processor.py`**: This module contains the primary data manipulation and analysis functions:
    -   `extract_client_controls`: Reads the "Compensating Controls" sheet to build a mapping of client-specific values (e.g., `cloud_provider: 'AWS'`).
    -   `extract_compliance_items`: Reads a "SCM" sheet, creates `ComplianceItem` objects, and performs dynamic placeholder replacement in deviation rationales using the client controls.
    -   `compare_results`: Takes the list of findings from the POAM and the list of items from Smartsheet and performs the core matching logic based on the `compliance_id`. It generates a `ComparisonResult` object containing the matched and unmatched items.
    -   `process_compliance_data`: A wrapper function that orchestrates the calls to the functions above for a single benchmark.
-   **`processors/` (Sub-Package)**: This directory contains the modular, plug-and-play system for parsing the POAM file.
    -   `base_poam_processor.py`: An abstract base class that serves as a template for all other processors. It mandates that every processor must have a `benchmark_name` and a `can_process` and `process` method, ensuring consistency.
    -   `poam_processor.py`: This is the **dispatcher**. Its `parse_poam` function is the only one called by the main app. It reads the POAM file row by row and passes each row to its registry of specialized processors, asking "Can you handle this?". The first processor to say "yes" gets to process the row.
    -   `rhel_poam_processor.py` & `postgres_poam_processor.py`: These are the specialized processors. Each one is an expert on a single benchmark. They contain the specific logic to identify a row as belonging to their benchmark and to correctly extract the `compliance_id` and other relevant data. This is where you would add a new benchmark like Windows. Create the processor and add it to the dispatcher registry.

### `src/export` - Reporting

This package is responsible for generating the final user-facing output.

-   **`excel_export.py`**: This module contains all logic for creating the final `.xlsx` report.
    -   It receives the `all_comparison_results` dictionary, which contains the results for each benchmark.
    -   It loops through each benchmark and calls the `categorize_findings` function to sort the matched items into the correct buckets (`Approved`, `Should Fix`, etc.).
    -   It then creates a set of dedicated, prefixed sheets for each benchmark (e.g., `RHEL_Approved`, `PSQLv15_Approved`).
    -   Finally, the `format_workbook` function applies all the styling, including colors, fonts, column widths, word wrapping, and hyperlinks.
