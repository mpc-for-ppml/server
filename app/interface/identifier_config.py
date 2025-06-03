# interface/identifier_config.py

from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class IdentifierMode(str, Enum):
    SINGLE = "single"  # Use a single column as identifier
    COMBINED = "combined"  # Combine multiple columns into one identifier


class IdentifierConfig(BaseModel):
    """Configuration for how to identify matching records across parties"""
    mode: IdentifierMode
    columns: List[str]  # List of column names to use as identifiers
    separator: Optional[str] = "_"  # Separator for combined mode
    
    def create_identifier(self, row_data: dict) -> str:
        """Create identifier from row data based on configuration"""
        if self.mode == IdentifierMode.SINGLE:
            if len(self.columns) != 1:
                raise ValueError("Single mode requires exactly one column")
            return str(row_data.get(self.columns[0], ""))
            
        elif self.mode == IdentifierMode.COMBINED:
            # Combine multiple columns with separator
            parts = []
            for col in self.columns:
                value = row_data.get(col, "")
                parts.append(str(value))
            return self.separator.join(parts)
            
        else:
            raise ValueError(f"Unknown identifier mode: {self.mode}")