# sheetsai/context/__init__.py

# Core superior cell context classes
from .shared_types import (
    SuperiorCellInfo, CellType, DataSemanticType, FormulaComplexity,
    EnhancedEvaluationResult, ColumnProfile, DataRegion,
    MergedCellInfo, NamedRange, StructuredReference,
    DataValidationRule, ConditionalFormatRule, Coordinate
)

# Core analyzer
from .core_analyzer import SuperiorCellContextAnalyzer

# Formula parsing and evaluation
from .formula_parsing import AdvancedFormulaParser
from .evaluation import RealSpreadsheetEvaluator

# Data profiling and semantic detection
from .profiling import AdvancedDataProfiler, SemanticTypeDetector

# Dependency tracking
from .dependency import DependencyTracker, FormulaInfo, SpillTracker, DependencyRelation, DependencyType

# Context building and formatting
from .context_builder import QuadraticContextBuilder, QuadraticContext, ContextFormatter

# Spreadsheet-native structures
from .spreadsheet_native import SpreadsheetGrid, SheetCollection

# A1 notation handling
from sheetsai.a1_notation import A1NotationHandler, CellReference, RangeReference, ReferenceType

# Integration and compatibility
from ..integration import ContextRevolutionIntegrator, upgrade_existing_system

# Version and capability info
__version__ = "2.0.0"
__capabilities__ = [
    "superior_cell_analysis",
    "quadratic_context_building", 
    "advanced_formula_parsing",
    "spreadsheet_native_operations",
    "semantic_type_detection",
    "real_evaluation_engine"
]