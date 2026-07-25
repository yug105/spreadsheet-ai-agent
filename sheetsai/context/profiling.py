"""
Advanced data profiling and semantic type detection - FIXED VERSION
"""

import pandas as pd
import re
import statistics
import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional
import warnings

from datetime import datetime

from .shared_types import (
    CellType, DataSemanticType, ColumnProfile, 
    Coordinate, EnhancedEvaluationResult
)

logger = logging.getLogger(__name__)

# For advanced statistics
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy not available. Install with: pip install scipy")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    warnings.warn("numpy not available. Install with: pip install numpy")

class SemanticTypeDetector:
    """Detect semantic types of data"""
    
    def __init__(self):
        self.patterns = {
            DataSemanticType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            DataSemanticType.PHONE: r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            DataSemanticType.URL: r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
            DataSemanticType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            DataSemanticType.SOCIAL_SECURITY: r'\b\d{3}-\d{2}-\d{4}\b',
            DataSemanticType.CREDIT_CARD: r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9]{2})[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})\b',
            DataSemanticType.COORDINATES: r'^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$',
            DataSemanticType.CURRENCY_VALUE: r'^\$?\s*\d{1,3}(?:[,\.]\d{3})*(?:\.\d{1,2})?$',
            DataSemanticType.PERCENTAGE_VALUE: r'^-?\d+\.?\d*\s*%$',
            DataSemanticType.DATE: r'^(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2})$',
            DataSemanticType.BOOLEAN: r'^(TRUE|FALSE|YES|NO)$',
        }
        
        self.compiled_patterns = {
            semantic_type: re.compile(pattern, re.IGNORECASE)
            for semantic_type, pattern in self.patterns.items()
        }
    
    def detect_semantic_type(self, value: Any) -> DataSemanticType:
        """Detect the semantic type of a value"""
        
        if value is None:
            return DataSemanticType.UNKNOWN
        
        value_str = str(value).strip()

        if not value_str:
            return DataSemanticType.EMPTY
        
        # Try direct type checks first
        if isinstance(value, bool):
            return DataSemanticType.BOOLEAN
        if isinstance(value, (int, float)):
            if value > 1_000_000_000 and len(str(int(value))) > 10:
                return DataSemanticType.IDENTIFIER
            return DataSemanticType.NUMERIC

        # Check against patterns
        for semantic_type, pattern in self.compiled_patterns.items():
            if semantic_type == DataSemanticType.DATE:
                try:
                    pd.to_datetime(value_str, errors='raise')
                    return DataSemanticType.DATE
                except:
                    continue
            
            if semantic_type == DataSemanticType.BOOLEAN:
                if pattern.match(value_str.upper()):
                    return DataSemanticType.BOOLEAN
            
            if pattern.search(value_str):
                return semantic_type

        # Additional heuristics for string values
        if isinstance(value, str):
            cleaned_value_for_numeric = value_str.replace('$', '').replace('%', '').replace(',', '')
            try:
                float(cleaned_value_for_numeric)
                if not any(p.search(value_str) for st, p in self.compiled_patterns.items() if st in [DataSemanticType.CURRENCY_VALUE, DataSemanticType.PERCENTAGE_VALUE, DataSemanticType.DATE]):
                    return DataSemanticType.NUMERIC
            except ValueError:
                pass

            if value_str.isupper() and len(value_str) <= 10 and len(value_str) >= 2:
                return DataSemanticType.CATEGORY
            
            if len(value_str) > 5 and re.match(r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]+$', value_str):
                return DataSemanticType.IDENTIFIER

        return DataSemanticType.UNKNOWN

