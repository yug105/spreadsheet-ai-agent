"""
Superior cell context analyzer - Core intelligence engine
"""

import ast
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .shared_types import (
    SuperiorCellInfo, CellType, DataSemanticType, FormulaComplexity,
    Coordinate, EnhancedEvaluationResult
)
from .formula_parsing import AdvancedFormulaParser
from .evaluation import RealSpreadsheetEvaluator
from .profiling import AdvancedDataProfiler, SemanticTypeDetector

logger = logging.getLogger(__name__)

class SuperiorCellContextAnalyzer:
    """Superior cell context analyzer with comprehensive intelligence"""
    
    def __init__(self):
        # Core components
        self.parser = AdvancedFormulaParser()
        self.evaluator = RealSpreadsheetEvaluator()
        self.profiler = AdvancedDataProfiler()
        self.semantic_detector = SemanticTypeDetector()
        
        # Analysis caches
        self.analysis_cache: Dict[Tuple[Coordinate, str], SuperiorCellInfo] = {}
        
        logger.info("🧠 SuperiorCellContextAnalyzer initialized")
    
    def analyze_cell_comprehensive(self, raw_value: Any, coordinate: Coordinate, 
                                 sheet_name: str, context: Dict[str, Any] = None) -> SuperiorCellInfo:
        """Analyze a cell comprehensively with all available intelligence"""
        
        cache_key = (coordinate, sheet_name)
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # Create base cell info
        cell_info = SuperiorCellInfo(
            coordinate=coordinate,
            a1_address=self._coordinate_to_a1(coordinate),
            sheet_name=sheet_name,
            raw_value=raw_value,
            display_value=str(raw_value) if raw_value is not None else "",
            cell_type=CellType.EMPTY,
            last_modified=datetime.now()
        )
        
        # Determine cell type
        cell_info.cell_type = self._determine_cell_type_advanced(raw_value)
        
        # Analyze semantic type
        cell_info.semantic_type = self.semantic_detector.detect_semantic_type(raw_value)
        
        # Analyze formulas
        if cell_info.cell_type == CellType.FORMULA:
            cell_info = self._analyze_formula_comprehensive(cell_info, context)
        
        # Analyze code cells
        elif cell_info.cell_type in [CellType.CODE_PYTHON, CellType.CODE_JAVASCRIPT]:
            cell_info = self._analyze_code_cell(cell_info, context)
        
        # Analyze security and privacy
        cell_info = self._analyze_security_privacy(cell_info)
        
        # Analyze cell quality
        cell_info = self._analyze_cell_quality(cell_info, context)
        
        # Add contextual information
        if context:
            cell_info = self._add_contextual_information(cell_info, context)
        
        # Cache the result
        self.analysis_cache[cache_key] = cell_info
        
        return cell_info
    
    def _determine_cell_type_advanced(self, value: Any) -> CellType:
        """Advanced cell type determination"""
        
        if value is None or value == "":
            return CellType.EMPTY
        
        if isinstance(value, bool):
            return CellType.BOOLEAN
        
        if isinstance(value, (int, float)):
            return CellType.NUMBER
        
        if isinstance(value, str):
            str_value = value.strip()
            
            # Check for formulas
            if str_value.startswith('='):
                return CellType.FORMULA
            
            # Check for code cells (must come before error detection)
            if str_value.startswith('#PYTHON') or str_value.startswith('#JAVASCRIPT'):
                return CellType.CODE_PYTHON if 'PYTHON' in str_value else CellType.CODE_JAVASCRIPT
            
            # Check for errors
            if str_value.startswith('#') or str_value.startswith('!ERROR'):
                return CellType.ERROR
            
            # Check for hyperlinks
            if str_value.startswith('http://') or str_value.startswith('https://'):
                return CellType.HYPERLINK
            
            # Check for dates/times
            try:
                from datetime import datetime
                datetime.fromisoformat(str_value.replace('Z', '+00:00'))
                return CellType.DATETIME
            except:
                pass
            
            # Check for currency/percentage
            if re.match(r'^\$[\d,]+\.?\d*$', str_value):
                return CellType.CURRENCY
            if re.match(r'^\d+\.?\d*%$', str_value):
                return CellType.PERCENTAGE
            
            # Default to text
            return CellType.TEXT
        
        if isinstance(value, datetime):
            return CellType.DATETIME
        
        return CellType.TEXT
    
    def _analyze_formula_comprehensive(self, cell_info: SuperiorCellInfo, 
                                     context: Dict[str, Any] = None) -> SuperiorCellInfo:
        """Comprehensive formula analysis"""
        
        formula = cell_info.raw_value
        
        # Parse formula
        parse_result = self.parser.parse_formula(formula, context)
        
        # Set formula properties
        cell_info.formula = formula
        cell_info.formula_complexity = parse_result.get('complexity', FormulaComplexity.SIMPLE)
        cell_info.parsed_formula = parse_result
        
        # Set dependencies
        cell_info.direct_dependencies = parse_result.get('dependencies', set())
        cell_info.named_range_dependencies = parse_result.get('named_ranges', set())
        
        # Check for array operations
        if parse_result.get('array_operations', False):
            cell_info.is_array_origin = True
        
        # Evaluate formula if evaluator is available
        if self.evaluator.workbook:
            try:
                eval_result = self.evaluator.evaluate_cell(cell_info.coordinate, cell_info.sheet_name)
                cell_info.evaluation_result = eval_result
                
                # Update dependencies from evaluation
                if eval_result.cells_accessed:
                    cell_info.direct_dependencies.update(eval_result.cells_accessed)
                
            except Exception as e:
                logger.warning(f"Formula evaluation failed for {cell_info.a1_address}: {e}")
        
        return cell_info
    
    def _analyze_code_cell(self, cell_info: SuperiorCellInfo, 
                          context: Dict[str, Any] = None) -> SuperiorCellInfo:
        """Analyze code cells (Python/JavaScript)"""
        
        code = cell_info.raw_value
        
        if cell_info.cell_type == CellType.CODE_PYTHON:
            cell_info = self._analyze_python_code(cell_info)
        elif cell_info.cell_type == CellType.CODE_JAVASCRIPT:
            cell_info = self._analyze_javascript_code(cell_info)
        
        # Evaluate code if evaluator is available
        if self.evaluator.workbook:
            try:
                eval_result = self.evaluator.evaluate_cell(cell_info.coordinate, cell_info.sheet_name)
                cell_info.evaluation_result = eval_result
            except Exception as e:
                logger.warning(f"Code evaluation failed for {cell_info.a1_address}: {e}")
        
        return cell_info
    
    def _analyze_python_code(self, cell_info: SuperiorCellInfo) -> SuperiorCellInfo:
        """Analyze Python code cells"""
        
        code = cell_info.raw_value
        
        # Extract Python code (remove #PYTHON comment)
        if code.startswith('#PYTHON'):
            code = code[7:].strip()
        
        # Parse for dependencies (simplified)
        try:
            tree = ast.parse(code)
            
            class DependencyVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.dependencies = set()
                
                def visit_Name(self, node):
                    # Look for cell references in variable names
                    if re.match(r'^[A-Z]+\d+$', node.id):
                        # Convert A1 to coordinate
                        coord = self._a1_to_coordinate(node.id)
                        if coord:
                            self.dependencies.add(coord)
                    # Don't call super() - just process this node
                
                def _a1_to_coordinate(self, a1_ref: str) -> Optional[Coordinate]:
                    """Convert A1 notation to coordinate"""
                    match = re.match(r'^([A-Z]+)(\d+)$', a1_ref.upper())
                    if match:
                        col_letters, row_str = match.groups()
                        col = 0
                        for char in col_letters:
                            col = col * 26 + (ord(char) - ord('A'))
                        row = int(row_str) - 1
                        return (row, col)
                    return None
            
            visitor = DependencyVisitor()
            visitor.visit(tree)
            cell_info.direct_dependencies.update(visitor.dependencies)
            
        except SyntaxError:
            # Code has syntax errors
            cell_info.validation_errors.append("Python syntax error")
        
        return cell_info
    
    def _analyze_javascript_code(self, cell_info: SuperiorCellInfo) -> SuperiorCellInfo:
        """Analyze JavaScript code cells"""
        
        code = cell_info.raw_value
        
        # Extract JavaScript code (remove #JAVASCRIPT comment)
        if code.startswith('#JAVASCRIPT'):
            code = code[11:].strip()
        
        # Simple dependency extraction for JavaScript
        # This is a simplified implementation
        cell_refs = re.findall(r'\b[A-Z]+\d+\b', code)
        for ref in cell_refs:
            coord = self._a1_to_coordinate(ref)
            if coord:
                cell_info.direct_dependencies.add(coord)
        
        return cell_info
    
    def _analyze_security_privacy(self, cell_info: SuperiorCellInfo) -> SuperiorCellInfo:
        """Analyze security and privacy aspects"""
        
        # Check for PII
        pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
        
        value_str = str(cell_info.raw_value)
        for pii_type, pattern in pii_patterns.items():
            if re.search(pattern, value_str, re.IGNORECASE):
                cell_info.contains_pii = True
                cell_info.sensitivity_level = "confidential"
                cell_info.anomaly_flags.append(f"Contains {pii_type.upper()}")
                break
        
        return cell_info
    
    def _analyze_cell_quality(self, cell_info: SuperiorCellInfo, 
                            context: Dict[str, Any] = None) -> SuperiorCellInfo:
        """Analyze cell quality and anomalies"""
        
        # Basic quality checks
        if cell_info.cell_type == CellType.ERROR:
            cell_info.quality_score = 0.0
            cell_info.anomaly_flags.append("Contains error")
        
        elif cell_info.cell_type == CellType.EMPTY:
            cell_info.quality_score = 0.5  # Neutral for empty cells
        
        else:
            # Calculate quality based on various factors
            quality_score = 1.0
            
            # Penalize for validation errors
            if cell_info.validation_errors:
                quality_score -= 0.3
            
            # Penalize for anomalies
            if cell_info.anomaly_flags:
                quality_score -= 0.2
            
            # Bonus for formulas (they're usually intentional)
            if cell_info.cell_type == CellType.FORMULA:
                quality_score += 0.1
            
            cell_info.quality_score = max(0.0, min(1.0, quality_score))
        
        return cell_info
    
    def _add_contextual_information(self, cell_info: SuperiorCellInfo, 
                                  context: Dict[str, Any]) -> SuperiorCellInfo:
        """Add contextual information to cell analysis"""
        
        # Check if it's a header
        if context.get('is_header', False):
            cell_info.is_header = True
        
        # Check for data region assignment
        if 'data_region_id' in context:
            cell_info.data_region_id = context['data_region_id']
        
        # Check for table information
        if 'table_info' in context:
            cell_info.table_info = context['table_info']
        
        return cell_info
    
    def _coordinate_to_a1(self, coord: Coordinate) -> str:
        """Convert coordinate to A1 notation"""
        
        row, col = coord
        col_str = ""
        temp_col = col
        while temp_col >= 0:
            col_str = chr(ord('A') + temp_col % 26) + col_str
            temp_col = temp_col // 26 - 1
        return f"{col_str}{row + 1}"
    
    def _a1_to_coordinate(self, a1_ref: str) -> Optional[Coordinate]:
        """Convert A1 notation to coordinate"""
        
        match = re.match(r'^([A-Z]+)(\d+)$', a1_ref.upper())
        if match:
            col_letters, row_str = match.groups()
            col = 0
            for char in col_letters:
                col = col * 26 + (ord(char) - ord('A'))
            row = int(row_str) - 1
            return (row, col)
        return None 