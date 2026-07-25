"""
Advanced Formula Parsing System - Complete Implementation
This was missing from the original codebase and is critical for formula analysis
"""

import re
import ast
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Assuming these are available from shared_types
from .shared_types import FormulaComplexity, Coordinate, StructuredReference

logger = logging.getLogger(__name__)

class FunctionCategory(Enum):
    """Categories of Excel/Google Sheets functions"""
    MATH = "math"
    STATISTICAL = "statistical"
    LOOKUP = "lookup"
    TEXT = "text"
    DATE_TIME = "date_time"
    LOGICAL = "logical"
    FINANCIAL = "financial"
    INFORMATION = "information"
    DATABASE = "database"
    ARRAY = "array"
    VOLATILE = "volatile"
    CUSTOM = "custom"

@dataclass
class ParsedFormula:
    """Complete parsed formula information"""
    original_formula: str
    functions_used: List[str] = field(default_factory=list)
    function_categories: Set[FunctionCategory] = field(default_factory=set)
    cell_dependencies: Set[Coordinate] = field(default_factory=set)
    range_dependencies: Set[str] = field(default_factory=set)
    named_range_dependencies: Set[str] = field(default_factory=set)
    structured_references: Set[StructuredReference] = field(default_factory=set)
    cross_sheet_references: List[str] = field(default_factory=list)
    complexity: FormulaComplexity = FormulaComplexity.SIMPLE
    complexity_score: float = 0.0
    is_array_formula: bool = False
    is_volatile: bool = False
    has_circular_potential: bool = False
    nesting_level: int = 0
    estimated_calc_time: float = 0.0
    potential_errors: List[str] = field(default_factory=list)
    parse_timestamp: datetime = field(default_factory=datetime.now)

