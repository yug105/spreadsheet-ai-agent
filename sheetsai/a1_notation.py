"""
Complete A1 Notation Handler - Fixed Implementation
Addresses the missing _parse_by_type method and incomplete functionality
"""

import re
from typing import Dict, List, Any, Optional, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ReferenceType(Enum):
    """Types of cell/range references"""
    CELL = "cell"
    RANGE = "range" 
    COLUMN = "column"
    ROW = "row"
    NAMED_RANGE = "named_range"
    TABLE_REFERENCE = "table_reference"

@dataclass
class CellReference:
    """Represents a single cell reference"""
    col: int
    row: int
    a1_notation: str
    sheet_name: Optional[str] = None
    is_absolute_col: bool = False
    is_absolute_row: bool = False
    reference_type: ReferenceType = ReferenceType.CELL
    
    def to_string(self) -> str:
        """Convert to string representation"""
        prefix = f"'{self.sheet_name}'!" if self.sheet_name else ""
        col_prefix = "$" if self.is_absolute_col else ""
        row_prefix = "$" if self.is_absolute_row else ""
        return f"{prefix}{col_prefix}{self._col_to_letter(self.col)}{row_prefix}{self.row + 1}"
    
    def _col_to_letter(self, col: int) -> str:
        """Convert column index to letter(s)"""
        result = ""
        col += 1  # Make 1-based
        while col > 0:
            col -= 1
            result = chr(ord('A') + (col % 26)) + result
            col //= 26
        return result

@dataclass
class RangeReference:
    """Represents a range reference"""
    start_cell: CellReference
    end_cell: CellReference
    reference_type: ReferenceType
    a1_notation: str
    sheet_name: Optional[str] = None
    
    def get_all_cells(self) -> List[CellReference]:
        """Get all individual cells in this range"""
        cells = []
        
        for row in range(self.start_cell.row, self.end_cell.row + 1):
            for col in range(self.start_cell.col, self.end_cell.col + 1):
                cell = CellReference(
                    col=col,
                    row=row,
                    a1_notation=A1NotationHandler.to_a1(row, col),
                    sheet_name=self.sheet_name
                )
                cells.append(cell)
        
        return cells
    
    def contains_cell(self, cell_ref: CellReference) -> bool:
        """Check if this range contains the given cell"""
        return (self.start_cell.row <= cell_ref.row <= self.end_cell.row and
                self.start_cell.col <= cell_ref.col <= self.end_cell.col)
    
    def overlaps_with(self, other_range: 'RangeReference') -> bool:
        """Check if this range overlaps with another range"""
        return not (self.end_cell.row < other_range.start_cell.row or
                   self.start_cell.row > other_range.end_cell.row or
                   self.end_cell.col < other_range.start_cell.col or
                   self.start_cell.col > other_range.end_cell.col)

