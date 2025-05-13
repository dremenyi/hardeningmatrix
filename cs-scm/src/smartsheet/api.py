"""
Smartsheet API Client Module

This module provides a client interface for interacting with the Smartsheet API.
It handles authentication, error handling, and provides methods for common
operations like searching workspaces, listing sheets, and retrieving data.

Key Features:
- Token-based authentication with the Smartsheet API
- Workspace discovery and filtering
- Sheet listing and filtering by prefix
- Detailed sheet data retrieval with full row and column information
- Conversion between Smartsheet API objects and application data models
- Comprehensive error handling for API exceptions

Dependencies:
- smartsheet-python-sdk for API communication
- src.smartsheet.models for data structure conversion
"""

import smartsheet
from src.smartsheet.models import Workspace, Sheet
from typing import List, Dict, Any, Optional


class SmartsheetClient:
    """
    Client for interacting with the Smartsheet API.
    
    This class provides a simplified interface to the Smartsheet API by wrapping
    the official Python SDK. It handles authentication, error management, and
    converts API responses to application-specific data models.
    
    Attributes:
        token (str): The Smartsheet API access token
        client (smartsheet.Smartsheet): The underlying Smartsheet SDK client
    """
    def __init__(self, token):
        """
        Initialize the Smartsheet client with an API token.
        
        Args:
            token (str): Smartsheet Personal Access Token for authentication
                         Can be generated from Smartsheet Account > Personal Settings > API Access
        
        Raises:
            smartsheet.exceptions.SmartsheetException: If token is invalid
        """
        self.token = token
        self.client = smartsheet.Smartsheet(token)
        # Configure SDK to raise exceptions on errors for better error handling
        self.client.errors_as_exceptions(True)
    
    def search_workspaces(self, query="SCM Program") -> List[Dict[str, Any]]:
        """
        Search for workspaces matching the given query.
        
        This method retrieves all workspaces the user has access to and filters them
        by name using a case-insensitive substring match.
        
        Args:
            query (str): The search query to match against workspace names.
                         Defaults to "SCM Program" for common compliance workspaces.
        
        Returns:
            List[Dict[str, Any]]: A list of matching workspace dictionaries with fields:
                - id (int): Workspace ID
                - name (str): Workspace name
                - owner (str, optional): Workspace owner
                - Additional properties from the Smartsheet API
                
        Example:
            >>> client = SmartsheetClient(token)
            >>> workspaces = client.search_workspaces("Compliance")
            >>> print(f"Found {len(workspaces)} matching workspaces")
        """
        try:
            # Get all workspaces
            response = self.client.Workspaces.list_workspaces(include_all=True)
            workspaces = response.data
            
            # Filter workspaces by name (case-insensitive)
            query = query.lower()
            matching_workspaces = [
                workspace for workspace in workspaces 
                if query in workspace.name.lower()
            ]
            
            # Convert to our model objects and then to dictionaries
            return [
                Workspace.from_api_obj(workspace).to_dict() 
                for workspace in matching_workspaces
            ]
        except smartsheet.exceptions.SmartsheetException as e:
            print(f"Error searching workspaces: {e}")
            return []
    
    def get_workspace(self, workspace_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a workspace by ID.
        
        Retrieves detailed information about a specific workspace.
        
        Args:
            workspace_id (int): The ID of the workspace to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: The workspace as a dictionary, or None if not found
                                     or if an error occurred.
        """
        try:
            workspace = self.client.Workspaces.get_workspace(workspace_id)
            return Workspace.from_api_obj(workspace).to_dict()
        except smartsheet.exceptions.SmartsheetException as e:
            print(f"Error retrieving workspace {workspace_id}: {e}")
            return None
    
    def list_sheets(self, workspace_id: int, prefix_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all sheets in a workspace, optionally filtered by a name prefix.
        
        This method retrieves all sheets within a workspace and can filter them
        to only include sheets with names starting with a specific prefix.
        Useful for finding sheets of a particular type or category.
        
        Args:
            workspace_id (int): The ID of the workspace to list sheets from
            prefix_filter (str, optional): If provided, only return sheets
                                         with names starting with this prefix.
                                         For example, "Compliance" to find
                                         all compliance-related sheets.
        
        Returns:
            List[Dict[str, Any]]: A list of sheet dictionaries with fields:
                - id (int): Sheet ID
                - name (str): Sheet name
                - permalink (str): URL to the sheet
                - created_at (str): Creation timestamp
                - modified_at (str): Last modification timestamp
                
        Example:
            >>> client = SmartsheetClient(token)
            >>> sheets = client.list_sheets(workspace_id, "Compensating Controls")
            >>> for sheet in sheets:
            >>>     print(f"Sheet: {sheet['name']}, Modified: {sheet['modified_at']}")
        """
        try:
            # Get all sheets in the workspace
            response = self.client.Workspaces.get_workspace(workspace_id, load_all=True)
            
            # Extract sheet information
            sheets = []
            for sheet in response.sheets:
                # Skip if it doesn't match our prefix filter
                if prefix_filter and not sheet.name.startswith(prefix_filter):
                    continue
                    
                sheets.append(Sheet.from_api_obj(sheet).to_dict())
            
            return sheets
        except smartsheet.exceptions.SmartsheetException as e:
            print(f"Error listing sheets in workspace {workspace_id}: {e}")
            return []
    
    def get_sheet(self, sheet_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the complete details of a specific sheet including columns and rows.
        
        This method retrieves the full sheet data including all columns, rows and cell values.
        It's used to extract the actual compliance data for analysis.
        
        Args:
            sheet_id (int): The ID of the sheet to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The sheet data as a dictionary, or None if not found
                                     or if an error occurred. The dictionary includes:
                - id (int): Sheet ID
                - name (str): Sheet name
                - columns (List[Dict]): Column definitions
                - rows (List[Dict]): Row data with cells
                - Additional metadata
                
        Example:
            >>> client = SmartsheetClient(token)
            >>> sheet_data = client.get_sheet(sheet_id)
            >>> if sheet_data:
            >>>     print(f"Retrieved {len(sheet_data['rows'])} rows from {sheet_data['name']}")
        """
        try:
            sheet = self.client.Sheets.get_sheet(sheet_id)
            return Sheet.from_api_obj(sheet, include_data=True).to_dict()
        except smartsheet.exceptions.SmartsheetException as e:
            print(f"Error retrieving sheet {sheet_id}: {e}")
            return None