"""
Smartsheet Data Models Module

This module defines Pydantic models for representing Smartsheet resources in a 
structured, type-safe way within the application. It handles conversion between 
the raw Smartsheet API objects and application-specific data structures.

Key Components:
- Workspace: Model for Smartsheet workspaces
- Sheet: Model for Smartsheet sheets, including columns and rows

Key Features:
- Consistent data representation across the application
- Type validation through Pydantic
- Conversion utilities for Smartsheet API objects
- Flexible property extraction with error handling
- Standardized dictionary conversion for data interchange

The models provide a clean interface between the Smartsheet API and the 
application's business logic, isolating API-specific details and providing
a consistent structure for downstream processing.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class Workspace(BaseModel):
    """
    Represents a Smartsheet workspace.
    
    A workspace in Smartsheet is a container for organizing related sheets and reports.
    This model provides a structured representation of workspace data and handles
    conversion between raw API objects and application data structures.
    
    Attributes:
        id (int): Unique identifier for the workspace
        name (str): Name of the workspace
        owner (Optional[str]): Owner of the workspace (if available)
        additional_attributes (Dict[str, Any]): Additional properties from the API 
                                              that aren't explicitly modeled
    
    Example:
        >>> workspace = Workspace(id=123456, name="SCM Program - Client XYZ")
        >>> workspace_dict = workspace.to_dict()
    """
    id: int
    name: str
    owner: Optional[str] = None
    additional_attributes: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration options."""
        arbitrary_types_allowed = True
    
    @classmethod
    def from_api_obj(cls, api_obj):
        """
        Create a Workspace instance from a Smartsheet API object.
        
        This method extracts relevant properties from the Smartsheet API object
        and creates a structured Workspace model. It handles potential missing
        attributes and provides a consistent interface regardless of the exact
        structure of the API response.
        
        Args:
            api_obj: A Smartsheet API Workspace object
            
        Returns:
            Workspace: A new Workspace instance with data from the API object
            
        Example:
            >>> api_workspace = client.Workspaces.get_workspace(workspace_id)
            >>> workspace = Workspace.from_api_obj(api_workspace)
        """
        # Extract owner if available 
        owner = getattr(api_obj, 'owner', None)
        
        # Extract base fields
        workspace_dict = {
            'id': api_obj.id,
            'name': api_obj.name,
            'owner': owner,
        }
        
        # Extract additional attributes
        additional_attributes = {}
        for attr in dir(api_obj):
            if not attr.startswith('_') and attr not in workspace_dict:
                try:
                    value = getattr(api_obj, attr)
                    # Only include non-callable attributes
                    if not callable(value):
                        additional_attributes[attr] = value
                except Exception:
                    pass
        
        workspace_dict['additional_attributes'] = additional_attributes
        
        # Create the workspace
        return cls(**workspace_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the workspace model to a dictionary.
        
        Creates a flattened dictionary representation of the workspace,
        including both explicitly modeled fields and additional attributes.
        This format is useful for passing workspace data to other parts
        of the application.
        
        Returns:
            Dict[str, Any]: Dictionary containing all workspace properties
            
        Example:
            >>> workspace_dict = workspace.to_dict()
            >>> workspace_id = workspace_dict['id']
            >>> workspace_name = workspace_dict['name']
        """
        return {
            'id': self.id,
            'name': self.name,
            'owner': self.owner,
            **self.additional_attributes
        }


class Sheet(BaseModel):
    """
    Represents a Smartsheet sheet with its columns and rows.
    
    A sheet in Smartsheet is a grid-like document similar to a spreadsheet.
    This model captures the sheet's metadata along with its structural elements
    (columns and rows) and provides methods to convert between API objects and
    application data structures.
    
    Attributes:
        id (int): Unique identifier for the sheet
        name (str): Name of the sheet
        permalink (Optional[str]): URL link to the sheet in Smartsheet
        created_at (Optional[Union[str, datetime]]): When the sheet was created
        modified_at (Optional[Union[str, datetime]]): When the sheet was last modified
        columns (List[Dict[str, Any]]): List of column definitions with id, title, and type
        rows (List[Dict[str, Any]]): List of rows with cells containing values
        additional_attributes (Dict[str, Any]): Additional properties from the API
                                              that aren't explicitly modeled
    
    Example:
        >>> # Creating a sheet model directly
        >>> sheet = Sheet(id=123456, name="Compensating Controls - Client XYZ")
        >>> 
        >>> # Or from an API object
        >>> api_sheet = client.Sheets.get_sheet(sheet_id)
        >>> sheet = Sheet.from_api_obj(api_sheet, include_data=True)
    """
    id: int
    name: str
    permalink: Optional[str] = None
    created_at: Optional[Union[str, datetime]] = None
    modified_at: Optional[Union[str, datetime]] = None
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    additional_attributes: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration options."""
        arbitrary_types_allowed = True
    
    @classmethod
    def from_api_obj(cls, api_obj, include_data=False):
        """
        Create a Sheet instance from a Smartsheet API object.
        
        This method extracts sheet metadata, and optionally column and row data,
        from a Smartsheet API object. It transforms the nested API structure into
        a flattened, more accessible format for use in the application.
        
        Args:
            api_obj: A Smartsheet API Sheet object
            include_data (bool): Whether to include column and row data.
                                Defaults to False to reduce memory usage when
                                only metadata is needed.
            
        Returns:
            Sheet: A new Sheet instance with data from the API object
            
        Example:
            >>> # Get sheet metadata only
            >>> sheet = Sheet.from_api_obj(api_sheet)
            >>> 
            >>> # Get full sheet data including columns and rows
            >>> detailed_sheet = Sheet.from_api_obj(api_sheet, include_data=True)
        """
        columns = []
        rows = []
        
        # Extract columns and rows if requested and available
        if include_data:
            if hasattr(api_obj, 'columns'):
                columns = [
                    {
                        'id': col.id,
                        'title': col.title,
                        'type': col.type,
                        'index': col.index
                    }
                    for col in api_obj.columns
                ]
            
            if hasattr(api_obj, 'rows'):
                rows = [
                    {
                        'id': row.id,
                        'row_number': row.row_number,
                        'cells': [
                            {
                                'column_id': cell.column_id,
                                'value': cell.value if hasattr(cell, 'value') else None,
                                'display_value': cell.display_value if hasattr(cell, 'display_value') else None
                            }
                            for cell in row.cells
                        ]
                    }
                    for row in api_obj.rows
                ]
        
        # Extract base fields
        sheet_dict = {
            'id': api_obj.id,
            'name': api_obj.name,
            'permalink': getattr(api_obj, 'permalink', None),
            'created_at': getattr(api_obj, 'created_at', None),
            'modified_at': getattr(api_obj, 'modified_at', None),
            'columns': columns,
            'rows': rows,
        }
        
        # Extract additional attributes
        additional_attributes = {}
        for attr in dir(api_obj):
            if not attr.startswith('_') and attr not in sheet_dict:
                try:
                    value = getattr(api_obj, attr)
                    # Only include non-callable attributes
                    if not callable(value):
                        additional_attributes[attr] = value
                except Exception:
                    pass
        
        sheet_dict['additional_attributes'] = additional_attributes
        
        # Create the sheet
        return cls(**sheet_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the sheet model to a dictionary.
        
        Creates a flattened dictionary representation of the sheet,
        including column and row data if present. This format is useful
        for passing sheet data to other parts of the application or for
        serialization.
        
        Returns:
            Dict[str, Any]: Dictionary containing all sheet properties
            
        Example:
            >>> sheet_dict = sheet.to_dict()
            >>> columns = sheet_dict['columns']
            >>> rows = sheet_dict['rows']
            >>> # Find a specific column by title
            >>> client_column = next((col for col in columns if col['title'] == 'CLIENT'), None)
        """
        return {
            'id': self.id,
            'name': self.name,
            'permalink': self.permalink,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'columns': self.columns,
            'rows': self.rows,
            **self.additional_attributes
        }