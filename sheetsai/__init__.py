"""
Enhanced Sheets AI System
Production-ready AI-powered spreadsheet analysis system
"""

__version__ = "1.0.0"
__author__ = "Enhanced Sheets AI Team"

# Only import the essential modules that are definitely available
try:
    from .quadratic_engine import ExactQuadraticEngine, QuadraticLevelAgent, create_quadratic_agent
    from .enhanced_sheets_api import EnhancedGoogleSheetsManager
    from .exceptions import SheetsAIError, SheetConnectionError, DataLoadError, ContextBuildError, FormulaParseError, A1NotationError
    from .tools_fixed import get_atomic_tools, get_tool_by_name, get_tools_schema
except ImportError as e:
    # If imports fail, don't crash the build
    print(f"Warning: Some modules could not be imported: {e}")

__all__ = [
    "ExactQuadraticEngine",
    "QuadraticLevelAgent", 
    "create_quadratic_agent",
    "EnhancedGoogleSheetsManager",
    "SheetsAIError",
    "SheetConnectionError", 
    "DataLoadError",
    "ContextBuildError",
    "FormulaParseError",
    "A1NotationError",
    "get_atomic_tools",
    "get_tool_by_name", 
    "get_tools_schema"
] 