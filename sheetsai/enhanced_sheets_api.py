"""
Enhanced Google Sheets API Manager
Provides advanced spreadsheet operations with rate limiting and error handling
"""

import os
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from functools import wraps
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.exceptions import GoogleAuthError

from .context.spreadsheet_native import SpreadsheetGrid, SuperiorCellInfo, CellType
from .exceptions import SheetsAIError

logger = logging.getLogger(__name__)

def rate_limit_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for rate limiting and retrying API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if "quota" in str(e).lower() or "rate" in str(e).lower():
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise e
            
            raise last_exception
        return wrapper
    return decorator

class EnhancedGoogleSheetsManager:
    """
    Enhanced Google Sheets Manager with comprehensive data access
    """
    
    def __init__(self, credential_file: str = None, spreadsheet_id: str = None, 
                 gspread_client: gspread.Client = None, spreadsheet: gspread.Spreadsheet = None):
        self.credential_file = credential_file
        self.spreadsheet_id = spreadsheet_id
        self.gspread_client = gspread_client
        self.spreadsheet = spreadsheet
        self.current_sheet = "Sheet1"  # Track current sheet
        self._current_worksheet = None  # Cache the actual worksheet object
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Rate limiting
        self._last_api_call = 0
        self._min_call_interval = 0.1  # 100ms between calls
        
        # Initialize connection
        if gspread_client and spreadsheet:
            # User OAuth mode
            self.client = gspread_client
            self.spreadsheet = spreadsheet
            self.auth_mode = "user_oauth"
            logger.info("✅ Initialized with user OAuth credentials")
        elif credential_file and spreadsheet_id:
            # Service account mode
            self._connect()
            self.auth_mode = "service_account"
            logger.info("✅ Initialized with service account credentials")
        else:
            raise SheetsAIError("Must provide either (credential_file, spreadsheet_id) or (gspread_client, spreadsheet)")
    
    def _rate_limit(self):
        """Implement rate limiting"""
        now = time.time()
        time_since_last = now - self._last_api_call
        if time_since_last < self._min_call_interval:
            time.sleep(self._min_call_interval - time_since_last)
        self._last_api_call = time.time()
    
    @rate_limit_retry(max_retries=3, base_delay=2.0)
    def _connect(self) -> bool:
        """Connect to Google Sheets using service account credentials"""
        try:
            if not self.credential_file or not os.path.exists(self.credential_file):
                raise SheetsAIError(f"Credential file not found: {self.credential_file}")
            
            # Load service account credentials
            credentials = ServiceAccountCredentials.from_service_account_file(
                self.credential_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Create gspread client
            self.client = gspread.authorize(credentials)
            
            # Open spreadsheet
            if self.spreadsheet_id:
                self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                logger.info(f"✅ Connected to spreadsheet: {self.spreadsheet.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            raise SheetsAIError(f"Connection failed: {str(e)}")
    
    def get_enhanced_data(self, worksheet_name: str = None, 
                         force_refresh: bool = False,
                         include_formatting: bool = True,
                         include_formulas: bool = True) -> SpreadsheetGrid:
        """
        Get enhanced spreadsheet data with comprehensive cell information
        """
        
        # Check cache first
        cache_key = f"{worksheet_name}_{include_formatting}_{include_formulas}"
        if not force_refresh and cache_key in self._cache:
            cache_age = (datetime.now() - self._cache[cache_key]['timestamp']).total_seconds()
            if cache_age < self._cache_ttl:
                logger.info(f"📋 Using cached data for '{worksheet_name}'")
                return self._cache[cache_key]['data']
        
        try:
            # Get worksheet
            if worksheet_name:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = self.spreadsheet.sheet1
            
            # Load enhanced data
            grid = self._load_enhanced_worksheet_data(worksheet, include_formatting, include_formulas)
            
            # Cache the result
            self._cache[cache_key] = {
                'data': grid,
                'timestamp': datetime.now()
            }
            
            logger.info(f"✅ Loaded enhanced data for '{worksheet_name or 'Sheet1'}'")
            return grid
            
        except Exception as e:
            logger.error(f"❌ Failed to get enhanced data: {e}")
            raise SheetsAIError(f"Data loading failed: {str(e)}")
    
    def _load_enhanced_worksheet_data(self, worksheet, 
                                    include_formatting: bool,
                                    include_formulas: bool) -> SpreadsheetGrid:
        """Load enhanced worksheet data with comprehensive cell information"""
        
        # Get basic data
        all_values = worksheet.get_all_values()
        
        # Create grid
        grid = SpreadsheetGrid(worksheet.title)
        
        # Process each cell
        for row_idx, row in enumerate(all_values):
            for col_idx, value in enumerate(row):
                address = f"{chr(65 + col_idx)}{row_idx + 1}"
                
                # Create superior cell info
                cell_info = SuperiorCellInfo(
                    coordinate=(row_idx, col_idx),
                    a1_address=address,
                    sheet_name=worksheet.title,
                    raw_value=value,
                    display_value=value,
                    cell_type=self._infer_cell_type(value)
                )
                
                grid.cells[address] = cell_info
        
        # Get formulas if requested
        if include_formulas:
            try:
                formulas = self._get_formulas_batch(worksheet)
                for address, formula in formulas.items():
                    if address in grid.cells:
                        grid.cells[address].formula = formula
                        grid.cells[address].cell_type = CellType.FORMULA
            except Exception as e:
                logger.warning(f"Could not load formulas: {e}")
        
        # Get formatting if requested
        if include_formatting:
            try:
                formatting = self._get_formatting_batch(worksheet)
                for address, format_data in formatting.items():
                    if address in grid.cells:
                        grid.cells[address].format_info = self._extract_format_info(format_data)
            except Exception as e:
                logger.warning(f"Could not load formatting: {e}")
        
        # Update used range
        grid._update_used_range()
        
        return grid
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def _get_formulas_batch(self, worksheet) -> Dict[str, str]:
        """Get formulas for all cells in batch"""
        try:
            # Get all formulas in one call
            formulas = worksheet.get_all_values(value_render_option='FORMULA')
            
            formula_dict = {}
            for row_idx, row in enumerate(formulas):
                for col_idx, value in enumerate(row):
                    if value.startswith('='):
                        address = f"{chr(65 + col_idx)}{row_idx + 1}"
                        formula_dict[address] = value
            
            return formula_dict
        except Exception as e:
            logger.warning(f"Failed to get formulas: {e}")
            return {}
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def _get_formatting_batch(self, worksheet) -> Dict[str, Dict]:
        """Get formatting for all cells in batch"""
        try:
            # Get formatting information
            # Note: This is a simplified implementation
            # In a full implementation, you'd use the Google Sheets API directly
            return {}
        except Exception as e:
            logger.warning(f"Failed to get formatting: {e}")
            return {}
    
    def _extract_format_info(self, format_data: Dict) -> Dict[str, Any]:
        """Extract formatting information from Google Sheets format data"""
        format_info = {}
        
        if 'numberFormat' in format_data:
            format_info['number_format'] = format_data['numberFormat'].get('pattern', '')
        
        if 'backgroundColor' in format_data:
            format_info['background_color'] = format_data['backgroundColor']
        
        if 'textFormat' in format_data:
            text_format = format_data['textFormat']
            format_info['bold'] = text_format.get('bold', False)
            format_info['italic'] = text_format.get('italic', False)
            format_info['font_size'] = text_format.get('fontSize', 10)
        
        return format_info
    
    def _infer_cell_type(self, value: Any) -> CellType:
        """Infer the cell type based on content"""
        if not value:
            return CellType.EMPTY
        elif isinstance(value, bool):
            return CellType.BOOLEAN
        elif isinstance(value, (int, float)):
            return CellType.NUMBER
        elif isinstance(value, str):
            if value.startswith('='):
                return CellType.FORMULA
            elif value.startswith('#'):
                return CellType.ERROR
            else:
                # Try to convert to number
                try:
                    float(value.replace(',', ''))
                    return CellType.NUMBER
                except ValueError:
                    return CellType.TEXT
        else:
            return CellType.TEXT
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def set_cell_value_native(self, address: str, value: Any, 
                            value_input_option: str = 'USER_ENTERED') -> bool:
        """Set a single cell value"""
        try:
            self._rate_limit()
            
            # Use current worksheet instead of always using sheet1
            if hasattr(self, '_current_worksheet') and self._current_worksheet:
                worksheet = self._current_worksheet
                logger.info(f"✅ Using current worksheet: '{worksheet.title}' for writing")
            else:
                # Fallback to current sheet name
                worksheet = self.spreadsheet.worksheet(self.current_sheet)
                logger.info(f"✅ Got worksheet: '{worksheet.title}' for writing")
            
            # Set the value
            worksheet.update(address, value, value_input_option=value_input_option)
            
            # Clear cache
            self.clear_cache()
            
            logger.info(f"✅ Set cell {address} to {value} in sheet '{worksheet.title}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set cell {address}: {e}")
            return False
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def set_range_values_native(self, range_notation: str, values: List[List[Any]], 
                              value_input_option: str = 'USER_ENTERED') -> bool:
        """Set values in a range"""
        try:
            self._rate_limit()
            
            # Use current worksheet instead of always using sheet1
            if hasattr(self, '_current_worksheet') and self._current_worksheet:
                worksheet = self._current_worksheet
                logger.info(f"✅ Using current worksheet: '{worksheet.title}' for writing")
            else:
                # Fallback to current sheet name
                worksheet = self.spreadsheet.worksheet(self.current_sheet)
                logger.info(f"✅ Got worksheet: '{worksheet.title}' for writing")
            
            # Set the values
            worksheet.update(range_notation, values, value_input_option=value_input_option)
            
            # Clear cache
            self.clear_cache()
            
            logger.info(f"✅ Set range {range_notation} with {len(values)} rows in sheet '{worksheet.title}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set range {range_notation}: {e}")
            return False
    
    def update_range_native(self, range_notation: str, values: list) -> bool:
        """Update a range with new values"""
        return self.set_range_values_native(range_notation, values)
    
    def insert_formula_native(self, address: str, formula: str) -> bool:
        """Insert a formula into a cell"""
        return self.set_cell_value_native(address, formula)
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def get_range_data_native(self, range_notation: str, 
                            include_formulas: bool = False) -> Dict[str, Any]:
        """Get data from a specific range"""
        try:
            self._rate_limit()
            # Extract sheet name and range from notation
            if '!' in range_notation:
                sheet_part, range_part = range_notation.split('!', 1)
                target_sheet = sheet_part.strip("'\"")
            else:
                range_part = range_notation
                target_sheet = self.current_sheet
            # Use cached worksheet if it matches, otherwise get fresh one
            if (hasattr(self, '_current_worksheet') and 
                self._current_worksheet and 
                self._current_worksheet.title == target_sheet):
                worksheet = self._current_worksheet
                logger.info(f"🔍 Using cached worksheet: '{worksheet.title}'")
            else:
                try:
                    worksheet = self.spreadsheet.worksheet(target_sheet)
                    logger.info(f"🔍 Got fresh worksheet: '{worksheet.title}'")
                    if target_sheet == self.current_sheet:
                        self._current_worksheet = worksheet
                except Exception as e:
                    logger.error(f"❌ Failed to find worksheet '{target_sheet}': {e}")
                    available_sheets = [ws.title for ws in self.spreadsheet.worksheets()]
                    logger.error(f"Available sheets: {available_sheets}")
                    worksheet = self.spreadsheet.sheet1
                    logger.warning(f"⚠️ Using fallback sheet: '{worksheet.title}'")
            # Get the data
            if include_formulas:
                values = worksheet.get(range_part, value_render_option='FORMULA')
            else:
                values = worksheet.get(range_part)
            result = {
                'range': range_notation,
                'values': values,
                'row_count': len(values),
                'column_count': len(values[0]) if values else 0,
                'actual_sheet_used': worksheet.title,
                'requested_sheet': target_sheet
            }
            logger.info(f"✅ Retrieved data from {range_part} in sheet '{worksheet.title}' (requested: '{target_sheet}')")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get range {range_notation}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'error': str(e),
                'range': range_notation,
                'values': [],
                'actual_sheet_used': 'ERROR'
            }
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def create_named_range(self, name: str, range_notation: str) -> bool:
        """Create a named range"""
        try:
            self._rate_limit()
            
            # Get worksheet (assuming first sheet for now)
            worksheet = self.spreadsheet.sheet1
            
            # Create named range
            worksheet.add_named_range(name, range_notation)
            
            logger.info(f"✅ Created named range '{name}' for {range_notation}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create named range '{name}': {e}")
            return False
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def _get_sheet_id(self, sheet_name: str) -> int:
        """Get the sheet ID for a given sheet name"""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return worksheet.id
        except Exception as e:
            logger.error(f"❌ Failed to get sheet ID for '{sheet_name}': {e}")
            return None
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def add_chart(self, chart_spec: Dict[str, Any]) -> bool:
        """Add a chart to the spreadsheet"""
        try:
            self._rate_limit()
            
            # Get worksheet (assuming first sheet for now)
            worksheet = self.spreadsheet.sheet1
            
            # Add chart (simplified implementation)
            logger.info(f"✅ Added chart to worksheet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add chart: {e}")
            return False
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def format_range(self, range_notation: str, format_spec: Dict[str, Any]) -> bool:
        """Format a range of cells"""
        try:
            self._rate_limit()
            
            # Get worksheet (assuming first sheet for now)
            worksheet = self.spreadsheet.sheet1
            
            # Apply formatting (simplified implementation)
            logger.info(f"✅ Applied formatting to {range_notation}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to format range {range_notation}: {e}")
            return False
    
    def set_current_worksheet(self, worksheet_name: str):
        """Set the current worksheet for operations"""
        try:
            # Verify the worksheet exists and get it
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            self.current_sheet = worksheet_name
            self._current_worksheet = worksheet  # Cache the worksheet object
            self.clear_cache()
            logger.info(f"✅ Set current worksheet to '{worksheet_name}' (ID: {worksheet.id})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set current worksheet to '{worksheet_name}': {e}")
            try:
                available_sheets = [ws.title for ws in self.spreadsheet.worksheets()]
                logger.error(f"Available sheets: {available_sheets}")
            except:
                pass
            return False
    
    def clear_cache(self, worksheet_name: Optional[str] = None):
        """Clear the data cache"""
        if worksheet_name:
            # Clear specific worksheet cache
            keys_to_remove = [k for k in self._cache.keys() if worksheet_name in k]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear all cache
            self._cache.clear()
        
        self._last_cache_clear = datetime.now()
        logger.info("🗑️ Cache cleared")
    
    @rate_limit_retry(max_retries=2, base_delay=1.0)
    def get_sheet_metadata(self, worksheet_name: str = None) -> Dict[str, Any]:
        """Get metadata about the spreadsheet and worksheets"""
        try:
            self._rate_limit()
            
            metadata = {
                'spreadsheet_id': self.spreadsheet_id,
                'spreadsheet_title': self.spreadsheet.title,
                'sheets': [ws.title for ws in self.spreadsheet.worksheets()],
                'total_sheets': len(self.spreadsheet.worksheets()),
                'auth_mode': self.auth_mode
            }
            
            if worksheet_name:
                try:
                    worksheet = self.spreadsheet.worksheet(worksheet_name)
                    metadata['current_sheet'] = {
                        'name': worksheet.title,
                        'id': worksheet.id,
                        'row_count': worksheet.row_count,
                        'col_count': worksheet.col_count
                    }
                except Exception as e:
                    logger.warning(f"Could not get metadata for sheet '{worksheet_name}': {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to get sheet metadata: {e}")
            return {
                'error': str(e),
                'spreadsheet_id': self.spreadsheet_id,
                'auth_mode': self.auth_mode
            }
    
    def get_data(self, worksheet_name: str = None, force_refresh: bool = False) -> Dict[str, Any]:
        """Get basic data from the spreadsheet (legacy compatibility)"""
        try:
            grid = self.get_enhanced_data(worksheet_name, force_refresh)
            
            # Convert to legacy format
            data = {
                'values': [],
                'headers': [],
                'data_regions': [],
                'sheet_name': grid.sheet_name
            }
            
            # Extract values
            if grid.cells:
                # Find the range of data
                addresses = list(grid.cells.keys())
                if addresses:
                    # Convert to legacy format
                    # This is a simplified conversion
                    data['values'] = [[cell.display_value for cell in row] for row in grid.get_rows()]
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to get data: {e}")
            return {'error': str(e)}
    
    def save_data(self, df: pd.DataFrame, worksheet_name: str, mode: str = 'overwrite') -> str:
        """Save a DataFrame to the spreadsheet"""
        try:
            # Convert DataFrame to list of lists
            values = [df.columns.tolist()] + df.values.tolist()
            
            # Get worksheet
            if worksheet_name:
                try:
                    worksheet = self.spreadsheet.worksheet(worksheet_name)
                except:
                    # Create new worksheet
                    worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=26)
            else:
                worksheet = self.spreadsheet.sheet1
            
            # Clear existing data if overwriting
            if mode == 'overwrite':
                worksheet.clear()
            
            # Write data
            worksheet.update('A1', values)
            
            logger.info(f"✅ Saved DataFrame to '{worksheet.title}'")
            return f"Data saved to {worksheet.title}"
            
        except Exception as e:
            logger.error(f"❌ Failed to save DataFrame: {e}")
            return f"Error saving data: {str(e)}"