class A1NotationHandler:
    """Comprehensive A1 notation handler with complete functionality"""
    
    def __init__(self):
        # Patterns for different types of references
        self.patterns = {
            'cell': r'^(\$?[A-Z]+)(\$?\d+)$',                    # A1, $A$1, etc.
            'range': r'^(\$?[A-Z]+)(\$?\d+):(\$?[A-Z]+)(\$?\d+)$',  # A1:B10
            'column': r'^(\$?[A-Z]+):(\$?[A-Z]+)$',              # A:A, A:C
            'row': r'^(\$?\d+):(\$?\d+)$',                       # 1:1, 1:10
            'sheet_cell': r'^([^!]+)!(\$?[A-Z]+)(\$?\d+)$',      # Sheet1!A1
            'sheet_range': r'^([^!]+)!(\$?[A-Z]+)(\$?\d+):(\$?[A-Z]+)(\$?\d+)$', # Sheet1!A1:B10
            'named_range': r'^[A-Za-z_][A-Za-z0-9_]*$',          # MyRange
            'table_ref': r'^([A-Za-z_][A-Za-z0-9_]*)\[([^\]]+)\]$'  # Table1[Column1]
        }
    
    @staticmethod
    def to_a1(row: int, col: int) -> str:
        """Convert 0-based row/col to A1 notation"""
        if row < 0 or col < 0:
            raise ValueError(f"Row and column must be non-negative, got row={row}, col={col}")
        
        col_letter = ""
        col_num = col + 1  # Make 1-based
        
        while col_num > 0:
            col_num -= 1
            col_letter = chr(ord('A') + (col_num % 26)) + col_letter
            col_num //= 26
        
        return f"{col_letter}{row + 1}"
    
    @staticmethod
    def from_a1(a1_notation: str) -> Tuple[int, int]:
        """Convert A1 notation to 0-based row/col"""
        a1_notation = a1_notation.strip().upper()
        
        # Remove $ signs for absolute references
        a1_notation = a1_notation.replace('$', '')
        
        # Extract column letters and row number
        match = re.match(r'^([A-Z]+)(\d+)$', a1_notation)
        if not match:
            raise ValueError(f"Invalid A1 notation: {a1_notation}")
        
        col_letters, row_str = match.groups()
        
        # Convert column letters to number
        col = 0
        for letter in col_letters:
            col = col * 26 + (ord(letter) - ord('A') + 1)
        col -= 1  # Make 0-based
        
        # Convert row to 0-based
        row = int(row_str) - 1
        
        return row, col
    
    def parse_reference(self, reference: str) -> Union[CellReference, RangeReference]:
        """Parse any type of cell/range reference - COMPLETE IMPLEMENTATION"""
        reference = reference.strip()
        
        # Try each pattern type
        for ref_type, pattern in self.patterns.items():
            match = re.match(pattern, reference, re.IGNORECASE)
            if match:
                return self._parse_by_type(ref_type, reference, match)
        
        raise ValueError(f"Could not parse reference: {reference}")
    
    def _parse_by_type(self, ref_type: str, reference: str, match) -> Union[CellReference, RangeReference]:
        """Parse reference by type - IMPLEMENTATION WAS MISSING"""
        
        if ref_type == 'cell':
            return self._parse_cell(reference, match)
        elif ref_type == 'range':
            return self._parse_range(reference, match)
        elif ref_type == 'column':
            return self._parse_column_range(reference, match)
        elif ref_type == 'row':
            return self._parse_row_range(reference, match)
        elif ref_type == 'sheet_cell':
            return self._parse_sheet_cell(reference, match)
        elif ref_type == 'sheet_range':
            return self._parse_sheet_range(reference, match)
        elif ref_type == 'named_range':
            return self._parse_named_range(reference, match)
        elif ref_type == 'table_ref':
            return self._parse_table_reference(reference, match)
        else:
            raise ValueError(f"Unknown reference type: {ref_type}")
    
    def _parse_cell(self, reference: str, match) -> CellReference:
        """Parse single cell reference"""
        col_str, row_str = match.groups()
        
        # Check for absolute references
        is_absolute_col = col_str.startswith('$')
        is_absolute_row = row_str.startswith('$')
        
        # Remove $ signs and convert
        col_str = col_str.replace('$', '')
        row_str = row_str.replace('$', '')
        
        row, col = self.from_a1(f"{col_str}{row_str}")
        
        return CellReference(
            col=col,
            row=row,
            a1_notation=reference,
            is_absolute_col=is_absolute_col,
            is_absolute_row=is_absolute_row,
            reference_type=ReferenceType.CELL
        )
    
    def _parse_range(self, reference: str, match) -> RangeReference:
        """Parse range reference (A1:B10)"""
        start_col, start_row, end_col, end_row = match.groups()
        
        # Parse start and end cells
        start_cell = self._parse_cell(f"{start_col}{start_row}", 
                                    re.match(self.patterns['cell'], f"{start_col}{start_row}"))
        end_cell = self._parse_cell(f"{end_col}{end_row}",
                                  re.match(self.patterns['cell'], f"{end_col}{end_row}"))
        
        return RangeReference(
            start_cell=start_cell,
            end_cell=end_cell,
            reference_type=ReferenceType.RANGE,
            a1_notation=reference
        )
    
    def _parse_column_range(self, reference: str, match) -> RangeReference:
        """Parse column range (A:A, A:C)"""
        start_col, end_col = match.groups()
        
        # Convert column letters to indices
        _, start_col_idx = self.from_a1(f"{start_col.replace('$', '')}1")
        _, end_col_idx = self.from_a1(f"{end_col.replace('$', '')}1")
        
        # Create range covering entire columns
        start_cell = CellReference(col=start_col_idx, row=0, a1_notation=f"{start_col}1")
        end_cell = CellReference(col=end_col_idx, row=1048575, a1_notation=f"{end_col}1048576")  # Excel max
        
        return RangeReference(
            start_cell=start_cell,
            end_cell=end_cell,
            reference_type=ReferenceType.COLUMN,
            a1_notation=reference
        )
    
    def _parse_row_range(self, reference: str, match) -> RangeReference:
        """Parse row range (1:1, 1:10)"""
        start_row, end_row = match.groups()
        
        start_row_idx = int(start_row.replace('$', '')) - 1  # 0-based
        end_row_idx = int(end_row.replace('$', '')) - 1
        
        # Create range covering entire rows
        start_cell = CellReference(col=0, row=start_row_idx, a1_notation=f"A{start_row}")
        end_cell = CellReference(col=16383, row=end_row_idx, a1_notation=f"XFD{end_row}")  # Excel max
        
        return RangeReference(
            start_cell=start_cell,
            end_cell=end_cell,
            reference_type=ReferenceType.ROW,
            a1_notation=reference
        )
    
    def _parse_sheet_cell(self, reference: str, match) -> CellReference:
        """Parse sheet-qualified cell reference"""
        sheet_name, col_str, row_str = match.groups()
        
        # Remove quotes from sheet name if present
        if sheet_name.startswith("'") and sheet_name.endswith("'"):
            sheet_name = sheet_name[1:-1]
        
        cell_ref = self._parse_cell(f"{col_str}{row_str}",
                                  re.match(self.patterns['cell'], f"{col_str}{row_str}"))
        cell_ref.sheet_name = sheet_name
        
        return cell_ref
    
    def _parse_sheet_range(self, reference: str, match) -> RangeReference:
        """Parse sheet-qualified range reference"""
        sheet_name, start_col, start_row, end_col, end_row = match.groups()
        
        # Remove quotes from sheet name if present
        if sheet_name.startswith("'") and sheet_name.endswith("'"):
            sheet_name = sheet_name[1:-1]
        
        range_ref = self._parse_range(f"{start_col}{start_row}:{end_col}{end_row}",
                                    re.match(self.patterns['range'], f"{start_col}{start_row}:{end_col}{end_row}"))
        range_ref.sheet_name = sheet_name
        
        return range_ref
    
    def _parse_named_range(self, reference: str, match) -> CellReference:
        """Parse named range reference"""
        return CellReference(
            col=0,  # Placeholder - would need to resolve from spreadsheet
            row=0,
            a1_notation=reference,
            reference_type=ReferenceType.NAMED_RANGE
        )
    
    def _parse_table_reference(self, reference: str, match) -> CellReference:
        """Parse table reference (Table1[Column1])"""
        table_name, column_spec = match.groups()
        
        return CellReference(
            col=0,  # Placeholder - would need to resolve from spreadsheet
            row=0,
            a1_notation=reference,
            reference_type=ReferenceType.TABLE_REFERENCE
        )
    
    def is_valid_a1_notation(self, notation: str) -> bool:
        """Check if a string is valid A1 notation"""
        try:
            self.parse_reference(notation)
            return True
        except (ValueError, Exception):
            return False
    
    def expand_range(self, range_ref: Union[str, RangeReference]) -> List[CellReference]:
        """Expand a range to individual cell references"""
        if isinstance(range_ref, str):
            range_ref = self.parse_reference(range_ref)
        
        if isinstance(range_ref, CellReference):
            return [range_ref]
        
        return range_ref.get_all_cells()
    
    def offset_reference(self, ref: Union[CellReference, RangeReference], 
                        row_offset: int, col_offset: int) -> Union[CellReference, RangeReference]:
        """Offset a reference by given rows and columns"""
        if isinstance(ref, CellReference):
            new_row = max(0, ref.row + row_offset)
            new_col = max(0, ref.col + col_offset)
            
            return CellReference(
                col=new_col,
                row=new_row,
                a1_notation=self.to_a1(new_row, new_col),
                sheet_name=ref.sheet_name,
                is_absolute_col=ref.is_absolute_col,
                is_absolute_row=ref.is_absolute_row,
                reference_type=ref.reference_type
            )
        
        elif isinstance(ref, RangeReference):
            new_start = self.offset_reference(ref.start_cell, row_offset, col_offset)
            new_end = self.offset_reference(ref.end_cell, row_offset, col_offset)
            
            return RangeReference(
                start_cell=new_start,
                end_cell=new_end,
                reference_type=ref.reference_type,
                a1_notation=f"{new_start.a1_notation}:{new_end.a1_notation}",
                sheet_name=ref.sheet_name
            )