class AdvancedFormulaParser:
    """Advanced formula parser with comprehensive analysis capabilities"""
    
    def __init__(self):
        # Function categorization
        self.function_categories = {
            FunctionCategory.MATH: {
                'SUM', 'AVERAGE', 'COUNT', 'MAX', 'MIN', 'ROUND', 'ABS', 'SQRT',
                'POWER', 'MOD', 'CEILING', 'FLOOR', 'PRODUCT', 'SUMPRODUCT',
                'SUMIF', 'SUMIFS', 'COUNTIF', 'COUNTIFS', 'AVERAGEIF', 'AVERAGEIFS'
            },
            FunctionCategory.STATISTICAL: {
                'STDEV', 'VAR', 'MEDIAN', 'MODE', 'PERCENTILE', 'QUARTILE',
                'CORREL', 'COVAR', 'SLOPE', 'INTERCEPT', 'RSQ', 'FORECAST'
            },
            FunctionCategory.LOOKUP: {
                'VLOOKUP', 'HLOOKUP', 'INDEX', 'MATCH', 'LOOKUP', 'XLOOKUP',
                'CHOOSE', 'OFFSET', 'INDIRECT'
            },
            FunctionCategory.TEXT: {
                'CONCATENATE', 'CONCAT', 'LEFT', 'RIGHT', 'MID', 'LEN', 
                'FIND', 'SEARCH', 'SUBSTITUTE', 'REPLACE', 'UPPER', 'LOWER',
                'PROPER', 'TRIM', 'TEXT', 'VALUE'
            },
            FunctionCategory.DATE_TIME: {
                'TODAY', 'NOW', 'DATE', 'TIME', 'YEAR', 'MONTH', 'DAY',
                'HOUR', 'MINUTE', 'SECOND', 'WEEKDAY', 'DATEDIF', 'WORKDAY'
            },
            FunctionCategory.LOGICAL: {
                'IF', 'IFS', 'AND', 'OR', 'NOT', 'TRUE', 'FALSE', 'IFERROR',
                'IFNA', 'SWITCH'
            },
            FunctionCategory.ARRAY: {
                'FILTER', 'SORT', 'UNIQUE', 'SEQUENCE', 'TRANSPOSE', 'FLATTEN',
                'ARRAYFORMULA', 'SPLIT'
            },
            FunctionCategory.VOLATILE: {
                'NOW', 'TODAY', 'RAND', 'RANDBETWEEN', 'INDIRECT', 'OFFSET'
            },
            FunctionCategory.FINANCIAL: {
                'NPV', 'IRR', 'PMT', 'PV', 'FV', 'RATE', 'NPER', 'XIRR', 'XNPV'
            }
        }
        
        # Reverse mapping for quick lookup
        self.function_to_category = {}
        for category, functions in self.function_categories.items():
            for func in functions:
                self.function_to_category[func] = category
        
        # Complexity weights
        self.complexity_weights = {
            FunctionCategory.MATH: 1.0,
            FunctionCategory.STATISTICAL: 1.5,
            FunctionCategory.LOOKUP: 2.0,
            FunctionCategory.TEXT: 1.0,
            FunctionCategory.DATE_TIME: 1.2,
            FunctionCategory.LOGICAL: 1.5,
            FunctionCategory.ARRAY: 3.0,
            FunctionCategory.VOLATILE: 2.5,
            FunctionCategory.FINANCIAL: 2.0
        }
        
        # Regex patterns
        self.patterns = {
            'functions': r'([A-Z_][A-Z0-9_]*)\s*\(',
            'cell_refs': r'\b([A-Z]+[0-9]+)\b',
            'range_refs': r'\b([A-Z]+[0-9]+:[A-Z]+[0-9]+)\b',
            'sheet_refs': r"(?:'([^']+)'|([A-Za-z0-9_]+))!",
            'named_ranges': r'\b([A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()',
            'structured_refs': r'(\w+)\[([^\]]+)\]',
            'string_literals': r'"([^"]*)"',
            'numeric_literals': r'\b\d+(?:\.\d+)?\b'
        }
    
    def parse_formula(self, formula: str) -> ParsedFormula:
        """Main entry point for formula parsing"""
        
        if not formula or not formula.startswith('='):
            return ParsedFormula(original_formula=formula)
        
        # Remove the = sign
        formula_body = formula[1:].strip()
        
        result = ParsedFormula(original_formula=formula)
        
        try:
            # Parse different components
            result.functions_used = self._extract_functions(formula_body)
            result.function_categories = self._categorize_functions(result.functions_used)
            result.cell_dependencies = self._extract_cell_references(formula_body)
            result.range_dependencies = self._extract_range_references(formula_body)
            result.cross_sheet_references = self._extract_sheet_references(formula_body)
            result.structured_references = self._extract_structured_references(formula_body)
            result.named_range_dependencies = self._extract_named_ranges(formula_body)
            
            # Analysis
            result.nesting_level = self._calculate_nesting_level(formula_body)
            result.is_volatile = self._check_volatility(result.functions_used)
            result.is_array_formula = self._check_array_formula(result.functions_used)
            result.complexity = self._determine_complexity(result)
            result.complexity_score = self._calculate_complexity_score(result)
            result.estimated_calc_time = self._estimate_calculation_time(result)
            result.potential_errors = self._identify_potential_errors(formula_body, result)
            
        except Exception as e:
            logger.error(f"Error parsing formula {formula}: {e}")
            result.potential_errors.append(f"Parse error: {str(e)}")
        
        return result
    
    def _extract_functions(self, formula: str) -> List[str]:
        """Extract all function names from formula"""
        # Remove string literals first to avoid false matches
        formula_no_strings = re.sub(self.patterns['string_literals'], '', formula)
        
        # Find all function patterns
        functions = re.findall(self.patterns['functions'], formula_no_strings, re.IGNORECASE)
        
        # Convert to uppercase and remove duplicates while preserving order
        seen = set()
        result = []
        for func in functions:
            func_upper = func.upper()
            if func_upper not in seen:
                seen.add(func_upper)
                result.append(func_upper)
        
        return result
    
    def _categorize_functions(self, functions: List[str]) -> Set[FunctionCategory]:
        """Categorize functions by type"""
        categories = set()
        
        for func in functions:
            category = self.function_to_category.get(func, FunctionCategory.CUSTOM)
            categories.add(category)
        
        return categories
    
    def _extract_cell_references(self, formula: str) -> Set[Coordinate]:
        """Extract individual cell references"""
        # Remove string literals and range references first
        formula_no_strings = re.sub(self.patterns['string_literals'], '', formula)
        formula_no_ranges = re.sub(self.patterns['range_refs'], '', formula_no_strings)
        
        cell_refs = re.findall(self.patterns['cell_refs'], formula_no_ranges)
        
        coordinates = set()
        for ref in cell_refs:
            try:
                row, col = self._a1_to_coordinate(ref)
                coordinates.add((row, col))
            except ValueError:
                continue  # Skip invalid references
        
        return coordinates
    
    def _extract_range_references(self, formula: str) -> Set[str]:
        """Extract range references"""
        # Remove string literals first
        formula_no_strings = re.sub(self.patterns['string_literals'], '', formula)
        
        ranges = re.findall(self.patterns['range_refs'], formula_no_strings)
        return set(ranges)
    
    def _extract_sheet_references(self, formula: str) -> List[str]:
        """Extract cross-sheet references"""
        # Remove string literals first
        formula_no_strings = re.sub(self.patterns['string_literals'], '', formula)
        
        sheet_matches = re.findall(self.patterns['sheet_refs'], formula_no_strings)
        
        sheets = []
        for match in sheet_matches:
            # match is a tuple of (quoted_name, unquoted_name)
            sheet_name = match[0] if match[0] else match[1]
            if sheet_name:
                sheets.append(sheet_name)
        
        return sheets
    
    def _extract_structured_references(self, formula: str) -> Set[StructuredReference]:
        """Extract structured table references"""
        # Remove string literals first
        formula_no_strings = re.sub(self.patterns['string_literals'], '', formula)
        
        structured_matches = re.findall(self.patterns['structured_refs'], formula_no_strings)
        
        references = set()
        for table_name, column_spec in structured_matches:
            references.add(StructuredReference(
                table_name=table_name,
                column_name=column_spec
            ))
        
        return references
    
    def _extract_named_ranges(self, formula: str) -> Set[str]:
        """Extract named range references"""
        # This is simplified - would need access to actual named ranges in spreadsheet
        # Remove string literals and function names first
        formula_no_strings = re.sub(self.patterns['string_literals'], '', formula)
        formula_no_functions = re.sub(self.patterns['functions'], '', formula_no_strings)
        
        # Find potential named ranges (words that aren't cell references)
        potential_names = re.findall(self.patterns['named_ranges'], formula_no_functions)
        
        # Filter out known functions and cell references
        named_ranges = set()
        for name in potential_names:
            name_upper = name.upper()
            if (name_upper not in self.function_to_category and 
                not re.match(r'^[A-Z]+[0-9]+$', name_upper)):
                named_ranges.add(name)
        
        return named_ranges
    
    def _calculate_nesting_level(self, formula: str) -> int:
        """Calculate maximum nesting level of parentheses"""
        max_level = 0
        current_level = 0
        
        in_string = False
        for char in formula:
            if char == '"':
                in_string = not in_string
            elif not in_string:
                if char == '(':
                    current_level += 1
                    max_level = max(max_level, current_level)
                elif char == ')':
                    current_level -= 1
        
        return max_level
    
    def _check_volatility(self, functions: List[str]) -> bool:
        """Check if formula contains volatile functions"""
        volatile_functions = self.function_categories[FunctionCategory.VOLATILE]
        return any(func in volatile_functions for func in functions)
    
    def _check_array_formula(self, functions: List[str]) -> bool:
        """Check if formula is an array formula"""
        array_functions = self.function_categories[FunctionCategory.ARRAY]
        return any(func in array_functions for func in functions)
    
    def _determine_complexity(self, parsed: ParsedFormula) -> FormulaComplexity:
        """Determine overall formula complexity"""
        
        # Count factors
        func_count = len(parsed.functions_used)
        dep_count = len(parsed.cell_dependencies) + len(parsed.range_dependencies)
        
        # Check for complex patterns
        if parsed.is_array_formula or parsed.nesting_level > 4:
            return FormulaComplexity.EXPERT
        
        if (FunctionCategory.ARRAY in parsed.function_categories or 
            FunctionCategory.VOLATILE in parsed.function_categories):
            return FormulaComplexity.EXPERT
        
        if (func_count > 3 or any(func in ['VLOOKUP', 'INDEX', 'MATCH', 'INDIRECT'] 
                                 for func in parsed.functions_used)):
            return FormulaComplexity.ADVANCED
        
        if func_count > 1 or dep_count > 5 or parsed.nesting_level > 2:
            return FormulaComplexity.INTERMEDIATE
        
        if func_count > 0 or dep_count > 1:
            return FormulaComplexity.BASIC
        
        return FormulaComplexity.SIMPLE
    
    def _calculate_complexity_score(self, parsed: ParsedFormula) -> float:
        """Calculate numerical complexity score"""
        score = 0.0
        
        # Base scores
        score += len(parsed.functions_used) * 1.0
        score += len(parsed.cell_dependencies) * 0.1
        score += len(parsed.range_dependencies) * 0.5
        score += parsed.nesting_level * 0.5
        
        # Category weights
        for category in parsed.function_categories:
            score += self.complexity_weights.get(category, 1.0)
        
        # Special cases
        if parsed.is_volatile:
            score *= 1.5
        if parsed.is_array_formula:
            score *= 2.0
        if len(parsed.cross_sheet_references) > 0:
            score *= 1.2
        
        return score
    
    def _estimate_calculation_time(self, parsed: ParsedFormula) -> float:
        """Estimate calculation time in milliseconds"""
        # This is a rough estimation based on complexity
        base_time = 0.1  # 0.1ms base
        
        # Function overhead
        time = base_time + len(parsed.functions_used) * 0.05
        
        # Data access overhead
        time += len(parsed.cell_dependencies) * 0.01
        time += len(parsed.range_dependencies) * 0.1
        
        # Complexity multipliers
        complexity_multipliers = {
            FormulaComplexity.SIMPLE: 1.0,
            FormulaComplexity.BASIC: 1.2,
            FormulaComplexity.INTERMEDIATE: 1.5,
            FormulaComplexity.ADVANCED: 2.0,
            FormulaComplexity.EXPERT: 3.0
        }
        
        time *= complexity_multipliers.get(parsed.complexity, 1.0)
        
        # Special cases
        if parsed.is_volatile:
            time *= 1.3
        if parsed.is_array_formula:
            time *= 2.0
        
        return time
    
    def _identify_potential_errors(self, formula: str, parsed: ParsedFormula) -> List[str]:
        """Identify potential errors in formula"""
        errors = []
        
        # Check for common error patterns
        if 'VLOOKUP' in parsed.functions_used and 'FALSE' not in formula:
            errors.append("VLOOKUP without exact match might cause errors")
        
        if 'INDIRECT' in parsed.functions_used:
            errors.append("INDIRECT function can cause #REF! errors if reference is invalid")
        
        if parsed.nesting_level > 7:
            errors.append("Deep nesting may cause performance issues")
        
        # Check for division by zero potential
        if '/' in formula and any(func in parsed.functions_used for func in ['IF', 'IFS']):
            errors.append("Potential division by zero - consider error handling")
        
        # Check for circular reference potential
        if 'INDIRECT' in parsed.functions_used or 'OFFSET' in parsed.functions_used:
            errors.append("Functions like INDIRECT/OFFSET may cause circular references")
        
        return errors
    
    def _a1_to_coordinate(self, a1_ref: str) -> Tuple[int, int]:
        """Convert A1 notation to coordinate tuple"""
        # Remove $ symbols for absolute references
        a1_clean = a1_ref.replace('$', '')
        
        # Extract column letters and row number
        match = re.match(r'^([A-Z]+)([0-9]+)$', a1_clean.upper())
        if not match:
            raise ValueError(f"Invalid A1 reference: {a1_ref}")
        
        col_letters, row_str = match.groups()
        
        # Convert column letters to number (A=0, B=1, etc.)
        col_num = 0
        for char in col_letters:
            col_num = col_num * 26 + (ord(char) - ord('A'))
        
        row_num = int(row_str) - 1  # Convert to 0-based
        
        return (row_num, col_num)