class AdvancedDataProfiler:
    """Advanced data profiling for columns and regions"""
    
    def __init__(self):
        self.semantic_detector = SemanticTypeDetector()
    
    def profile_column(self, values: List[Any], column_name: str = None) -> ColumnProfile:
        """Create a comprehensive column profile with advanced analysis"""
        
        if not values:
            return ColumnProfile(column_index=0, column_name=column_name or "Empty Column")
        
        # Basic statistics
        non_empty_values = [v for v in values if v is not None and v != ""]
        total_cells = len(values)
        non_empty_cells = len(non_empty_values)
        unique_values = len(set(str(v) for v in non_empty_values))
        
        # Create profile
        profile = ColumnProfile(
            column_index=0,  # Will be set by caller
            column_name=column_name or "Column",
            total_cells=total_cells,
            non_empty_cells=non_empty_cells,
            unique_values=unique_values,
            null_percentage=(total_cells - non_empty_cells) / total_cells if total_cells > 0 else 0.0
        )
        
        # Type distribution analysis
        profile.type_distribution = self._analyze_type_distribution(values)
        
        # Semantic type detection
        profile.semantic_type = self._determine_semantic_type_from_cells(values)
        profile.inferred_type = profile.semantic_type  # For backward compatibility
        
        # Build stats dictionary
        profile.stats = self._build_stats_dict(profile)
        
        # Add numeric statistics if applicable
        numeric_values = self._extract_numeric_values(values)
        if numeric_values:
            profile = self._add_numeric_statistics(profile, numeric_values)
        
        # Add string statistics if applicable
        string_values = self._extract_string_values(values)
        if string_values:
            profile = self._add_string_statistics(profile, string_values)
        
        # Analyze patterns
        profile.common_patterns = self._analyze_patterns(values)
        
        # Analyze quality
        profile = self._analyze_quality(profile, values)
        
        return profile
    
    def _build_stats_dict(self, profile: ColumnProfile) -> Dict[str, Any]:
        """Build backward-compatible stats dictionary"""
        return {
            'count': profile.non_empty_cells,
            'unique_count': profile.unique_values,
            'mean': profile.mean,
            'median': profile.median,
            'std': profile.std_dev,
            'variance': profile.variance,
            'min': profile.min_value,
            'max': profile.max_value,
            'sum': profile.mean * profile.non_empty_cells if profile.mean else None,
            'average': profile.mean  # Alias for mean
        }
    
    def _analyze_type_distribution(self, values: List[Any]) -> Dict[CellType, int]:
        """Analyze type distribution in values"""
        
        type_counts = defaultdict(int)
        
        for value in values:
            if isinstance(value, bool):
                type_counts[CellType.BOOLEAN] += 1
            elif isinstance(value, (int, float)):
                type_counts[CellType.NUMBER] += 1
            elif isinstance(value, datetime):
                type_counts[CellType.DATETIME] += 1
            elif isinstance(value, str):
                if value.startswith('='):
                    type_counts[CellType.FORMULA] += 1
                elif value.startswith('#'):
                    type_counts[CellType.ERROR] += 1
                else:
                    try:
                        float(value.replace(',', ''))
                        type_counts[CellType.NUMBER] += 1
                    except ValueError:
                        type_counts[CellType.TEXT] += 1
            else:
                type_counts[CellType.TEXT] += 1
        
        return dict(type_counts)
    
    def _determine_semantic_type_from_cells(self, values: List[Any]) -> DataSemanticType:
        """Determine the most likely semantic type for a column based on cell analyses."""
        
        semantic_counts = defaultdict(int)
        
        for value in values:
            semantic_type = self.semantic_detector.detect_semantic_type(value)
            semantic_counts[semantic_type] += 1
        
        semantic_counts.pop(DataSemanticType.EMPTY, None)
        
        total_classified_cells = sum(semantic_counts.values())
        
        if not semantic_counts or total_classified_cells == 0:
            unique_non_empty_values = [v for v in values if v is not None and str(v).strip()]
            if not unique_non_empty_values:
                return DataSemanticType.EMPTY
            
            unique_ratio = len(set(str(v).strip() for v in unique_non_empty_values)) / len(unique_non_empty_values) if unique_non_empty_values else 0

            if unique_ratio < 0.15 and len(unique_non_empty_values) > 1:
                numeric_elements_ratio = sum(1 for v in unique_non_empty_values if isinstance(v, (int, float))) / len(unique_non_empty_values)
                if numeric_elements_ratio < 0.5:
                     return DataSemanticType.CATEGORY

            if unique_ratio > 0.8 and len(unique_non_empty_values) > 1:
                alphanumeric_count = sum(1 for v in unique_non_empty_values if isinstance(v, str) and re.match(r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]+$', v))
                if alphanumeric_count / len(unique_non_empty_values) > 0.5:
                    return DataSemanticType.IDENTIFIER

            return DataSemanticType.UNKNOWN
        
        # Get the most common semantic type
        most_common_type = max(semantic_counts.items(), key=lambda item: item[1])[0]
        
        majority_threshold = 0.7
        if semantic_counts[most_common_type] / total_classified_cells < majority_threshold:
            if len(semantic_counts) > 1:
                return DataSemanticType.MIXED
            return DataSemanticType.UNKNOWN
        
        return most_common_type
    
    def _extract_numeric_values(self, values: List[Any]) -> List[float]:
        """Extract numeric values for statistical analysis"""
        
        numeric_values = []
        
        for value in values:
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))
            elif isinstance(value, str):
                try:
                    cleaned = re.sub(r'[,$%]', '', value)
                    numeric_values.append(float(cleaned))
                except ValueError:
                    continue
        
        return numeric_values
    
    def _extract_string_values(self, values: List[Any]) -> List[str]:
        """Extract string values for text analysis"""
        
        return [str(value) for value in values if not isinstance(value, (int, float))]
    
    def _add_numeric_statistics(self, profile: ColumnProfile, numeric_values: List[float]) -> ColumnProfile:
        """Add numeric statistics to profile"""
        
        if not numeric_values:
            return profile
        
        profile.min_value = min(numeric_values)
        profile.max_value = max(numeric_values)
        profile.mean = statistics.mean(numeric_values)
        
        if len(numeric_values) > 1:
            profile.median = statistics.median(numeric_values)
            profile.std_dev = statistics.stdev(numeric_values)
            profile.variance = statistics.variance(numeric_values)

            # Guard against precision errors for data with no variance
            if SCIPY_AVAILABLE and NUMPY_AVAILABLE and profile.variance > 1e-9:
                try:
                    profile.skewness = float(stats.skew(numeric_values))
                    profile.kurtosis = float(stats.kurtosis(numeric_values))
                except:
                    pass
            
            try:
                profile.mode = statistics.mode(numeric_values)
            except statistics.StatisticsError:
                pass
        
        # Outlier detection using IQR method
        if len(numeric_values) > 4 and NUMPY_AVAILABLE:
            q1 = np.percentile(numeric_values, 25)
            q3 = np.percentile(numeric_values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            profile.outlier_count = sum(1 for v in numeric_values 
                                      if v < lower_bound or v > upper_bound)
        
        return profile
    
    def _add_string_statistics(self, profile: ColumnProfile, string_values: List[str]) -> ColumnProfile:
        """Add string statistics to profile"""
        
        if not string_values:
            return profile
        
        lengths = [len(s) for s in string_values]
        profile.avg_string_length = statistics.mean(lengths)
        profile.max_string_length = max(lengths)
        profile.min_string_length = min(lengths)
        
        # Unique values
        profile.unique_values = len(set(string_values))
        
        return profile
    
    def _analyze_patterns(self, values: List[Any]) -> List[str]:
        """Analyze common patterns in the data"""
        
        patterns = []
        
        string_values = [str(v) for v in values if str(v).strip()]
        
        if string_values:
            lengths = [len(s) for s in string_values]
            most_common_length = statistics.mode(lengths) if len(set(lengths)) < len(lengths) else None
            
            if most_common_length:
                patterns.append(f"Fixed length: {most_common_length}")
            
            if all(s.isupper() for s in string_values):
                patterns.append("All uppercase")
            elif all(s.islower() for s in string_values):
                patterns.append("All lowercase")
            elif all(s.istitle() for s in string_values):
                patterns.append("Title case")
        
        return patterns
    
    def _analyze_quality(self, profile: ColumnProfile, values: List[Any]) -> ColumnProfile:
        """Analyzes the column for common data quality issues and generates proactive warnings."""
        total_count = len(values)
        if total_count == 0:
            return profile

        # Check for high percentage of empty cells
        empty_count = profile.type_distribution.get(CellType.EMPTY, 0)
        if (empty_count / total_count) > 0.5:
            profile.quality_warnings.append(f"High proportion of empty cells ({empty_count}/{total_count}).")

        # Check for mixed types in a predominantly numeric or text column
        if profile.semantic_type == DataSemanticType.NUMERIC and profile.type_distribution.get(CellType.TEXT, 0) > 0:
            text_count = profile.type_distribution.get(CellType.TEXT, 0)
            profile.quality_warnings.append(f"Mixed data types: Column is mostly numeric but contains {text_count} text value(s).")
        
        # Check for high cardinality in categorical data
        if profile.semantic_type == DataSemanticType.CATEGORY and profile.unique_values > 20 and (profile.unique_values / total_count) > 0.8:
             profile.quality_warnings.append(f"High cardinality ({profile.unique_values} unique values); may not be a true category.")

        # Check for potential outliers in numeric data
        if profile.semantic_type == DataSemanticType.NUMERIC and profile.std_dev and profile.mean:
            numeric_values = self._extract_numeric_values(values)
            if numeric_values:
                # Use 2 standard deviations as outlier threshold
                outlier_threshold = 2 * profile.std_dev
                outliers = [v for v in numeric_values if abs(v - profile.mean) > outlier_threshold]
                if outliers:
                    profile.quality_warnings.append(f"Potential outliers detected: {len(outliers)} values outside 2 standard deviations.")

        # Check for inconsistent formatting in text data
        if profile.semantic_type in [DataSemanticType.NAME, DataSemanticType.IDENTIFIER, DataSemanticType.EMAIL, DataSemanticType.PHONE, DataSemanticType.ADDRESS, DataSemanticType.URL]:
            # Check for mixed case patterns
            case_patterns = set()
            for value in values:
                if isinstance(value, str) and value.strip():
                    if value.isupper():
                        case_patterns.add("uppercase")
                    elif value.islower():
                        case_patterns.add("lowercase")
                    elif value.istitle():
                        case_patterns.add("titlecase")
                    else:
                        case_patterns.add("mixed")
            
            if len(case_patterns) > 1:
                profile.quality_warnings.append(f"Inconsistent text formatting: mixed case patterns detected.")

        # Check for potential date/time inconsistencies
        if profile.semantic_type == DataSemanticType.DATE:
            # This would be enhanced with actual date parsing logic
            profile.quality_warnings.append("Date column detected - verify date formats are consistent.")

        # Check for potential currency inconsistencies
        if profile.semantic_type == DataSemanticType.CURRENCY_VALUE:
            # Check for mixed currency symbols
            currency_symbols = set()
            for value in values:
                if isinstance(value, str):
                    if '$' in value:
                        currency_symbols.add('$')
                    if '€' in value:
                        currency_symbols.add('€')
                    if '£' in value:
                        currency_symbols.add('£')
            
            if len(currency_symbols) > 1:
                profile.quality_warnings.append(f"Mixed currency symbols detected: {', '.join(currency_symbols)}")

        return profile
    
    def _is_convertible_to_float(self, value_str: str) -> bool:
        """Helper to check if a string can be safely converted to float"""
        try:
            float(value_str.replace('$', '').replace('%', '').replace(',', '').strip())
            return True
        except ValueError:
            return False

    def _looks_like_date(self, value: str) -> bool:
        """Check if value looks like a date"""
        try:
            pd.to_datetime(value, errors='raise')
            return True
        except (ValueError, TypeError):
            return False