class RangeAnalyzer:
    """Analyzes ranges for relationships and patterns"""
    
    def __init__(self):
        self.a1_handler = A1NotationHandler()
    
    def find_adjacent_ranges(self, range1: RangeReference, range2: RangeReference) -> bool:
        """Check if two ranges are adjacent (touching but not overlapping)"""
        
        # Check if they're adjacent horizontally
        if (range1.start_cell.row == range2.start_cell.row and 
            range1.end_cell.row == range2.end_cell.row):
            
            # range1 is to the left of range2
            if range1.end_cell.col + 1 == range2.start_cell.col:
                return True
            
            # range2 is to the left of range1
            if range2.end_cell.col + 1 == range1.start_cell.col:
                return True
        
        # Check if they're adjacent vertically
        if (range1.start_cell.col == range2.start_cell.col and
            range1.end_cell.col == range2.end_cell.col):
            
            # range1 is above range2
            if range1.end_cell.row + 1 == range2.start_cell.row:
                return True
            
            # range2 is above range1
            if range2.end_cell.row + 1 == range1.start_cell.row:
                return True
        
        return False
    
    def merge_ranges(self, ranges: List[RangeReference]) -> List[RangeReference]:
        """Merge overlapping ranges"""
        if not ranges:
            return []
        
        # Sort ranges by start position
        sorted_ranges = sorted(ranges, key=lambda r: (r.start_cell.row, r.start_cell.col))
        merged = [sorted_ranges[0]]
        
        for current in sorted_ranges[1:]:
            last_merged = merged[-1]
            
            if last_merged.overlaps_with(current):
                # Merge ranges
                new_start_row = min(last_merged.start_cell.row, current.start_cell.row)
                new_start_col = min(last_merged.start_cell.col, current.start_cell.col)
                new_end_row = max(last_merged.end_cell.row, current.end_cell.row)
                new_end_col = max(last_merged.end_cell.col, current.end_cell.col)
                
                merged_range = RangeReference(
                    start_cell=CellReference(new_start_col, new_start_row, 
                                           A1NotationHandler.to_a1(new_start_row, new_start_col)),
                    end_cell=CellReference(new_end_col, new_end_row,
                                         A1NotationHandler.to_a1(new_end_row, new_end_col)),
                    reference_type=ReferenceType.RANGE,
                    a1_notation=f"{A1NotationHandler.to_a1(new_start_row, new_start_col)}:{A1NotationHandler.to_a1(new_end_row, new_end_col)}"
                )
                
                merged[-1] = merged_range
            else:
                merged.append(current)
        
        return merged

# Error classes for A1 notation
class A1NotationError(Exception):
    """Base exception for A1 notation errors"""
    pass

class InvalidCellReferenceError(A1NotationError):
    """Raised when cell reference is invalid"""
    pass

class InvalidRangeError(A1NotationError):
    """Raised when range reference is invalid"""
    pass