class FormulaValidator:
    """Validates formulas for correctness and best practices"""
    
    def __init__(self):
        self.parser = AdvancedFormulaParser()
    
    def validate_formula(self, formula: str) -> Dict[str, Any]:
        """Validate a formula and return validation results"""
        
        if not formula.startswith('='):
            return {
                'valid': False,
                'errors': ['Formula must start with ='],
                'warnings': [],
                'suggestions': []
            }
        
        parsed = self.parser.parse_formula(formula)
        
        result = {
            'valid': len(parsed.potential_errors) == 0,
            'errors': [],
            'warnings': parsed.potential_errors,
            'suggestions': [],
            'complexity': parsed.complexity.value,
            'complexity_score': parsed.complexity_score
        }
        
        # Add suggestions based on complexity
        if parsed.complexity in [FormulaComplexity.ADVANCED, FormulaComplexity.EXPERT]:
            result['suggestions'].append("Consider breaking into smaller formulas for maintainability")
        
        if parsed.is_volatile:
            result['suggestions'].append("Volatile functions may impact performance")
        
        if parsed.nesting_level > 3:
            result['suggestions'].append("Deep nesting may be hard to debug")
        
        return result

# Utility functions for integration with other modules
def parse_formula_simple(formula: str) -> Dict[str, Any]:
    """Simple parsing function for backward compatibility"""
    parser = AdvancedFormulaParser()
    parsed = parser.parse_formula(formula)
    
    return {
        'functions': parsed.functions_used,
        'dependencies': parsed.cell_dependencies,
        'complexity': parsed.complexity.value,
        'is_volatile': parsed.is_volatile,
        'errors': parsed.potential_errors
    }

def get_formula_dependencies(formula: str) -> Set[Tuple[int, int]]:
    """Get just the cell dependencies for dependency tracking"""
    parser = AdvancedFormulaParser()
    parsed = parser.parse_formula(formula)
    return parsed.cell_dependencies