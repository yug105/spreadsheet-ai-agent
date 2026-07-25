"""
Shared types for the superior context system
Contains all enums and dataclasses used across the system
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Set, Union

# Type definitions
Coordinate = Tuple[int, int]
CellAddress = str
Range = Tuple[Coordinate, Coordinate]

class CellType(Enum):
    """Enhanced cell types with more granular classification"""
    EMPTY = "empty"
    TEXT = "text"
    NUMBER = "number"
    FORMULA = "formula"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    ERROR = "error"
    CODE_PYTHON = "code_python"
    CODE_JAVASCRIPT = "code_javascript"
    CODE_SQL = "code_sql"
    SPILL_OUTPUT = "spill_output"
    MERGED_CELL = "merged_cell"
    HYPERLINK = "hyperlink"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"

class DataSemanticType(Enum):
    """Semantic classification of data content"""
    UNKNOWN = "unknown"
    EMPTY = "empty"
    IDENTIFIER = "identifier"
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    URL = "url"
    CURRENCY_VALUE = "currency_value"
    PERCENTAGE_VALUE = "percentage_value"
    SCIENTIFIC_NOTATION = "scientific_notation"
    SOCIAL_SECURITY = "social_security"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    COORDINATES = "coordinates"
    MEASUREMENT = "measurement"
    DATE = "date"
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    CATEGORY = "category"
    MIXED = "mixed"

class FormulaComplexity(Enum):
    """Formula complexity levels"""
    SIMPLE = "simple"          # =A1, =5+3
    BASIC = "basic"            # =SUM(A1:A5)
    INTERMEDIATE = "intermediate"  # =VLOOKUP(...), nested functions
    ADVANCED = "advanced"      # Array formulas, complex nested logic
    EXPERT = "expert"          # VBA UDFs, dynamic references

@dataclass
class MergedCellInfo:
    """Information about merged cells"""
    range: Range
    display_coordinate: Coordinate  # Top-left cell that shows the value
    size: Tuple[int, int]  # (rows, cols)
    content: Any
    
@dataclass
class NamedRange:
    """Information about named ranges"""
    name: str
    range: Range
    sheet_scope: Optional[str] = None  # None for workbook scope
    formula: Optional[str] = None  # For dynamic named ranges
    
@dataclass
class StructuredReference:
    """Information about table structured references"""
    table_name: str
    column_name: Optional[str] = None
    specifier: Optional[str] = None  # [#Headers], [#Data], [#Totals], etc.
    range: Optional[Range] = None  # Resolved range

@dataclass 
class DataValidationRule:
    """Data validation rule information"""
    rule_type: str  # "list", "decimal", "date", "custom", etc.
    formula1: Optional[str] = None
    formula2: Optional[str] = None
    operator: Optional[str] = None
    allow_blank: bool = True
    show_input_message: bool = False
    show_error_message: bool = True
    error_style: str = "stop"  # "stop", "warning", "information"
    
@dataclass
class ConditionalFormatRule:
    """Conditional formatting rule"""
    rule_type: str
    formula: Optional[str] = None
    priority: int = 0
    format_settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnhancedEvaluationResult:
    """Complete evaluation result with runtime information"""
    success: bool
    output_value: Any
    display_value: str
    
    # Runtime tracking
    cells_accessed: Set[Coordinate] = field(default_factory=set)
    ranges_accessed: List[Range] = field(default_factory=list)
    named_ranges_accessed: Set[str] = field(default_factory=set)
    
    # Execution details
    execution_time_ms: float = 0.0
    memory_used_bytes: int = 0
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_location: Optional[Coordinate] = None
    stack_trace: Optional[str] = None
    
    # Code execution specific
    std_out: Optional[str] = None
    std_err: Optional[str] = None
    variables_created: Dict[str, Any] = field(default_factory=dict)
    
    # Array/spill information
    array_output: Optional[List[List[Any]]] = None
    spill_range: Optional[Range] = None
    
    # Dependencies discovered at runtime
    runtime_dependencies: Set[Coordinate] = field(default_factory=set)

@dataclass
class ColumnProfile:
    """Comprehensive column data profile"""
    column_index: int
    column_name: Optional[str] = None
    
    # Basic statistics
    total_cells: int = 0
    non_empty_cells: int = 0
    unique_values: int = 0
    
    # Type distribution
    type_distribution: Dict[CellType, int] = field(default_factory=dict)
    semantic_type: DataSemanticType = DataSemanticType.UNKNOWN
    inferred_type: DataSemanticType = DataSemanticType.UNKNOWN  # For backward compatibility
    
    # Numeric statistics (if applicable)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[float] = None
    std_dev: Optional[float] = None
    variance: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    
    # String statistics (if applicable)
    avg_string_length: Optional[float] = None
    max_string_length: Optional[int] = None
    min_string_length: Optional[int] = None
    
    # Pattern analysis
    common_patterns: List[str] = field(default_factory=list)
    format_patterns: Set[str] = field(default_factory=set)
    
    # Quality metrics
    null_percentage: float = 0.0
    outlier_count: int = 0
    validation_failures: int = 0
    
    # Statistics dictionary for backward compatibility
    stats: Dict[str, Any] = field(default_factory=dict)
    
    # Data consistency
    consistency_score: float = 1.0
    format_consistency: float = 1.0
    
    # Quality score (for backward compatibility)
    quality_score: float = 1.0
    
    # Data quality warnings - NEW FIELD
    quality_warnings: List[str] = field(default_factory=list)

@dataclass
class SuperiorCellInfo:
    """Superior cell information with complete context"""
    # Basic identification
    coordinate: Coordinate
    a1_address: str
    sheet_name: str
    
    # Content and type
    raw_value: Any
    display_value: str
    cell_type: CellType
    semantic_type: DataSemanticType = DataSemanticType.UNKNOWN
    
    # Formula information
    formula: Optional[str] = None
    formula_complexity: Optional[FormulaComplexity] = None
    parsed_formula: Optional[Dict[str, Any]] = None
    
    # Evaluation results
    evaluation_result: Optional[EnhancedEvaluationResult] = None
    
    # Dependencies (runtime-accurate)
    direct_dependencies: Set[Coordinate] = field(default_factory=set)
    indirect_dependencies: Set[Coordinate] = field(default_factory=set)
    dependents: Set[Coordinate] = field(default_factory=set)
    named_range_dependencies: Set[str] = field(default_factory=set)
    structured_ref_dependencies: Set[StructuredReference] = field(default_factory=set)
    
    # Merged cell information
    is_merged: bool = False
    merged_info: Optional[MergedCellInfo] = None
    
    # Array/spill information
    is_array_origin: bool = False
    is_spill_output: bool = False
    array_cells: List[Coordinate] = field(default_factory=list)
    spill_origin: Optional[Coordinate] = None
    
    # Formatting and visual
    format_info: Dict[str, Any] = field(default_factory=dict)
    conditional_formats: List[ConditionalFormatRule] = field(default_factory=list)
    
    # Validation and rules
    data_validation: Optional[DataValidationRule] = None
    
    # Context
    data_region_id: Optional[str] = None
    is_header: bool = False
    table_info: Optional[Dict[str, Any]] = None
    
    # Change tracking
    last_modified: Optional[datetime] = None
    modification_count: int = 0
    version_hash: Optional[str] = None
    
    # Security and privacy
    contains_pii: bool = False
    sensitivity_level: str = "public"  # "public", "internal", "confidential", "restricted"
    
    # Quality and anomalies
    quality_score: float = 1.0
    anomaly_flags: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

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
