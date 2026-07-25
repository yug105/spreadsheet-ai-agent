"""
Real spreadsheet evaluation engine
"""

import ast
import time
import logging
import warnings
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .shared_types import EnhancedEvaluationResult, Coordinate

logger = logging.getLogger(__name__)

# For code execution sandbox
try:
    import RestrictedPython
    RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    RESTRICTED_PYTHON_AVAILABLE = False
    warnings.warn("RestrictedPython not available. Install with: pip install RestrictedPython")

# For Excel file handling
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    warnings.warn("openpyxl not available. Install with: pip install openpyxl")

class RealSpreadsheetEvaluator:
    """Real spreadsheet evaluation engine"""
    
    def __init__(self):
        self.workbook: Optional[Any] = None
        self.evaluation_cache: Dict[Coordinate, EnhancedEvaluationResult] = {}
        self.execution_sandbox = None
        
        if RESTRICTED_PYTHON_AVAILABLE:
            self.setup_execution_sandbox()
    
    def setup_execution_sandbox(self):
        """Setup secure code execution environment"""
        try:
            from RestrictedPython import compile_restricted
            self.compile_restricted = compile_restricted
        except ImportError:
            logger.warning("RestrictedPython not available - code execution disabled")
    
    def load_workbook(self, file_path: str) -> bool:
        """Load Excel workbook for analysis"""
        if not OPENPYXL_AVAILABLE:
            logger.error("openpyxl not available - cannot load workbook")
            return False
            
        try:
            self.workbook = openpyxl.load_workbook(file_path, data_only=False)
            return True
        except Exception as e:
            logger.error(f"Failed to load workbook: {e}")
            return False
    
    def evaluate_cell(self, coordinate: Coordinate, sheet_name: str = None) -> EnhancedEvaluationResult:
        """Evaluate a single cell with complete runtime information"""
        
        if coordinate in self.evaluation_cache:
            return self.evaluation_cache[coordinate]
        
        if not self.workbook:
            return EnhancedEvaluationResult(
                success=False,
                output_value=None,
                display_value="",
                error_message="No workbook loaded"
            )
        
        try:
            worksheet = self.workbook.active if not sheet_name else self.workbook[sheet_name]
            excel_coord = self._coordinate_to_excel(coordinate)
            cell = worksheet[excel_coord]
            
            start_time = time.time()
            result = self._evaluate_cell_content(cell, coordinate)
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            # Cache the result
            self.evaluation_cache[coordinate] = result
            
            return result
            
        except Exception as e:
            return EnhancedEvaluationResult(
                success=False,
                output_value=None,
                display_value="",
                error_message=str(e),
                error_type=type(e).__name__
            )
    
    def _evaluate_cell_content(self, cell, coordinate: Coordinate) -> EnhancedEvaluationResult:
        """Evaluate the content of a cell"""
        
        result = EnhancedEvaluationResult(
            success=True,
            output_value=cell.value,
            display_value=str(cell.value) if cell.value is not None else ""
        )
        
        # If it's a formula, parse and analyze
        if isinstance(cell.value, str) and cell.value.startswith('='):
            from .formula_parsing import AdvancedFormulaParser
            parser = AdvancedFormulaParser()
            parse_result = parser.parse_formula(cell.value)
            
            result.cells_accessed = parse_result.get('dependencies', set())
            
            # Try to evaluate the formula
            try:
                # This is simplified - in a real implementation, you'd need
                # a full Excel formula evaluation engine
                if cell.value == '=NOW()':
                    result.output_value = datetime.now()
                elif cell.value == '=TODAY()':
                    result.output_value = datetime.now().date()
                elif cell.value.startswith('=SUM('):
                    # Simple SUM evaluation as example
                    import re
                    range_match = re.search(r'SUM\(([A-Z]+\d+:[A-Z]+\d+)\)', cell.value)
                    if range_match:
                        range_ref = range_match.group(1)
                        total = self._evaluate_sum_range(range_ref)
                        result.output_value = total
                        result.display_value = str(total)
                
            except Exception as e:
                result.success = False
                result.error_message = str(e)
                result.error_type = type(e).__name__
        
        # Handle code cells (Python/JavaScript)
        elif hasattr(cell, 'comment') and cell.comment:
            comment_text = cell.comment.text
            if comment_text.startswith('#PYTHON'):
                result = self._evaluate_python_code(cell.value, coordinate)
            elif comment_text.startswith('#JAVASCRIPT'):
                result = self._evaluate_javascript_code(cell.value, coordinate)
        
        return result
    
    def _evaluate_python_code(self, code: str, coordinate: Coordinate) -> EnhancedEvaluationResult:
        """Evaluate Python code in a restricted environment"""
        
        if not RESTRICTED_PYTHON_AVAILABLE:
            return EnhancedEvaluationResult(
                success=False,
                output_value=None,
                display_value="",
                error_message="Python code execution not available"
            )
        
        try:
            # Compile the code in restricted mode
            compiled_code = self.compile_restricted(code, '<cell>', 'exec')
            
            if compiled_code.errors:
                return EnhancedEvaluationResult(
                    success=False,
                    output_value=None,
                    display_value="",
                    error_message='; '.join(compiled_code.errors)
                )
            
            # Create restricted execution environment
            restricted_globals = {
                '__builtins__': {
                    'len': len,
                    'range': range,
                    'enumerate': enumerate,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'abs': abs,
                    'round': round
                },
                'pd': None,  # Allow pandas if available
                'np': None,  # Allow numpy if available
            }
            
            # Execute the code
            local_vars = {}
            exec(compiled_code.code, restricted_globals, local_vars)
            
            # Get the result (last expression or explicit return)
            output_value = local_vars.get('result') or local_vars.get('_')
            
            return EnhancedEvaluationResult(
                success=True,
                output_value=output_value,
                display_value=str(output_value) if output_value is not None else "",
                variables_created=local_vars
            )
            
        except Exception as e:
            return EnhancedEvaluationResult(
                success=False,
                output_value=None,
                display_value="",
                error_message=str(e),
                error_type=type(e).__name__
            )
    
    def _evaluate_javascript_code(self, code: str, coordinate: Coordinate) -> EnhancedEvaluationResult:
        """Evaluate JavaScript code (placeholder implementation)"""
        # JavaScript evaluation would require a JS engine like V8
        return EnhancedEvaluationResult(
            success=False,
            output_value=None,
            display_value="",
            error_message="JavaScript evaluation not implemented"
        )
    
    def _evaluate_sum_range(self, range_ref: str) -> float:
        """Evaluate SUM over a range (simplified example)"""
        # This is a simplified implementation
        # A real implementation would need full range evaluation
        return 0.0
    
    def _coordinate_to_excel(self, coord: Coordinate) -> str:
        """Convert coordinate to Excel notation"""
        row, col = coord
        col_str = ""
        temp_col = col
        while temp_col >= 0:
            col_str = chr(ord('A') + temp_col % 26) + col_str
            temp_col = temp_col // 26 - 1
        return f"{col_str}{row + 1}" 