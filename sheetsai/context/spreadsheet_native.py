"""
Spreadsheet-native data structures - Foundation for Quadratic-level operations
These structures understand spreadsheet concepts natively, not just DataFrames
"""

from typing import Dict, List, Any, Optional, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from .shared_types import (
    SuperiorCellInfo, CellType, DataSemanticType, 
    FormulaComplexity, EnhancedEvaluationResult, NamedRange
)
from sheetsai.a1_notation import ReferenceType
from sheetsai.a1_notation import A1NotationHandler, CellReference, RangeReference

logger = logging.getLogger(__name__)

class SheetChangeType(Enum):
    """Types of changes that can occur in a sheet"""
    CELL_VALUE_CHANGE = "cell_value_change"
    CELL_FORMAT_CHANGE = "cell_format_change"
    FORMULA_CHANGE = "formula_change"
    RANGE_INSERT = "range_insert"
    RANGE_DELETE = "range_delete"
    CHART_ADD = "chart_add"
    CHART_MODIFY = "chart_modify"
    CHART_DELETE = "chart_delete"

@dataclass
class SheetChange:
    """Represents a change to the sheet"""
    change_type: SheetChangeType
    affected_range: str                    # A1 notation
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

# Create a simplified DataRegion class for backward compatibility
@dataclass
class DataRegion:
    """Simplified data region for backward compatibility"""
    region_id: str
    region_type: str = "table"  # Simplified type
    top_left: str = "A1"
    bottom_right: str = "A1"
    total_cells: int = 0
    data_quality_score: float = 1.0
    sample_data: List[Any] = field(default_factory=list)
    suggested_operations: List[str] = field(default_factory=list)
    column_profiles: List[Dict[str, Any]] = field(default_factory=list)
    
