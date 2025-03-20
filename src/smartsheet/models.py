"""
Data models for the Smartsheet application.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class Workspace(BaseModel):
    """
    Represents a Smartsheet workspace.
    """
    id: int
    name: str
    owner: Optional[str] = None
    additional_attributes: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def from_api_obj(cls, api_obj):
        """
        Create a Workspace from a Smartsheet API object.
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
    
    def to_dict(self):
        """
        Convert the workspace to a dictionary.
        """
        return {
            'id': self.id,
            'name': self.name,
            'owner': self.owner,
            **self.additional_attributes
        }


class Sheet(BaseModel):
    """
    Represents a Smartsheet sheet.
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
        arbitrary_types_allowed = True
    
    @classmethod
    def from_api_obj(cls, api_obj, include_data=False):
        """
        Create a Sheet from a Smartsheet API object.
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
    
    def to_dict(self):
        """
        Convert the sheet to a dictionary.
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
