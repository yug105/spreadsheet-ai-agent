"""
Custom exceptions for the SheetsAI system.
"""

class SheetsAIError(Exception):
    """Base exception for SheetsAI errors."""
    
    def __init__(self, message: str, suggestion: str = None, original_exception: Exception = None):
        self.message = message
        self.suggestion = suggestion
        self.original_exception = original_exception
        super().__init__(self.message)

class SheetConnectionError(SheetsAIError):
    """Raised when there's an error connecting to Google Sheets."""
    
    def __init__(self, message: str, original_exception: Exception = None):
        suggestion = "Check your credentials and internet connection."
        super().__init__(message, suggestion, original_exception)

class DataLoadError(SheetsAIError):
    """Raised when there's an error loading data from Google Sheets."""
    
    def __init__(self, worksheet_name: str = None, original_exception: Exception = None):
        message = f"Failed to load data from worksheet '{worksheet_name}'" if worksheet_name else "Failed to load data"
        suggestion = "Verify the worksheet name and permissions."
        super().__init__(message, suggestion, original_exception)

class ContextBuildError(SheetsAIError):
    """Raised when there's an error building context."""
    
    def __init__(self, message: str, original_exception: Exception = None):
        suggestion = "Check the data structure and try again."
        super().__init__(message, suggestion, original_exception)

class FormulaParseError(SheetsAIError):
    """Raised when there's an error parsing formulas."""
    
    def __init__(self, formula: str, original_exception: Exception = None):
        message = f"Failed to parse formula: {formula}"
        suggestion = "Check the formula syntax."
        super().__init__(message, suggestion, original_exception)

class A1NotationError(SheetsAIError):
    """Raised when there's an error with A1 notation."""
    
    def __init__(self, notation: str, original_exception: Exception = None):
        message = f"Invalid A1 notation: {notation}"
        suggestion = "Use valid A1 notation (e.g., A1, B2:C5)."
        super().__init__(message, suggestion, original_exception) 