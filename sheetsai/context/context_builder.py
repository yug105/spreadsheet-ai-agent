"""
Quadratic-Level Context Builder - FIXED VERSION
Fixes column profile creation and data region analysis
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import logging
from datetime import datetime

from .shared_types import (
    SuperiorCellInfo, DataSemanticType, CellType, FormulaComplexity,
    ColumnProfile, EnhancedEvaluationResult, DataRegion
)
from .core_analyzer import SuperiorCellContextAnalyzer
from .profiling import AdvancedDataProfiler
from .evaluation import RealSpreadsheetEvaluator
from sheetsai.a1_notation import A1NotationHandler, CellReference, RangeReference
from .spreadsheet_native import SpreadsheetGrid, SheetCollection
from .dependency import DependencyTracker, FormulaInfo, SpillTracker

logger = logging.getLogger(__name__)

@dataclass
class QuadraticContext:
    """Complete Quadratic-level context - everything the AI needs to understand the spreadsheet"""
    # Sheet identity
    sheet_name: str
    workbook_name: str = "Untitled"
    
    # Structural analysis
    sheet_structure: Dict[str, Any] = None
    used_range: Optional[str] = None
    total_cells: int = 0
    
    # Data intelligence
    data_regions: Dict[str, DataRegion] = field(default_factory=dict)
    named_ranges: Dict[str, Any] = field(default_factory=dict)
    
    # Formula intelligence  
    formula_summary: Dict[str, Any] = field(default_factory=dict)
    dependency_analysis: Dict[str, Any] = field(default_factory=dict)
    circular_references: List[str] = field(default_factory=list)
    
    # Relationship analysis
    cell_relationships: List[Dict[str, Any]] = field(default_factory=list)
    spill_ranges: Dict[str, str] = field(default_factory=dict)
    
    # Quality metrics
    data_quality_score: float = 0.0
    complexity_score: float = 0.0
    
    # AI-ready insights
    intelligent_suggestions: List[str] = field(default_factory=list)
    operation_recommendations: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    
    # Sample data for AI
    representative_sample: Dict[str, Any] = field(default_factory=dict)
    column_profiles: List[ColumnProfile] = field(default_factory=list)
    
    # Metadata
    last_analysis: datetime = field(default_factory=datetime.now)
    analysis_duration: float = 0.0

class QuadraticContextBuilder:
    """Builds Quadratic-level context from Google Sheets data"""
    
    def __init__(self, sheets_manager):
        self.sheets_manager = sheets_manager
        self.a1_handler = A1NotationHandler()
        
        # Single superior analyzer that contains all advanced capabilities
        self.superior_analyzer = SuperiorCellContextAnalyzer()
        
        # Dependency tracking
        self.dependency_tracker = DependencyTracker()
        self.spill_tracker = SpillTracker()
        
        # Configuration
        self.max_analysis_cells = 50000
        self.max_sample_rows = 10
        
    def build_context(self, worksheet_name: str, 
                     selection: Optional[str] = None,
                     force_refresh: bool = True) -> QuadraticContext:
        """Build comprehensive Quadratic-level context"""
        
        start_time = datetime.now()
        logger.info(f"🧠 Building Quadratic-level context for '{worksheet_name}'")
        
        try:
            # Get enhanced data from Google Sheets
            grid = self.sheets_manager.get_enhanced_data(worksheet_name, force_refresh=force_refresh)
            
            if not grid.cells:
                return self._create_empty_context(worksheet_name)
            
            # Build sheet structure using superior analysis
            sheet_structure = self._build_sheet_structure_superior(grid)
            
            # Analyze data regions with superior intelligence
            data_regions = self._analyze_data_regions_superior(sheet_structure)
            
            # Analyze formulas and dependencies
            formula_analysis = self._analyze_formulas_superior(grid)
            
            # Analyze relationships
            relationships = self._analyze_relationships_superior(sheet_structure, formula_analysis)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics_superior(sheet_structure, data_regions)
            
            # Generate AI insights
            ai_insights = self._generate_ai_insights_superior(
                sheet_structure, data_regions, formula_analysis, relationships
            )
            
            # Create representative sample
            sample_data = self._create_representative_sample_superior(grid, data_regions)
            
            # Build final context
            context = QuadraticContext(
                sheet_name=worksheet_name,
                sheet_structure=sheet_structure,
                used_range=sheet_structure.get('used_range', 'A1:A1'),
                total_cells=sheet_structure.get('total_cells', 0),
                data_regions=data_regions,
                formula_summary=formula_analysis.get('summary', {}),
                dependency_analysis=formula_analysis.get('dependencies', {}),
                circular_references=formula_analysis.get('circular_refs', []),
                cell_relationships=relationships,
                spill_ranges=formula_analysis.get('spill_ranges', {}),
                data_quality_score=quality_metrics['overall_quality'],
                complexity_score=quality_metrics['complexity'],
                intelligent_suggestions=ai_insights['suggestions'],
                operation_recommendations=ai_insights['operations'],
                potential_issues=ai_insights['issues'],
                representative_sample=sample_data,
                column_profiles=self._create_column_profiles_superior(grid, data_regions)
            )
            
            # Calculate analysis duration
            end_time = datetime.now()
            context.analysis_duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Context built in {context.analysis_duration:.2f}s - "
                       f"{context.total_cells} cells, {len(context.data_regions)} regions")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error building context for '{worksheet_name}': {e}", exc_info=True)
            return self._create_error_context(worksheet_name, str(e))
    
    def _build_sheet_structure_superior(self, grid: SpreadsheetGrid) -> Dict[str, Any]:
        """Build comprehensive sheet structure using superior analysis"""
        
        analyzed_cells = grid.cells
        
        # Detect data regions using superior analysis
        data_regions = self._detect_data_regions_superior(analyzed_cells)
        
        # Extract formula cells with superior analysis
        formula_cells = {}
        for address, cell in analyzed_cells.items():
            if cell.cell_type == CellType.FORMULA and cell.formula:
                formula_info = self.dependency_tracker.add_formula(address, cell.formula)
                formula_cells[address] = formula_info
        
        # Calculate superior metrics
        total_cells = len(analyzed_cells)
        formula_cells_count = len(formula_cells)
        error_cells = sum(1 for cell in analyzed_cells.values() if cell.cell_type == CellType.ERROR)
        
        structure = {
            'sheet_name': grid.sheet_name,
            'total_rows': max(cell.coordinate[0] for cell in analyzed_cells.values()) + 1 if analyzed_cells else 0,
            'total_cols': max(cell.coordinate[1] for cell in analyzed_cells.values()) + 1 if analyzed_cells else 0,
            'used_range': grid.used_range.a1_notation if grid.used_range else "A1:A1",
            'total_cells': total_cells,
            'formula_cells': formula_cells_count,
            'error_cells': error_cells,
            'data_density': self._calculate_data_density_superior(analyzed_cells),
            'formula_density': formula_cells_count / total_cells if total_cells > 0 else 0,
            'complexity_score': self._calculate_sheet_complexity_superior(analyzed_cells, formula_cells),
            'cells': analyzed_cells,
            'data_regions': data_regions,
            'formula_cells': formula_cells
        }
        
        return structure
    
    def _detect_data_regions_superior(self, cells: Dict[str, SuperiorCellInfo]) -> Dict[str, DataRegion]:
        """Detect data regions using superior analysis"""
        
        regions = {}
        region_id = 1
        
        # Group cells by proximity and type
        processed_cells = set()
        
        for address, cell in cells.items():
            if address in processed_cells:
                continue
            
            # Find connected region
            region_cells = self._find_connected_region(address, cells, processed_cells)
            if region_cells:
                # Create data region
                region = self._create_data_region_superior(region_cells, f"region_{region_id}")
                regions[f"region_{region_id}"] = region
                region_id += 1
                
                # Mark cells as processed
                processed_cells.update(region_cells.keys())
        
        return regions
    
    def _find_connected_region(self, start_address: str, cells: Dict[str, SuperiorCellInfo], 
                              processed: Set[str]) -> Dict[str, SuperiorCellInfo]:
        """Find all cells connected to the start address"""
        
        region_cells = {}
        to_process = [start_address]
        
        while to_process:
            current = to_process.pop(0)
            if current in processed or current not in cells:
                continue
            
            cell = cells[current]
            region_cells[current] = cell
            processed.add(current)
            
            # Find adjacent cells
            row, col = cell.coordinate
            adjacent = []
            
            # Only add adjacent cells if they're within bounds
            if row > 0:
                adjacent.append(self.a1_handler.to_a1(row-1, col))
            if row < 1000:
                adjacent.append(self.a1_handler.to_a1(row+1, col))
            if col > 0:
                adjacent.append(self.a1_handler.to_a1(row, col-1))
            if col < 100:
                adjacent.append(self.a1_handler.to_a1(row, col+1))
            
            for adj in adjacent:
                if adj in cells and adj not in processed:
                    to_process.append(adj)
        
        return region_cells
    
    def _create_data_region_superior(self, cells: Dict[str, SuperiorCellInfo], 
                                   region_id: str) -> DataRegion:
        """Create a data region using superior analysis"""
        
        if not cells:
            return DataRegion(region_id=region_id)
        
        # Calculate bounds
        rows = [cell.coordinate[0] for cell in cells.values()]
        cols = [cell.coordinate[1] for cell in cells.values()]
        
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)
        
        top_left = self.a1_handler.to_a1(min_row, min_col)
        bottom_right = self.a1_handler.to_a1(max_row, max_col)
        
        # Analyze cell types using superior analysis
        cell_types = [cell.cell_type for cell in cells.values()]
        type_distribution = {}
        for cell_type in cell_types:
            type_distribution[cell_type.value] = type_distribution.get(cell_type.value, 0) + 1
        
        # Determine region type based on superior analysis
        region_type = "table"
        if len(cells) > 10 and CellType.FORMULA in cell_types:
            region_type = "data_table"
        elif len(cells) <= 4:
            region_type = "small_data"
        
        # Calculate quality score using superior analysis
        quality_score = 1.0
        error_cells = sum(1 for cell in cells.values() if cell.cell_type == CellType.ERROR)
        if cells:
            quality_score = 1.0 - (error_cells / len(cells))
        
        # Sample data
        sample_data = [cell.raw_value for cell in list(cells.values())[:5]]
        
        # Generate suggestions using superior analysis
        suggestions = self._generate_region_suggestions_superior(cells, region_type)
        
        # Create column profiles for this region using superior analysis
        column_profiles = self._create_region_column_profiles(cells, min_row, max_row, min_col, max_col)
        
        return DataRegion(
            region_id=region_id,
            region_type=region_type,
            top_left=top_left,
            bottom_right=bottom_right,
            total_cells=len(cells),
            data_quality_score=quality_score,
            sample_data=sample_data,
            suggested_operations=suggestions,
            column_profiles=column_profiles
        )
    
    def _create_region_column_profiles(self, cells: Dict[str, SuperiorCellInfo], 
                                     min_row: int, max_row: int, min_col: int, max_col: int) -> List[ColumnProfile]:
        """Create column profiles for a specific region"""
        
        column_profiles = []
        
        for col in range(min_col, max_col + 1):
            col_data = []
            for row in range(min_row, max_row + 1):
                address = self.a1_handler.to_a1(row, col)
                if address in cells:
                    col_data.append(cells[address].raw_value)
                else:
                    col_data.append(None)
            
            # Create column profile using superior profiler
            column_name = f"Column_{chr(ord('A') + col)}" if col < 26 else f"Column_{col}"
            if col_data:
                profile = self.superior_analyzer.profiler.profile_column(col_data, column_name)
                profile.column_index = col
                profile.column_name = column_name
                column_profiles.append(profile)
        
        return column_profiles
    
    def _generate_region_suggestions_superior(self, cells: Dict[str, SuperiorCellInfo], 
                                           region_type: str) -> List[str]:
        """Generate intelligent suggestions for a region using superior analysis"""
        
        suggestions = []
        
        # Analyze cell types using superior analysis
        cell_types = [cell.cell_type for cell in cells.values()]
        semantic_types = [cell.semantic_type for cell in cells.values()]
        
        # Formula suggestions
        formula_cells = [cell for cell in cells.values() if cell.cell_type == CellType.FORMULA]
        if formula_cells:
            suggestions.append("Review formula complexity")
        
        # Data type suggestions based on semantic analysis
        if CellType.NUMBER in cell_types:
            suggestions.append("Perform statistical analysis")
        
        if DataSemanticType.EMAIL in semantic_types:
            suggestions.append("Validate email addresses")
        
        if DataSemanticType.CURRENCY_VALUE in semantic_types:
            suggestions.append("Format as currency")
        
        # Quality suggestions
        error_cells = [cell for cell in cells.values() if cell.cell_type == CellType.ERROR]
        if error_cells:
            suggestions.append("Fix data errors")
        
        return suggestions
    
    def _analyze_data_regions_superior(self, sheet_structure: Dict[str, Any]) -> Dict[str, DataRegion]:
        """Enhanced analysis of data regions using superior intelligence"""
        
        enhanced_regions = {}
        
        for region_id, region in sheet_structure.get('data_regions', {}).items():
            # Enhance region with additional analysis
            enhanced_region = self._enhance_data_region_superior(region, sheet_structure)
            enhanced_regions[region_id] = enhanced_region
        
        return enhanced_regions
    
    def _enhance_data_region_superior(self, region: DataRegion, 
                                    sheet_structure: Dict[str, Any]) -> DataRegion:
        """Add enhanced analysis to a data region using superior intelligence"""
        
        try:
            top_left_ref = self.a1_handler.parse_reference(region.top_left)
            bottom_right_ref = self.a1_handler.parse_reference(region.bottom_right)
            
            if isinstance(top_left_ref, CellReference) and isinstance(bottom_right_ref, CellReference):
                
                # Analyze each column if not already done
                if not hasattr(region, 'column_profiles') or not region.column_profiles:
                    column_profiles = []
                    for col in range(top_left_ref.col, bottom_right_ref.col + 1):
                        col_profile_dict = self._analyze_column_in_region_superior(
                            col, top_left_ref.row, bottom_right_ref.row, sheet_structure
                        )
                        
                        # Convert dictionary to ColumnProfile object
                        profile = self._dict_to_column_profile(col_profile_dict)
                        column_profiles.append(profile)
                    
                    region.column_profiles = column_profiles
                
                # Generate better suggestions
                region.suggested_operations = self._suggest_region_operations_superior(region, region.column_profiles)
        
        except Exception as e:
            logger.error(f"Error enhancing region {region.region_id}: {e}")
        
        return region
    
    def _dict_to_column_profile(self, col_dict: Dict[str, Any]) -> ColumnProfile:
        """Convert column analysis dictionary to ColumnProfile object"""
        
        profile = ColumnProfile(
            column_index=col_dict.get('column_index', 0),
            column_name=col_dict.get('column_name', 'Unknown'),
            total_cells=col_dict.get('total_cells', 0),
            non_empty_cells=col_dict.get('non_empty_cells', 0)
        )
        
        # Set semantic type
        semantic_types = col_dict.get('semantic_types', [])
        if semantic_types:
            # Try to map string to enum
            try:
                profile.semantic_type = DataSemanticType(semantic_types[0])
            except ValueError:
                profile.semantic_type = DataSemanticType.UNKNOWN
        
        # Set backward compatibility attributes
        profile.inferred_type = profile.semantic_type
        profile.unique_values = len(set(col_dict.get('sample_values', [])))
        profile.quality_score = col_dict.get('quality_score', 1.0)
        
        # Build stats dictionary for backward compatibility
        profile.stats = {
            'count': profile.non_empty_cells,
            'unique_count': profile.unique_values,
            'mean': None,
            'median': None,
            'std': None,
            'variance': None,
            'min': None,
            'max': None,
            'sum': None,
            'average': None
        }
        
        return profile
    
    def _analyze_column_in_region_superior(self, col: int, start_row: int, end_row: int, 
                                         sheet_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single column within a region using superior intelligence"""
        
        col_data = []
        cell_types = []
        semantic_types = []
        
        for row in range(start_row, end_row + 1):
            address = self.a1_handler.to_a1(row, col)
            cell = sheet_structure['cells'].get(address)
            
            if cell:
                col_data.append(cell.raw_value)
                cell_types.append(cell.cell_type)
                semantic_types.append(cell.semantic_type)
            else:
                col_data.append(None)
                cell_types.append(CellType.EMPTY)
                semantic_types.append(DataSemanticType.UNKNOWN)
        
        # Analyze column characteristics using superior profiler
        non_empty_data = [d for d in col_data if d is not None and d != ""]
        
        return {
            'column_index': col,
            'column_name': f"Column_{chr(ord('A') + col)}" if col < 26 else f"Column_{col}",
            'total_cells': len(col_data),
            'non_empty_cells': len(non_empty_data),
            'data_types': list(set(ct.value for ct in cell_types)),
            'semantic_types': list(set(st.value for st in semantic_types)),
            'sample_values': non_empty_data[:3],
            'has_header': start_row == 0,
            'data_pattern': self._detect_column_pattern_superior(non_empty_data),
            'quality_score': len(non_empty_data) / len(col_data) if col_data else 0
        }
    
    def _detect_column_pattern_superior(self, data: List[Any]) -> str:
        """Detect pattern in column data using superior analysis"""
        
        if not data:
            return "empty"
        
        # Use superior semantic type detection
        semantic_types = []
        for item in data:
            semantic_type = self.superior_analyzer.semantic_detector.detect_semantic_type(item)
            semantic_types.append(semantic_type)
        
        # Determine pattern based on semantic types
        if all(st == DataSemanticType.EMAIL for st in semantic_types):
            return "email"
        elif all(st == DataSemanticType.CURRENCY_VALUE for st in semantic_types):
            return "currency"
        elif all(st == DataSemanticType.PERCENTAGE_VALUE for st in semantic_types):
            return "percentage"
        
        # Check for numeric pattern
        numeric_count = 0
        for item in data:
            try:
                float(str(item))
                numeric_count += 1
            except:
                pass
        
        if numeric_count / len(data) > 0.8:
            return "numeric"
        
        # Check for date pattern
        date_like = sum(1 for item in data if self._looks_like_date(str(item)))
        if date_like / len(data) > 0.5:
            return "date"
        
        # Check for categorical pattern
        unique_ratio = len(set(str(item) for item in data)) / len(data)
        if unique_ratio < 0.1:
            return "categorical"
        
        return "text"
    
    def _looks_like_date(self, value: str) -> bool:
        """Check if value looks like a date"""
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
    def _analyze_formulas_superior(self, grid: SpreadsheetGrid) -> Dict[str, Any]:
        """Comprehensive formula analysis using superior intelligence"""
        
        report = self.dependency_tracker.generate_dependency_report()
        formula_stats = report['summary']
        circular_refs = report['circular_references']
        
        # Get spill information
        spill_ranges = {}
        for address, cell in grid.cells.items():
            spill_range = grid.find_spill_range(address)
            if spill_range:
                spill_ranges[address] = spill_range
        
        return {
            'summary': formula_stats,
            'dependencies': {
                'total_dependencies': formula_stats.get('total_dependencies', 0),
                'circular_references': len(circular_refs)
            },
            'circular_refs': circular_refs,
            'spill_ranges': spill_ranges
        }
    
    def _analyze_relationships_superior(self, sheet_structure: Dict[str, Any], 
                             formula_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze relationships between data elements using superior intelligence"""
        
        relationships = []
        
        # Formula-data relationships
        for address, formula_info in sheet_structure.get('formula_cells', {}).items():
            for ref in formula_info.direct_refs:
                relationships.append({
                    'type': 'formula_dependency',
                    'source': address,
                    'target': ref,
                    'strength': 1.0,
                    'description': f"Formula in {address} references {ref}"
                })
        
        # Data region relationships (simplified)
        region_list = list(sheet_structure.get('data_regions', {}).values())
        for i, region1 in enumerate(region_list):
            for region2 in region_list[i+1:]:
                if self._regions_are_related_superior(region1, region2):
                    relationships.append({
                        'type': 'data_region_relationship',
                        'source': region1.region_id,
                        'target': region2.region_id,
                        'strength': 0.5,
                        'description': f"Regions {region1.region_id} and {region2.region_id} are related"
                    })
        
        return relationships
    
    def _regions_are_related_superior(self, region1: DataRegion, region2: DataRegion) -> bool:
        """Check if two regions are related using superior analysis"""
        
        try:
            r1_ref = self.a1_handler.parse_reference(f"{region1.top_left}:{region1.bottom_right}")
            r2_ref = self.a1_handler.parse_reference(f"{region2.top_left}:{region2.bottom_right}")
            
            if isinstance(r1_ref, RangeReference) and isinstance(r2_ref, RangeReference):
                # Simple adjacency check
                return abs(r1_ref.start_cell.row - r2_ref.end_cell.row) <= 2 or \
                       abs(r1_ref.start_cell.col - r2_ref.end_cell.col) <= 2
        
        except:
            pass
        
        return False
    
    def _calculate_quality_metrics_superior(self, sheet_structure: Dict[str, Any], 
                                  data_regions: Dict[str, DataRegion]) -> Dict[str, float]:
        """Calculate comprehensive quality metrics using superior analysis"""
        
        # Overall data quality
        total_cells = sheet_structure.get('total_cells', 0)
        error_cells = sheet_structure.get('error_cells', 0)
        
        overall_quality = 1.0 - (error_cells / total_cells) if total_cells > 0 else 0.0
        
        # Region quality
        if data_regions:
            region_qualities = [region.data_quality_score for region in data_regions.values()]
            overall_quality = (overall_quality + sum(region_qualities) / len(region_qualities)) / 2
        
        # Complexity calculation
        complexity = 0.0
        complexity += min(1.0, total_cells / 1000) * 0.3  # Size complexity
        formula_cells = sheet_structure.get('formula_cells', 0)
        if isinstance(formula_cells, dict):
            formula_cells = len(formula_cells)
        complexity += min(1.0, formula_cells / 100) * 0.4  # Formula complexity
        complexity += min(1.0, len(data_regions) / 10) * 0.3  # Structure complexity
        
        return {
            'overall_quality': overall_quality,
            'complexity': complexity,
            'error_ratio': error_cells / total_cells if total_cells > 0 else 0.0
        }
    
    def _generate_ai_insights_superior(self, sheet_structure: Dict[str, Any], 
                            data_regions: Dict[str, DataRegion],
                            formula_analysis: Dict[str, Any],
                            relationships: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate intelligent suggestions for AI using superior analysis"""
        
        suggestions = []
        operations = []
        issues = []
        
        # Data region insights
        for region in data_regions.values():
            if region.region_type == "table":
                suggestions.append(f"Analyze tabular data in {region.region_id} ({region.top_left}:{region.bottom_right})")
                operations.extend(region.suggested_operations)
            
            elif region.region_type == "data_table":
                suggestions.append(f"Perform matrix operations on {region.region_id}")
                operations.append(f"correlation_analysis:{region.region_id}")
        
        # Formula insights
        if formula_analysis.get('circular_refs'):
            issues.extend([f"Circular reference detected: {' -> '.join(cycle)}" 
                          for cycle in formula_analysis['circular_refs']])
        
        complex_formulas = [addr for addr, info in sheet_structure.get('formula_cells', {}).items() 
                           if info.complexity_score > 5.0]
        if complex_formulas:
            suggestions.append(f"Review complex formulas: {', '.join(complex_formulas[:3])}")
        
        # Quality issues
        error_cells = [addr for addr, cell in sheet_structure.get('cells', {}).items() 
                      if cell.cell_type == CellType.ERROR]
        if error_cells:
            issues.append(f"Found {len(error_cells)} error cells")
            operations.append("fix_errors")
        
        # Relationship insights
        if len(relationships) > 10:
            suggestions.append("Sheet has complex relationships - consider simplification")
        
        return {
            'suggestions': suggestions[:5],  # Limit to top 5
            'operations': list(set(operations))[:5],
            'issues': issues[:3]
        }
    
    def _suggest_region_operations_superior(self, region: DataRegion, 
                                  column_profiles: List[ColumnProfile]) -> List[str]:
        """Suggest operations for a specific region using superior analysis"""
        
        operations = []
        
        if region.region_type == "table":
            # Check for numeric columns
            numeric_cols = sum(1 for profile in column_profiles 
                             if hasattr(profile, 'semantic_type') and profile.semantic_type == DataSemanticType.NUMERIC)
            
            if numeric_cols >= 2:
                operations.extend(['create_scatter_plot', 'correlation_analysis'])
            
            if numeric_cols >= 1:
                operations.extend(['calculate_statistics', 'create_histogram'])
            
            # Check for categorical columns  
            categorical_cols = sum(1 for profile in column_profiles 
                                 if hasattr(profile, 'semantic_type') and profile.semantic_type == DataSemanticType.CATEGORY)
            
            if categorical_cols >= 1 and numeric_cols >= 1:
                operations.append('create_pivot_table')
        
        elif region.region_type == "data_table":
            operations.extend(['matrix_operations', 'eigenvalue_analysis'])
        
        return operations
    
    def _create_representative_sample_superior(self, grid: SpreadsheetGrid, 
                                    data_regions: Dict[str, DataRegion]) -> Dict[str, Any]:
        """Create representative sample for AI context using superior analysis"""
        
        # Convert grid to DataFrame for compatibility
        df = grid.to_dataframe()
        
        sample = {
            'shape': df.shape,
            'columns': df.columns.tolist() if not df.empty else [],
            'dtypes': df.dtypes.to_dict() if not df.empty else {},
            'preview': df.head(self.max_sample_rows).to_dict('records') if not df.empty else [],
            'regions_sample': {}
        }
        
        # Add sample from each region
        for region_id, region in data_regions.items():
            sample['regions_sample'][region_id] = {
                'type': region.region_type,
                'size': region.total_cells,
                'quality': region.data_quality_score,
                'sample_data': region.sample_data[:3]  # First 3 rows
            }
        
        return sample
    
    def _create_column_profiles_superior(self, grid: SpreadsheetGrid,
                                         data_regions: Dict[str, DataRegion]) -> List[ColumnProfile]:
        """Create detailed column profiles by aggregating from data regions."""
        
        all_profiles: List[ColumnProfile] = []
        # Use a set to track processed columns and avoid duplicates from overlapping regions
        processed_columns: Set[int] = set()
        
        # Prioritize larger regions to get more representative profiles
        sorted_regions = sorted(data_regions.values(), key=lambda r: r.total_cells, reverse=True)
        
        for region in sorted_regions:
            if region.column_profiles:
                for profile in region.column_profiles:
                    if profile.column_index not in processed_columns:
                        all_profiles.append(profile)
                        processed_columns.add(profile.column_index)

        # Sort by column index for a predictable order
        all_profiles.sort(key=lambda p: p.column_index)

        # Fallback for sheets with no detectable regions but with some data
        if not all_profiles and grid.cells:
            logger.warning("No column profiles found in data regions. Falling back to sheet-level profiling. This may be inaccurate.")
            # Critical change: Do not infer headers from potentially data-only sheets
            df = grid.to_dataframe(include_headers=False)
            if df.empty:
                return []
            
            profiles = []
            for i, _ in enumerate(df.columns):
                series = df.iloc[:, i].dropna()
                # Use a generic, safe column name
                col_name = f"Column_{chr(ord('A') + i)}"
                
                profile = self.superior_analyzer.profiler.profile_column(series.tolist(), col_name)
                profile.column_index = i
                profile.column_name = col_name
                
                profiles.append(profile)
            return profiles

        return all_profiles
    
    def _calculate_data_density_superior(self, cells: Dict[str, SuperiorCellInfo]) -> float:
        """Calculate data density of the sheet using superior analysis"""
        
        if not cells:
            return 0.0
        
        non_empty_cells = sum(1 for cell in cells.values() 
                             if cell.cell_type != CellType.EMPTY)
        
        # Estimate total possible cells (simplified)
        max_row = max(cell.coordinate[0] for cell in cells.values()) if cells else 0
        max_col = max(cell.coordinate[1] for cell in cells.values()) if cells else 0
        total_possible = (max_row + 1) * (max_col + 1)
        
        if total_possible == 0:
            return 0.0
        
        return min(1.0, non_empty_cells / total_possible)
    
    def _calculate_sheet_complexity_superior(self, cells: Dict[str, SuperiorCellInfo], 
                                           formula_cells: Dict[str, FormulaInfo]) -> float:
        """Calculate overall sheet complexity using superior analysis"""
        
        complexity = 0.0
        
        # Size factor
        total_cells = len(cells)
        complexity += min(1.0, total_cells / 10000) * 0.3
        
        # Formula factor
        formula_count = len(formula_cells)
        complexity += min(1.0, formula_count / 100) * 0.4
        
        # Cell type diversity factor
        cell_types = set(cell.cell_type for cell in cells.values())
        complexity += min(1.0, len(cell_types) / 5) * 0.3
        
        return complexity
    
    def _create_empty_context(self, worksheet_name: str) -> QuadraticContext:
        """Create context for empty sheet"""
        
        return QuadraticContext(
            sheet_name=worksheet_name,
            intelligent_suggestions=["Add data to get started"],
            operation_recommendations=["import_data", "create_sample_data"],
            potential_issues=["Sheet is empty"]
        )
    
    def _create_error_context(self, worksheet_name: str, error_msg: str) -> QuadraticContext:
        """Create context when analysis fails"""
        
        return QuadraticContext(
            sheet_name=worksheet_name,
            potential_issues=[f"Analysis failed: {error_msg}"],
            operation_recommendations=["retry_analysis", "check_sheet_access"]
        )

class ContextFormatter:
    """Formats Quadratic context for AI consumption"""
    
    @staticmethod
    def format_for_ai(context: QuadraticContext) -> str:
        """Format context as AI-readable prompt"""
        
        prompt = f"""QUADRATIC-LEVEL SPREADSHEET CONTEXT:

📊 SHEET: "{context.sheet_name}"
   Used Range: {context.used_range}
   Total Cells: {context.total_cells}
   Quality Score: {context.data_quality_score:.2f}
   Complexity: {context.complexity_score:.2f}

🗂️ DATA REGIONS ({len(context.data_regions)} found):"""
        
        for region_id, region in list(context.data_regions.items())[:3]:
            prompt += f"""
   {region_id}: {region.top_left}:{region.bottom_right}
   - Type: {region.region_type}
   - Quality: {region.data_quality_score:.2f}
   - Sample: {region.sample_data[0] if region.sample_data else 'No data'}"""
        
        if context.formula_summary:
            prompt += f"""

🔗 FORMULAS & DEPENDENCIES:
   Total Formulas: {context.formula_summary.get('total_formulas', 0)}
   Dependencies: {context.formula_summary.get('total_dependencies', 0)}
   Circular Refs: {len(context.circular_references)}"""
        
        if context.cell_relationships:
            prompt += f"""

🔄 RELATIONSHIPS ({len(context.cell_relationships)} found):"""
            for rel in context.cell_relationships[:2]:
                prompt += f"""
   {rel['source']} → {rel['target']} ({rel['type']})"""
        
        if context.intelligent_suggestions:
            prompt += f"""

💡 INTELLIGENT SUGGESTIONS:"""
            for suggestion in context.intelligent_suggestions:
                prompt += f"\n   • {suggestion}"
        
        if context.potential_issues:
            prompt += f"""

⚠️ POTENTIAL ISSUES:"""
            for issue in context.potential_issues:
                prompt += f"\n   • {issue}"
        
        prompt += f"""

📈 COLUMN PROFILES:"""
        for profile in context.column_profiles[:5]:
            semantic_type_str = profile.semantic_type.value if hasattr(profile.semantic_type, 'value') else str(profile.semantic_type)
            unique_values = getattr(profile, 'unique_values', 0)
            prompt += f"""
   {profile.column_name}: {semantic_type_str} ({unique_values} unique)"""
        
        return prompt
    
    @staticmethod  
    def format_for_tools(context: QuadraticContext) -> Dict[str, Any]:
        """Format context for tool selection"""
        
        return {
            'available_operations': context.operation_recommendations,
            'data_regions': [
                {
                    'id': region_id,
                    'range': f"{region.top_left}:{region.bottom_right}",
                    'type': region.region_type,
                    'suggested_ops': region.suggested_operations
                }
                for region_id, region in context.data_regions.items()
            ],
            'sheet_metrics': {
                'quality': context.data_quality_score,
                'complexity': context.complexity_score,
                'has_formulas': len(context.formula_summary) > 0,
                'has_errors': len(context.potential_issues) > 0
            }
        }