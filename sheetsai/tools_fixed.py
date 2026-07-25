"""
Atomic Tools System - Following Quadratic's Architecture
Replaces heavy analytical tools with atomic primitives for AI-driven reasoning
"""

import logging
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple
import json
from sheetsai.enhanced_sheets_api import EnhancedGoogleSheetsManager
from sheetsai.context.context_builder import QuadraticContext
from sheetsai.exceptions import SheetsAIError

logger = logging.getLogger(__name__)

class BaseTool:
    """Abstract base class for all tools."""
    name: str = "base_tool"
    description: str = "A base tool"
    args_schema: Dict[str, Any] = {}
    category: str = "uncategorized"
    requires_context: bool = False

    def __call__(self, manager: EnhancedGoogleSheetsManager, context: Optional[QuadraticContext] = None, **kwargs) -> Any:
        # Simple validation
        for key in self.args_schema.keys():
            if key not in kwargs:
                raise SheetsAIError(f"Missing required argument '{key}' for tool '{self.name}'")
        return self.run(manager=manager, context=context, **kwargs)

    def run(self, manager: EnhancedGoogleSheetsManager, context: Optional[QuadraticContext] = None, **kwargs) -> Any:
        raise NotImplementedError("Each tool must implement its own run method.")

    def get_schema(self) -> Dict[str, Any]:
        """Returns the tool schema in OpenAI function-calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.args_schema,
                    "required": list(self.args_schema.keys()),
                },
            },
        }

class GetCellDataTool(BaseTool):
    name = "get_cell_data"
    description = "Gets the values of cells in a specified range. Use this to read data from the spreadsheet before performing operations."
    category = "data_access"
    args_schema = {
        "range": {"type": "string", "description": "The A1 notation of the range to get data from (e.g., 'A1:B5')."}
    }

    def run(self, manager: EnhancedGoogleSheetsManager, range: str, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running GetCellDataTool for range: {range}")
        try:
            data = manager.get_range_data_native(range)
            if not data:
                return {
                    "status": "error",
                    "error": f"No data found in range '{range}'",
                    "error_type": "no_data",
                    "suggestion": "Try a different range or check if the data exists"
                }
            return {"status": "success", "data": data}
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to get data from range '{range}': {error_msg}",
                "error_type": "data_access_error",
                "suggestion": "Check the range format and ensure the data exists"
            }

class SetCellValuesTool(BaseTool):
    name = "set_cell_values"
    description = "Sets values in a range of cells. Use this to write data to the spreadsheet."
    category = "data_write"
    args_schema = {
        "range": {"type": "string", "description": "The A1 notation of the range to write to (e.g., 'A1')."},
        "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "A 2D array of values to write."},
    }

    def run(self, manager: EnhancedGoogleSheetsManager, range: str, values: List[List[str]], context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running SetCellValuesTool for range: {range}")
        try:
            success = manager.set_range_values_native(range, values)
            if success:
                return {"status": "success", "message": f"Successfully set {len(values)} rows in range '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to set values in range '{range}'",
                    "error_type": "write_error",
                    "suggestion": "Check the range format and ensure you have write permissions"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to set values in range '{range}': {error_msg}",
                "error_type": "write_error",
                "suggestion": "Check the range format and ensure you have write permissions"
            }

class SetFormulaTool(BaseTool):
    name = "set_formula"
    description = "Inserts a formula into a single cell. Use this for calculations."
    category = "formula"
    args_schema = {
        "cell": {"type": "string", "description": "The A1 notation of the cell to insert the formula into (e.g., 'C1')."},
        "formula": {"type": "string", "description": "The formula to insert, starting with '='."},
    }

    def run(self, manager: EnhancedGoogleSheetsManager, cell: str, formula: str, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running SetFormulaTool for cell: {cell}")
        try:
            if not formula.startswith('='):
                formula = '=' + formula
            success = manager.insert_formula_native(cell, formula)
            if success:
                return {"status": "success", "message": f"Successfully set formula in cell '{cell}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to set formula in cell '{cell}'",
                    "error_type": "formula_error",
                    "suggestion": "Check the formula syntax and ensure the cell reference is valid"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to set formula in cell '{cell}': {error_msg}",
                "error_type": "formula_error",
                "suggestion": "Check the formula syntax and ensure the cell reference is valid"
            }

class PythonCodeTool(BaseTool):
    name = "python_code"
    description = "Executes Python code for complex data analysis, transformation, or when other tools are insufficient. The code runs in a sandboxed environment with pandas available. Use `get_cell_data` first to load data into a DataFrame."
    category = "computation"
    args_schema = {
        "code": {"type": "string", "description": "A string of Python code to execute. The result of the last expression will be returned."},
    }

    def run(self, manager: EnhancedGoogleSheetsManager, code: str, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info("Running PythonCodeTool")
        try:
            exec_globals = {'pd': pd, 'np': np}
            exec(code, exec_globals)
            result = exec_globals.get('result', 'No result variable set.')
            return {"status": "success", "result": str(result)}
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            error_msg = str(e)
            return {
                "status": "error", 
                "error": f"Python code execution failed: {error_msg}",
                "error_type": "python_execution_error",
                "suggestion": "Check the Python syntax and ensure all variables are properly defined"
            }

class SetCellFormatsTool(BaseTool):
    name = "set_cell_formats"
    description = "Applies formatting (bold, italics, colors, number formats) to a range of cells."
    category = "formatting"
    args_schema = {
        "range": {"type": "string", "description": "A1 notation of the range to format."},
        "formats": {"type": "object", "description": "Formatting options (e.g., bold, color, number_format)."}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, range: str, formats: dict, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running SetCellFormatsTool for range: {range}")
        try:
            success = manager.format_range(range, formats)
            if success:
                return {"status": "success", "message": f"Successfully formatted range '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to format range '{range}'",
                    "error_type": "formatting_error",
                    "suggestion": "Check the range format and formatting options"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to format range '{range}': {error_msg}",
                "error_type": "formatting_error",
                "suggestion": "Check the range format and formatting options"
            }

class ApplyConditionalFormattingTool(BaseTool):
    name = "apply_conditional_formatting"
    description = "Applies conditional formatting rules to a range."
    category = "formatting"
    args_schema = {
        "range": {"type": "string", "description": "A1 notation of the range."},
        "rule": {"type": "object", "description": "Conditional formatting rule definition."}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, range: str, rule: dict, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running ApplyConditionalFormattingTool for range: {range}")
        try:
            # Convert rule to format spec
            format_spec = self._convert_rule_to_format(rule)
            success = manager.format_range(range, format_spec)
            if success:
                return {"status": "success", "message": f"Successfully applied conditional formatting to '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to apply conditional formatting to '{range}'",
                    "error_type": "formatting_error",
                    "suggestion": "Check the conditional formatting rule"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to apply conditional formatting to '{range}': {error_msg}",
                "error_type": "formatting_error",
                "suggestion": "Check the conditional formatting rule"
            }
    
    def _convert_rule_to_format(self, rule: dict) -> dict:
        """Convert conditional formatting rule to format specification"""
        format_spec = {}
        
        if 'backgroundColor' in rule:
            format_spec['backgroundColor'] = rule['backgroundColor']
        
        if 'textFormat' in rule:
            format_spec['textFormat'] = rule['textFormat']
        
        if 'numberFormat' in rule:
            format_spec['numberFormat'] = rule['numberFormat']
        
        return format_spec

class ClearFormatsTool(BaseTool):
    name = "clear_formats"
    description = "Removes all formatting from a range of cells."
    category = "formatting"
    args_schema = {
        "range": {"type": "string", "description": "A1 notation of the range to clear formatting from."}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, range: str, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running ClearFormatsTool for range: {range}")
        try:
            # Clear formatting by applying default format
            default_format = {
                'textFormat': {'bold': False, 'italic': False},
                'backgroundColor': {'red': 1, 'green': 1, 'blue': 1}
            }
            success = manager.format_range(range, default_format)
            if success:
                return {"status": "success", "message": f"Successfully cleared formatting from '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to clear formatting from '{range}'",
                    "error_type": "formatting_error",
                    "suggestion": "Check the range format"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to clear formatting from '{range}': {error_msg}",
                "error_type": "formatting_error",
                "suggestion": "Check the range format"
            }

class AddSheetTool(BaseTool):
    name = "add_sheet"
    description = "Creates a new worksheet in the spreadsheet."
    category = "structure"
    args_schema = {
        "sheet_name": {"type": "string", "description": "Name of the new worksheet."}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, sheet_name: str, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running AddSheetTool for sheet: {sheet_name}")
        try:
            # Create new worksheet using gspread
            worksheet = manager.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=26)
            if worksheet:
                return {"status": "success", "message": f"Successfully created worksheet '{sheet_name}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to create worksheet '{sheet_name}'",
                    "error_type": "sheet_creation_error",
                    "suggestion": "Check if the sheet name is valid and not already exists"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to create worksheet '{sheet_name}': {error_msg}",
                "error_type": "sheet_creation_error",
                "suggestion": "Check if the sheet name is valid and not already exists"
            }

class RenameSheetTool(BaseTool):
    name = "rename_sheet"
    description = "Renames an existing worksheet."
    category = "structure"
    args_schema = {
        "old_name": {"type": "string", "description": "Current name of the worksheet."},
        "new_name": {"type": "string", "description": "New name for the worksheet."}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, old_name: str, new_name: str, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running RenameSheetTool from '{old_name}' to '{new_name}'")
        try:
            # Get worksheet and rename it
            worksheet = manager.spreadsheet.worksheet(old_name)
            worksheet.update_title(new_name)
            return {"status": "success", "message": f"Successfully renamed worksheet from '{old_name}' to '{new_name}'"}
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to rename worksheet from '{old_name}' to '{new_name}': {error_msg}",
                "error_type": "sheet_rename_error",
                "suggestion": "Check if the old sheet exists and new name is valid"
            }

class SortRangeTool(BaseTool):
    name = "sort_range"
    description = "Sorts a range of data by one or more columns."
    category = "manipulation"
    args_schema = {
        "range": {"type": "string", "description": "A1 notation of the range to sort."},
        "sort_columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to sort by (A, B, etc.)."},
        "ascending": {"type": "boolean", "description": "Sort ascending (true) or descending (false).", "default": True}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, range: str, sort_columns: list, ascending: bool = True, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running SortRangeTool for range: {range}")
        try:
            # Get data from range
            data_result = manager.get_range_data_native(range)
            if 'error' in data_result:
                return {
                    "status": "error",
                    "error": f"Failed to get data from range '{range}': {data_result['error']}",
                    "error_type": "data_access_error",
                    "suggestion": "Check the range format"
                }
            
            values = data_result['values']
            if not values:
                return {
                    "status": "error",
                    "error": f"No data found in range '{range}'",
                    "error_type": "empty_range_error",
                    "suggestion": "Check if the range contains data"
                }
            
            # Convert to DataFrame for sorting
            df = pd.DataFrame(values[1:], columns=values[0])  # First row as headers
            
            # Convert column letters to indices
            sort_indices = []
            for col in sort_columns:
                col_idx = ord(col.upper()) - ord('A')
                if 0 <= col_idx < len(df.columns):
                    sort_indices.append(col_idx)
            
            if not sort_indices:
                return {
                    "status": "error",
                    "error": f"Invalid sort columns: {sort_columns}",
                    "error_type": "invalid_column_error",
                    "suggestion": "Check column references"
                }
            
            # Sort the DataFrame
            df_sorted = df.sort_values(by=sort_indices, ascending=ascending)
            
            # Convert back to list of lists
            sorted_values = [df.columns.tolist()] + df_sorted.values.tolist()
            
            # Write back to spreadsheet
            success = manager.set_range_values_native(range, sorted_values)
            if success:
                return {"status": "success", "message": f"Successfully sorted range '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to write sorted data to range '{range}'",
                    "error_type": "write_error",
                    "suggestion": "Check write permissions"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to sort range '{range}': {error_msg}",
                "error_type": "sort_error",
                "suggestion": "Check the range format and column references"
            }

class CreateChartTool(BaseTool):
    name = "create_chart"
    description = "Creates a chart from a data range."
    category = "visualization"
    args_schema = {
        "range": {"type": "string", "description": "A1 notation of the data range."},
        "chart_type": {"type": "string", "description": "Type of chart (bar, line, pie, etc.)."},
        "options": {"type": "object", "description": "Additional chart options.", "default": {}}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, range: str, chart_type: str, options: dict = None, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running CreateChartTool for range: {range}, type: {chart_type}")
        try:
            if options is None:
                options = {}
            
            # Create chart specification
            chart_spec = {
                'chartType': chart_type.upper(),
                'dataRange': range,
                'options': options
            }
            
            success = manager.add_chart(chart_spec)
            if success:
                return {"status": "success", "message": f"Successfully created {chart_type} chart from range '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to create chart from range '{range}'",
                    "error_type": "chart_creation_error",
                    "suggestion": "Check the data range and chart type"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to create chart from range '{range}': {error_msg}",
                "error_type": "chart_creation_error",
                "suggestion": "Check the data range and chart type"
            }

class FindAndReplaceTool(BaseTool):
    name = "find_and_replace"
    description = "Finds and replaces values in a range."
    category = "manipulation"
    args_schema = {
        "range": {"type": "string", "description": "A1 notation of the range."},
        "find": {"type": "string", "description": "Value to find."},
        "replace": {"type": "string", "description": "Value to replace with."},
        "match_case": {"type": "boolean", "description": "Match case?", "default": False}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, range: str, find: str, replace: str, match_case: bool = False, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running FindAndReplaceTool for range: {range}")
        try:
            # Get data from range
            data_result = manager.get_range_data_native(range)
            if 'error' in data_result:
                return {
                    "status": "error",
                    "error": f"Failed to get data from range '{range}': {data_result['error']}",
                    "error_type": "data_access_error",
                    "suggestion": "Check the range format"
                }
            
            values = data_result['values']
            if not values:
                return {
                    "status": "error",
                    "error": f"No data found in range '{range}'",
                    "error_type": "empty_range_error",
                    "suggestion": "Check if the range contains data"
                }
            
            # Perform find and replace
            replaced_count = 0
            for row_idx, row in enumerate(values):
                for col_idx, cell_value in enumerate(row):
                    if isinstance(cell_value, str):
                        if match_case:
                            if find in cell_value:
                                values[row_idx][col_idx] = cell_value.replace(find, replace)
                                replaced_count += 1
                        else:
                            if find.lower() in cell_value.lower():
                                # Case-insensitive replacement
                                import re
                                pattern = re.compile(re.escape(find), re.IGNORECASE)
                                values[row_idx][col_idx] = pattern.sub(replace, cell_value)
                                replaced_count += 1
            
            # Write back to spreadsheet
            success = manager.set_range_values_native(range, values)
            if success:
                return {"status": "success", "message": f"Successfully replaced {replaced_count} occurrences in range '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to write updated data to range '{range}'",
                    "error_type": "write_error",
                    "suggestion": "Check write permissions"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to perform find and replace in range '{range}': {error_msg}",
                "error_type": "find_replace_error",
                "suggestion": "Check the range format and search parameters"
            }

class CreateDataTableTool(BaseTool):
    name = "create_data_table"
    description = "Converts a range into a structured data table."
    category = "structure"
    args_schema = {
        "range": {"type": "string", "description": "A1 notation of the range to convert."},
        "table_name": {"type": "string", "description": "Name for the new table."}
    }
    
    def run(self, manager: EnhancedGoogleSheetsManager, range: str, table_name: str, context: Optional[QuadraticContext] = None) -> Dict[str, Any]:
        logger.info(f"Running CreateDataTableTool for range: {range}, table: {table_name}")
        try:
            # Create named range for the table
            success = manager.create_named_range(table_name, range)
            if success:
                return {"status": "success", "message": f"Successfully created data table '{table_name}' from range '{range}'"}
            else:
                return {
                    "status": "error",
                    "error": f"Failed to create data table '{table_name}' from range '{range}'",
                    "error_type": "table_creation_error",
                    "suggestion": "Check the range format and table name"
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "status": "error",
                "error": f"Failed to create data table '{table_name}' from range '{range}': {error_msg}",
                "error_type": "table_creation_error",
                "suggestion": "Check the range format and table name"
            }

# --- Tool Registry ---

_atomic_tools = [
    GetCellDataTool(),
    SetCellValuesTool(),
    SetFormulaTool(),
    PythonCodeTool(),
    SetCellFormatsTool(),
    ApplyConditionalFormattingTool(),
    ClearFormatsTool(),
    AddSheetTool(),
    RenameSheetTool(),
    SortRangeTool(),
    CreateChartTool(),
    FindAndReplaceTool(),
    CreateDataTableTool(),
]

_tool_map = {tool.name: tool for tool in _atomic_tools}

def get_atomic_tools() -> List[BaseTool]:
    return _atomic_tools

def get_tool_by_name(name: str) -> Optional[BaseTool]:
    return _tool_map.get(name)

def get_tools_schema() -> List[Dict[str, Any]]:
    return [tool.get_schema() for tool in _atomic_tools]