class SpreadsheetGrid:
    """
    Native spreadsheet grid that understands cells, ranges, and relationships
    This replaces simple DataFrame thinking with spreadsheet intelligence
    """
    
    def __init__(self, sheet_name: str):
        self.sheet_name = sheet_name
        self.a1_handler = A1NotationHandler()
        
        # Core data storage - updated to use SuperiorCellInfo
        self.cells: Dict[str, SuperiorCellInfo] = {}              # A1 address -> SuperiorCellInfo
        self.data_regions: Dict[str, DataRegion] = {}     # region_id -> DataRegion
        self.named_ranges: Dict[str, NamedRange] = {}     # name -> NamedRange
        
        # Relationships and dependencies
        self.dependency_graph: Dict[str, Set[str]] = {}   # cell -> cells it depends on
        self.dependent_graph: Dict[str, Set[str]] = {}    # cell -> cells that depend on it
        self.spill_ranges: Dict[str, str] = {}            # origin_cell -> spill_range
        
        # Change tracking
        self.change_history: List[SheetChange] = []
        self.last_modified: datetime = datetime.now()
        
        # Metadata
        self.used_range: Optional[RangeReference] = None
        self.sheet_bounds = {"max_row": 1048576, "max_col": 16384}  # Excel limits
    
    def set_cell_value(self, address: str, value: Any, 
                      cell_type: Optional[CellType] = None,
                      formula: Optional[str] = None) -> bool:
        """Set value of a cell with full context tracking"""
        
        try:
            # Parse address
            if not self.a1_handler.is_valid_a1_notation(address):
                raise ValueError(f"Invalid A1 notation: {address}")
            
            row, col = self.a1_handler.from_a1(address)
            coordinate = (row, col)
            
            # Get or create cell info
            old_cell = self.cells.get(address)
            old_value = old_cell.raw_value if old_cell else None
            
            # Determine cell type if not provided
            if cell_type is None:
                cell_type = self._infer_cell_type(value, formula)
            
            # Create new SuperiorCellInfo
            new_cell = SuperiorCellInfo(
                coordinate=coordinate,
                a1_address=address,
                sheet_name=self.sheet_name,
                raw_value=value,
                display_value=str(value) if value is not None else "",
                cell_type=cell_type,
                formula=formula,
                last_modified=datetime.now()
            )
            
            # Handle formula dependencies
            if formula:
                self._update_formula_dependencies(address, formula)
            
            # Update cell
            self.cells[address] = new_cell
            
            # Track change
            self._record_change(SheetChangeType.CELL_VALUE_CHANGE, address, old_value, value)
            
            # Update used range
            self._update_used_range()
            
            # Check for spill effects
            self._check_spill_effects(address, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cell {address}: {e}")
            return False
    
    def get_cell_value(self, address: str) -> Any:
        """Get value of a cell"""
        cell = self.cells.get(address)
        return cell.raw_value if cell else None
    
    def get_cell_info(self, address: str) -> Optional[SuperiorCellInfo]:
        """Get complete cell information"""
        return self.cells.get(address)
    
    def get_range_values(self, range_notation: str) -> Dict[str, Any]:
        """Get values for all cells in a range"""
        try:
            range_ref = self.a1_handler.parse_reference(range_notation)
            if not isinstance(range_ref, RangeReference):
                # Single cell
                return {range_notation: self.get_cell_value(range_notation)}
            
            values = {}
            cells = range_ref.get_all_cells()
            
            for cell_ref in cells:
                values[cell_ref.a1_notation] = self.get_cell_value(cell_ref.a1_notation)
            
            return values
            
        except Exception as e:
            logger.error(f"Error getting range values for {range_notation}: {e}")
            return {}
    
    def set_range_values(self, range_notation: str, values: Union[List[List[Any]], Dict[str, Any]]) -> bool:
        """Set values for a range of cells"""
        try:
            range_ref = self.a1_handler.parse_reference(range_notation)
            
            if isinstance(values, dict):
                # Dictionary mapping addresses to values
                for address, value in values.items():
                    self.set_cell_value(address, value)
            
            elif isinstance(values, list):
                # 2D array of values
                if not isinstance(range_ref, RangeReference):
                    return False
                
                start_row, start_col = range_ref.start_cell.row, range_ref.start_cell.col
                
                for row_idx, row_values in enumerate(values):
                    if not isinstance(row_values, list):
                        row_values = [row_values]
                    
                    for col_idx, value in enumerate(row_values):
                        cell_row = start_row + row_idx
                        cell_col = start_col + col_idx
                        address = self.a1_handler.to_a1(cell_row, cell_col)
                        self.set_cell_value(address, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting range values for {range_notation}: {e}")
            return False
    
    def insert_formula(self, address: str, formula: str) -> bool:
        """Insert a formula at the specified address"""
        return self.set_cell_value(address, None, CellType.FORMULA, formula)
    
    def get_dependencies(self, address: str) -> Set[str]:
        """Get all cells that this cell depends on"""
        return self.dependency_graph.get(address, set())
    
    def get_dependents(self, address: str) -> Set[str]:
        """Get all cells that depend on this cell"""
        return self.dependent_graph.get(address, set())
    
    def find_spill_range(self, origin_address: str) -> Optional[str]:
        """Find the spill range for a given origin cell"""
        return self.spill_ranges.get(origin_address)
    
    def detect_spill_conflicts(self, origin_address: str, proposed_range: str) -> List[str]:
        """Detect cells that would conflict with a proposed spill range"""
        conflicts = []
        
        try:
            range_ref = self.a1_handler.parse_reference(proposed_range)
            if isinstance(range_ref, RangeReference):
                cells = range_ref.get_all_cells()
                
                for cell_ref in cells:
                    if (cell_ref.a1_notation != origin_address and 
                        cell_ref.a1_notation in self.cells and
                        self.cells[cell_ref.a1_notation].raw_value is not None):
                        conflicts.append(cell_ref.a1_notation)
            
        except Exception as e:
            logger.error(f"Error detecting spill conflicts: {e}")
        
        return conflicts
    
    def create_named_range(self, name: str, range_notation: str, description: Optional[str] = None) -> bool:
        """Create a named range"""
        try:
            range_ref = self.a1_handler.parse_reference(range_notation)
            if not isinstance(range_ref, RangeReference):
                # Convert single cell to range
                cell_ref = range_ref
                range_ref = RangeReference(
                    start_cell=cell_ref,
                    end_cell=cell_ref,
                    reference_type=ReferenceType.RANGE,
                    a1_notation=cell_ref.a1_notation
                )
            
            named_range = NamedRange(
                name=name,
                range=(range_ref.start_cell.coordinate, range_ref.end_cell.coordinate),
                description=description
            )
            
            self.named_ranges[name] = named_range
            return True
            
        except Exception as e:
            logger.error(f"Error creating named range {name}: {e}")
            return False
    
    def get_named_range(self, name: str) -> Optional[NamedRange]:
        """Get a named range by name"""
        return self.named_ranges.get(name)
    
    def to_dataframe(self, range_notation: Optional[str] = None, 
                    include_headers: bool = True) -> pd.DataFrame:
        """Convert sheet data to DataFrame for compatibility"""
        
        if range_notation is None:
            # Use entire used range
            if self.used_range is None:
                # If no used range, try to calculate it from cells
                if self.cells:
                    self._update_used_range()
                    if self.used_range is None:
                        return pd.DataFrame()
                else:
                    return pd.DataFrame()
            range_notation = self.used_range.a1_notation
        
        try:
            values = self.get_range_values(range_notation)
            
            if not values:
                return pd.DataFrame()
            
            # Convert to 2D structure
            range_ref = self.a1_handler.parse_reference(range_notation)
            if not isinstance(range_ref, RangeReference):
                # Single cell
                return pd.DataFrame([list(values.values())], columns=['Value'])
            
            # Build 2D array
            rows = range_ref.end_cell.row - range_ref.start_cell.row + 1
            cols = range_ref.end_cell.col - range_ref.start_cell.col + 1
            
            data = []
            for row_idx in range(rows):
                row_data = []
                for col_idx in range(cols):
                    cell_row = range_ref.start_cell.row + row_idx
                    cell_col = range_ref.start_cell.col + col_idx
                    address = self.a1_handler.to_a1(cell_row, cell_col)
                    value = values.get(address, None)
                    row_data.append(value)
                data.append(row_data)
            
            # Create DataFrame
            if include_headers and data:
                headers = data[0]
                data = data[1:]
                return pd.DataFrame(data, columns=headers)
            else:
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Error converting to DataFrame: {e}")
            return pd.DataFrame()
    
    def from_dataframe(self, df: pd.DataFrame, start_address: str = "A1", 
                      include_headers: bool = True) -> bool:
        """Load data from DataFrame into sheet"""
        
        try:
            start_row, start_col = self.a1_handler.from_a1(start_address)
            
            # Insert headers if requested
            if include_headers:
                for col_idx, header in enumerate(df.columns):
                    address = self.a1_handler.to_a1(start_row, start_col + col_idx)
                    self.set_cell_value(address, header, CellType.TEXT)
                start_row += 1
            
            # Insert data
            for row_idx, (_, row) in enumerate(df.iterrows()):
                for col_idx, value in enumerate(row):
                    if pd.isna(value):
                        value = None
                    address = self.a1_handler.to_a1(start_row + row_idx, start_col + col_idx)
                    self.set_cell_value(address, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading from DataFrame: {e}")
            return False
    
    def get_sheet_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of sheet state"""
        
        total_cells = len(self.cells)
        formula_cells = sum(1 for cell in self.cells.values() if cell.cell_type == CellType.FORMULA)
        error_cells = sum(1 for cell in self.cells.values() if cell.cell_type == CellType.ERROR)
        
        return {
            "sheet_name": self.sheet_name,
            "total_cells": total_cells,
            "formula_cells": formula_cells,
            "error_cells": error_cells,
            "data_regions": len(self.data_regions),
            "named_ranges": len(self.named_ranges),
            "spill_ranges": len(self.spill_ranges),
            "used_range": self.used_range.a1_notation if self.used_range else None,
            "last_modified": self.last_modified,
            "change_count": len(self.change_history)
        }
    
    # Internal methods
    
    def _infer_cell_type(self, value: Any, formula: Optional[str]) -> CellType:
        """Infer cell type from value and formula using superior analysis"""
        
        # Delegate to SuperiorCellContextAnalyzer for advanced type detection
        from .core_analyzer import SuperiorCellContextAnalyzer
        
        analyzer = SuperiorCellContextAnalyzer()
        return analyzer._determine_cell_type_advanced(value)
    
    def _update_formula_dependencies(self, address: str, formula: str):
        """Update dependency tracking for a formula cell"""
        
        # Clear old dependencies
        if address in self.dependency_graph:
            old_deps = self.dependency_graph[address]
            for dep in old_deps:
                if dep in self.dependent_graph:
                    self.dependent_graph[dep].discard(address)
        
        # Find new dependencies using superior analysis
        from .core_analyzer import SuperiorCellContextAnalyzer
        
        analyzer = SuperiorCellContextAnalyzer()
        cell_info = analyzer.analyze_cell_comprehensive(
            raw_value=formula,
            coordinate=self.a1_handler.from_a1(address),
            sheet_name=self.sheet_name,
            context={'address': address}
        )
        
        # Convert coordinate dependencies to A1 strings for backward compatibility
        new_deps = set()
        for coord in cell_info.direct_dependencies:
            a1_address = self.a1_handler.to_a1(coord[0], coord[1])
            new_deps.add(a1_address)
        
        # Update dependency graph
        self.dependency_graph[address] = new_deps
        
        # Update dependent graph
        for dep in new_deps:
            if dep not in self.dependent_graph:
                self.dependent_graph[dep] = set()
            self.dependent_graph[dep].add(address)
    
    def _record_change(self, change_type: SheetChangeType, affected_range: str, 
                      old_value: Any, new_value: Any):
        """Record a change to the sheet"""
        
        change = SheetChange(
            change_type=change_type,
            affected_range=affected_range,
            old_value=old_value,
            new_value=new_value
        )
        
        self.change_history.append(change)
        self.last_modified = datetime.now()
        
        # Keep only recent changes (last 1000)
        if len(self.change_history) > 1000:
            self.change_history = self.change_history[-1000:]
    
    def _update_used_range(self):
        """Update the used range of the sheet"""
        
        if not self.cells:
            self.used_range = None
            return
        
        min_row = min(cell.coordinate[0] for cell in self.cells.values())
        max_row = max(cell.coordinate[0] for cell in self.cells.values())
        min_col = min(cell.coordinate[1] for cell in self.cells.values())
        max_col = max(cell.coordinate[1] for cell in self.cells.values())
        
        start_cell = CellReference(
            col=min_col, 
            row=min_row, 
            a1_notation=self.a1_handler.to_a1(min_row, min_col)
        )
        
        end_cell = CellReference(
            col=max_col, 
            row=max_row, 
            a1_notation=self.a1_handler.to_a1(max_row, max_col)
        )
        
        self.used_range = RangeReference(
            start_cell=start_cell,
            end_cell=end_cell,
            reference_type=ReferenceType.RANGE,
            a1_notation=f"{start_cell.a1_notation}:{end_cell.a1_notation}"
        )
    
    def _check_spill_effects(self, address: str, value: Any):
        """Check if setting this cell creates or affects spill ranges"""
        
        # This is a simplified implementation
        # In full version, would check for array formulas and their output ranges
        
        cell = self.cells.get(address)
        if cell and cell.cell_type == CellType.FORMULA:
            # Check if formula might produce array output
            if any(func in cell.formula.upper() for func in ['TRANSPOSE', 'UNIQUE', 'FILTER', 'SORT']):
                # Estimate spill range (simplified)
                estimated_range = f"{address}:{self.a1_handler.to_a1(cell.coordinate[0] + 9, cell.coordinate[1] + 4)}"
                conflicts = self.detect_spill_conflicts(address, estimated_range)
                
                if not conflicts:
                    self.spill_ranges[address] = estimated_range
                else:
                    # Record spill error
                    logger.warning(f"Spill conflict at {address}: {conflicts}")

class SheetCollection:
    """
    Manages multiple spreadsheet grids - like a workbook
    """
    
    def __init__(self, workbook_name: str = "Workbook"):
        self.workbook_name = workbook_name
        self.sheets: Dict[str, SpreadsheetGrid] = {}
        self.active_sheet: Optional[str] = None
        self.sheet_order: List[str] = []
    
    def add_sheet(self, sheet_name: str) -> SpreadsheetGrid:
        """Add a new sheet to the collection"""
        
        if sheet_name in self.sheets:
            raise ValueError(f"Sheet '{sheet_name}' already exists")
        
        sheet = SpreadsheetGrid(sheet_name)
        self.sheets[sheet_name] = sheet
        self.sheet_order.append(sheet_name)
        
        if self.active_sheet is None:
            self.active_sheet = sheet_name
        
        return sheet
    
    def get_sheet(self, sheet_name: str) -> Optional[SpreadsheetGrid]:
        """Get a sheet by name"""
        return self.sheets.get(sheet_name)
    
    def get_active_sheet(self) -> Optional[SpreadsheetGrid]:
        """Get the currently active sheet"""
        if self.active_sheet:
            return self.sheets.get(self.active_sheet)
        return None
    
    def set_active_sheet(self, sheet_name: str) -> bool:
        """Set the active sheet"""
        if sheet_name in self.sheets:
            self.active_sheet = sheet_name
            return True
        return False
    
    def delete_sheet(self, sheet_name: str) -> bool:
        """Delete a sheet"""
        if sheet_name not in self.sheets:
            return False
        
        del self.sheets[sheet_name]
        self.sheet_order.remove(sheet_name)
        
        if self.active_sheet == sheet_name:
            self.active_sheet = self.sheet_order[0] if self.sheet_order else None
        
        return True
    
    def get_workbook_summary(self) -> Dict[str, Any]:
        """Get summary of entire workbook"""
        
        total_cells = sum(len(sheet.cells) for sheet in self.sheets.values())
        total_formulas = sum(
            sum(1 for cell in sheet.cells.values() if cell.cell_type == CellType.FORMULA)
            for sheet in self.sheets.values()
        )
        
        return {
            "workbook_name": self.workbook_name,
            "sheet_count": len(self.sheets),
            "active_sheet": self.active_sheet,
            "total_cells": total_cells,
            "total_formulas": total_formulas,
            "sheet_names": self.sheet_order
        }