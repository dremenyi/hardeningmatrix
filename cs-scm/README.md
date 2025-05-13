# Smartsheet Compliance Analyzer

A powerful tool for automating compliance analysis by comparing external scan results with Smartsheet compliance data.

## Overview

The Smartsheet Compliance Analyzer is a specialized tool designed to streamline the compliance analysis process by automating the comparison between external compliance scan results and client-specific compliance documentation stored in Smartsheet. This tool helps security and compliance professionals save time and reduce errors when managing compliance exceptions and deviations.


### SUPPORTED OPERATING SYSTEMS AND STIG VERSION(S)

- **Redhat Enterprise 8.x (any minor version) | STIG Version V2R1**

### SUPPORTED VULNERABILITY SCANNERS

As of 29 April 2025, only the compliance results outputed from Nessus are known to be working with this tool. Future iterations may include Wiz, and Rapid7.

### Prerequisites

- **Nessus must be using RHEL stig version V2R1**, any other release will output incorrect results. Ensure the benchmark you are scanning against FOR ALL RHEL 8 SYSTEMS is V2R1.
- **Client compliance scans must be exported as a .csv from nessus.**
- **Ensure you have access to the following smartsheets:**
  - ***[compensating controls list](https://app.smartsheet.com/sheets/c5W6FvwPxQMVVHx5f6mMcWwx98Ww22p9GcQPqmp1?view=grid)***
    - ****Ensure that the client has their toolsets filled in using the dropdowns provided.****
  - ***[rhel8 compliance clearing house tracker](https://app.smartsheet.com/sheets/3vfpRJG9GG3RvC5hW6Jf8jCqqXVwmMHp2xHxH2X1?view=grid&filterId=4284754240163716)***
    - ****You only need access to this sheet, you do not need to edit anything. Editing this sheet could break the automation.****
- **Create an Access token in Smartsheet.**
- **Python 3.11.5 or later**
- **Pip (python package manager)**
- **pipenv (pip3 install pipenv)**
### Key Features

- **Automated Scan Integration**: Parse various compliance scan result formats (Nessus, CSV)
- **Smartsheet Data Extraction**: Retrieve and process compliance data from Smartsheet workspaces
- **Client-Specific Analysis**: Filter and process data for specific clients
- **Dynamic Placeholder Replacement**: Automatically replace placeholders with client-specific values
- **Comprehensive Comparison**: Match scan findings with approved deviations and identify gaps
- **Detailed Reporting**: Generate Excel reports with matched and unmatched compliance items

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
smartsheet-compliance-analyzer/
├── main.py                  # Entry point
├── src/
│   ├── analyzer/            # Core analysis functionality
│   │   ├── models.py        # Data models for compliance items
│   │   └── processor.py     # Processing and comparison logic
│   ├── cli/                 # Command-line interface
│   │   ├── app.py           # Main application runner
│   │   ├── parsers.py       # Command-line argument parsing
│   │   └── utils.py         # CLI utilities and helpers
│   ├── export/              # Export functionality
│   │   └── excel_export.py  # Excel report generation
│   └── smartsheet/          # Smartsheet API integration
│       ├── api.py           # API client implementation
│       └── models.py        # Smartsheet data models
```

## Workflow

The application follows a step-by-step workflow:

1. **CLI Setup**: Parse command-line arguments to determine input files and options
2. **Scan Result Loading**: Load and parse compliance scan results from CSV
3. **Smartsheet Connection**: Authenticate with the Smartsheet API
4. **Workspace Selection**: Search for and select the appropriate Smartsheet workspace
5. **Sheet Selection**: Select the required Compensating Controls and Compliance ClearingHouse sheets
6. **Client Selection**: Select or filter for a specific client
7. **Control Extraction**: Extract client-specific control values from the Compensating Controls sheet
8. **Compliance Processing**: Extract compliance items and replace placeholders with client values
9. **Comparison**: Compare scan results with Smartsheet compliance data
10. **Report Generation**: Generate a detailed Excel report of the findings

## Installation
- Install pipenv with pip (pip or pip3 install pipenv)
- Clone this code
- Change directory to the scm directory and run **pipenv install .**
- run the command (this is a bug, it's not currently installed via the previous pipenv command. Will be fixed in a future release.
 ```bash
pipenv install pydantic
```


## Usage

### Basic Usage

- Retrieve your Smartsheet API key.
- Copy your client files to a separate directory.
- from the SRC directory, run ```bash
pipenv shell
```
- Run the program
```bash
pipenv run python main.py --scan-csv [path/to/your-compliance-csv-name] --token [your-smartsheet-api-token] --query "SCM Program"
```

### All Options

```bash
pipenv run python main.py --scan-csv path/to/scan_results.csv [options]

Options:
  --scan-csv, -s     Path to the compliance scan CSV file (required)
  --token, -t        Smartsheet API token (or set SMARTSHEET_TOKEN env variable)
  --query, -q        Search query for workspace (default: "SCM Program")
  --client, -c       Client name to filter results (will skip selection if provided)
  --output, -o       Custom output filename for the Excel report
```

### Example Workflow

1. **Run the tool**:
   ```bash
   pipenv run python main.py --scan-csv RHEL8Comp.csv --token 123457498273498763450072345 --query "SCM Program"
   ```

2. **Select workspace** from the list of matching workspaces

3. **Select sheets**:
   - Choose the appropriate "Compensating Controls" sheet
   - Choose the appropriate "Compliance ClearingHouse" sheet

4. **Select client** from the list of available clients in the sheet

5. **Review results** in the generated Excel report:
   - Matched compliance items (found in both scan and Smartsheet)
   - Unmatched scan items (items in scan but not in Smartsheet)

## Data Models

### Core Data Models

- **ControlValue**: Maps placeholder variables to client-specific values
- **ClientControls**: Collection of control values for a specific client
- **ComplianceItem**: Represents compliance entries from Smartsheet with enhanced metadata
- **ComplianceScanResult**: Represents findings from external compliance scan tools
- **ComparisonResult**: Contains the matching logic outcomes and statistics

### Smartsheet Models

- **Workspace**: Represents a Smartsheet workspace container
- **Sheet**: Represents a Smartsheet sheet with columns and rows

## Smartsheet Integration

The tool integrates with Smartsheet using the following specific data structure:

1. **Compensating Controls Sheet**:
   - Contains client-specific values in a table format
   - Each row represents a set of values for a specific client
   - The "CLIENT" column identifies the client
   - Other columns represent placeholders that can be substituted into rationales

2. **Compliance ClearingHouse Sheet**:
   - Contains compliance items with standard fields:
     - Compliance ID
     - Finding Description
     - SRG Solution
     - Deviation Type
     - Deviation Rationale (may contain placeholders)
     - Supporting Documents
     - Deviation Status
     - Should Fix flag

## Development

### Dependency Management

This project uses Pipenv for dependency management and virtual environment handling:

- `Pipfile` defines the project dependencies
- `Pipfile.lock` locks all dependencies to specific versions for reproducibility

Common Pipenv commands:

```bash
# Install all dependencies (including dev)
pipenv install --dev

# Run a command in the virtual environment
pipenv run python main.py --scan-csv scan_results.csv

# Activate the virtual environment shell
pipenv shell

# Add a new package
pipenv install requests

# Add a development dependency
pipenv install pytest --dev
