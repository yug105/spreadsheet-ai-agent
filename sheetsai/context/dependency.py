"""
Complete Dependency Tracking System
Provides advanced understanding of formula relationships and dependencies
"""

from typing import Dict, List, Set, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
from datetime import datetime
import networkx as nx

from ..a1_notation import A1NotationHandler, CellReference, RangeReference
from .shared_types import CellType, FormulaComplexity, Coordinate
from .formula_parsing import AdvancedFormulaParser

logger = logging.getLogger(__name__)

class DependencyType(Enum):
    """Types of dependencies between cells"""
    DIRECT = "direct"
    INDIRECT = "indirect"
    CIRCULAR = "circular"
    SPILL = "spill"
    VOLATILE = "volatile"
    ARRAY = "array"

@dataclass
class FormulaInfo:
    """Detailed information about a formula"""
    address: str
    formula_text: str
    formula_complexity: FormulaComplexity
    direct_refs: Set[str] = field(default_factory=set)
    range_refs: Set[str] = field(default_factory=set)
    named_refs: Set[str] = field(default_factory=set)
    external_refs: Set[str] = field(default_factory=set)
    complexity_score: float = 0.0
    is_array_formula: bool = False
    estimated_calc_time: float = 0.0
    has_errors: bool = False
    error_message: Optional[str] = None
    created: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class DependencyRelation:
    """Represents a dependency relationship between cells"""
    source: str
    target: str
    dependency_type: DependencyType
    strength: float = 1.0
    path: Tuple[str, ...] = field(default_factory=tuple)

class DependencyTracker:
    """Tracks dependencies between cells and formulas using advanced parsing"""
    
    def __init__(self):
        self.parser = AdvancedFormulaParser()
        self.a1_handler = A1NotationHandler()
        
        # Dependency graphs
        self.dependency_graph = nx.DiGraph()  # cell -> cells it depends on
        self.dependent_graph = nx.DiGraph()   # cell -> cells that depend on it
        
        # Formula tracking
        self.formulas: Dict[str, FormulaInfo] = {}
        self.calculation_order: List[str] = []
        
        # Analysis caches
        self.circular_refs: Set[Tuple[str, ...]] = set()
        self.volatile_cells: Set[str] = set()
        self.array_formulas: Dict[str, List[str]] = {}  # origin -> spill range
        
        # Performance tracking
        self.last_analysis: Optional[datetime] = None
        self.analysis_stats = {
            'total_formulas': 0,
            'circular_count': 0,
            'volatile_count': 0,
            'array_count': 0,
            'max_dependency_chain': 0
        }
    
    def add_formula(self, address: str, formula: str, 
                   cell_type: CellType = CellType.FORMULA) -> FormulaInfo:
        """Add a formula and track its dependencies"""
        
        try:
            # Parse the formula
            parsed = self.parser.parse_formula(formula)
            
            # Create formula info
            formula_info = FormulaInfo(
                address=address,
                formula_text=formula,
                formula_complexity=parsed.complexity,
                complexity_score=parsed.complexity_score,
                is_array_formula=parsed.is_array_formula,
                estimated_calc_time=parsed.estimated_calc_time,
                has_errors=len(parsed.potential_errors) > 0,
                error_message='; '.join(parsed.potential_errors) if parsed.potential_errors else None
            )
            
            # Extract dependencies
            for coord in parsed.cell_dependencies:
                dep_address = self.a1_handler.to_a1(coord[0], coord[1])
                formula_info.direct_refs.add(dep_address)
            
            formula_info.range_refs = parsed.range_dependencies
            formula_info.named_refs = parsed.named_range_dependencies
            formula_info.external_refs = set(parsed.cross_sheet_references)
            
            # Store formula info
            self.formulas[address] = formula_info
            
            # Update dependency graphs
            self._update_dependency_graphs(address, formula_info)
            
            # Check for special formula types
            if parsed.is_volatile:
                self.volatile_cells.add(address)
            
            if parsed.is_array_formula:
                self._handle_array_formula(address, formula_info)
            
            return formula_info
            
        except Exception as e:
            logger.error(f"Error adding formula at {address}: {e}")
            # Create minimal formula info for error case
            return FormulaInfo(
                address=address,
                formula_text=formula,
                formula_complexity=FormulaComplexity.SIMPLE,
                has_errors=True,
                error_message=str(e)
            )
    
    def remove_formula(self, address: str):
        """Remove a formula and its dependencies"""
        
        if address in self.formulas:
            # Remove from graphs
            if self.dependency_graph.has_node(address):
                self.dependency_graph.remove_node(address)
            if self.dependent_graph.has_node(address):
                self.dependent_graph.remove_node(address)
            
            # Remove from special sets
            self.volatile_cells.discard(address)
            if address in self.array_formulas:
                del self.array_formulas[address]
            
            # Remove formula info
            del self.formulas[address]
    
    def _update_dependency_graphs(self, address: str, formula_info: FormulaInfo):
        """Update the dependency graphs with new formula"""
        
        # Add node if not exists
        if not self.dependency_graph.has_node(address):
            self.dependency_graph.add_node(address)
        if not self.dependent_graph.has_node(address):
            self.dependent_graph.add_node(address)
        
        # Add direct dependencies
        for dep_address in formula_info.direct_refs:
            # Dependency graph: address depends on dep_address
            self.dependency_graph.add_edge(address, dep_address)
            
            # Dependent graph: dep_address has address as dependent
            self.dependent_graph.add_edge(dep_address, address)
        
        # Handle range dependencies
        for range_ref in formula_info.range_refs:
            try:
                # Parse range and add all cells in range
                range_obj = self.a1_handler.parse_reference(range_ref)
                if isinstance(range_obj, RangeReference):
                    for cell in range_obj.get_all_cells():
                        self.dependency_graph.add_edge(address, cell.a1_notation)
                        self.dependent_graph.add_edge(cell.a1_notation, address)
            except Exception as e:
                logger.warning(f"Could not parse range {range_ref}: {e}")
    
    def _handle_array_formula(self, address: str, formula_info: FormulaInfo):
        """Handle array formula spill ranges"""
        
        # This is simplified - in reality would need to determine actual spill range
        # For now, we'll mark it as an array formula origin
        self.array_formulas[address] = [address]  # Placeholder for spill range
    
    def find_circular_references(self) -> List[List[str]]:
        """Find all circular reference chains"""
        
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            self.circular_refs = set(tuple(cycle) for cycle in cycles)
            return cycles
        except Exception as e:
            logger.error(f"Error finding circular references: {e}")
            return []
    
    def get_calculation_order(self) -> List[str]:
        """Get topological order for formula calculations"""
        
        try:
            # Use topological sort to get calculation order
            if nx.is_directed_acyclic_graph(self.dependency_graph):
                self.calculation_order = list(nx.topological_sort(self.dependency_graph))
            else:
                # Handle circular references by breaking cycles
                self.calculation_order = self._get_order_with_cycles()
            
            return self.calculation_order
            
        except Exception as e:
            logger.error(f"Error calculating order: {e}")
            return list(self.formulas.keys())
    
    def _get_order_with_cycles(self) -> List[str]:
        """Get calculation order when there are circular references"""
        
        # Find strongly connected components
        sccs = list(nx.strongly_connected_components(self.dependency_graph))
        
        # Create condensed graph
        condensed = nx.condensation(self.dependency_graph, sccs)
        
        # Get topological order of SCCs
        scc_order = list(nx.topological_sort(condensed))
        
        # Flatten back to individual cells
        order = []
        for scc_idx in scc_order:
            scc = sccs[scc_idx]
            order.extend(sorted(scc))  # Sort within SCC for deterministic order
        
        return order
    
    def get_dependents(self, address: str, recursive: bool = False) -> Set[str]:
        """Get all cells that depend on the given address"""
        
        if not self.dependent_graph.has_node(address):
            return set()
        
        if recursive:
            # Get all descendants (recursive dependents)
            return set(nx.descendants(self.dependent_graph, address))
        else:
            # Get direct dependents only
            return set(self.dependent_graph.successors(address))
    
    def get_dependencies(self, address: str, recursive: bool = False) -> Set[str]:
        """Get all cells that the given address depends on"""
        
        if not self.dependency_graph.has_node(address):
            return set()
        
        if recursive:
            # Get all descendants (recursive dependencies)
            return set(nx.descendants(self.dependency_graph, address))
        else:
            # Get direct dependencies only
            return set(self.dependency_graph.successors(address))
    
    def analyze_impact(self, address: str) -> Dict[str, Any]:
        """Analyze the impact of changing a cell"""
        
        impact = {
            'direct_dependents': len(self.get_dependents(address, recursive=False)),
            'total_dependents': len(self.get_dependents(address, recursive=True)),
            'dependency_chain_length': 0,
            'affects_volatile': False,
            'affects_array_formulas': False,
            'circular_references': [],
            'performance_impact': 'low'
        }
        
        # Calculate dependency chain length
        try:
            if self.dependent_graph.has_node(address):
                # Find longest path from this node
                distances = nx.single_source_shortest_path_length(self.dependent_graph, address)
                impact['dependency_chain_length'] = max(distances.values()) if distances else 0
        except:
            impact['dependency_chain_length'] = 0
        
        # Check if affects volatile or array formulas
        dependents = self.get_dependents(address, recursive=True)
        impact['affects_volatile'] = bool(dependents & self.volatile_cells)
        impact['affects_array_formulas'] = bool(dependents & set(self.array_formulas.keys()))
        
        # Check for circular references
        for cycle in self.circular_refs:
            if address in cycle:
                impact['circular_references'].append(list(cycle))
        
        # Estimate performance impact
        if impact['total_dependents'] > 100:
            impact['performance_impact'] = 'high'
        elif impact['total_dependents'] > 20:
            impact['performance_impact'] = 'medium'
        
        return impact
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about formulas and dependencies"""
        
        return {
            'total_formulas': len(self.formulas),
            'total_dependencies': sum(len(formula_info.direct_refs) for formula_info in self.formulas.values()),
            'circular_references': len(self.circular_refs),
            'volatile_formulas': len(self.volatile_cells),
            'array_formulas': len(self.array_formulas),
            'max_dependency_chain': self._calculate_max_chain_length()
        }
    
    def get_formula_complexity_summary(self) -> Dict[str, Any]:
        """Get summary of formula complexity across the sheet"""
        
        complexity_counts = {complexity.value: 0 for complexity in FormulaComplexity}
        total_complexity = 0.0
        error_count = 0
        
        for formula_info in self.formulas.values():
            complexity_counts[formula_info.formula_complexity.value] += 1
            total_complexity += formula_info.complexity_score
            if formula_info.has_errors:
                error_count += 1
        
        return {
            'total_formulas': len(self.formulas),
            'complexity_breakdown': complexity_counts,
            'average_complexity': total_complexity / len(self.formulas) if self.formulas else 0,
            'formulas_with_errors': error_count,
            'circular_references': len(self.circular_refs),
            'volatile_formulas': len(self.volatile_cells),
            'array_formulas': len(self.array_formulas)
        }
    
    def generate_dependency_report(self) -> Dict[str, Any]:
        """Generate comprehensive dependency analysis report"""
        
        # Update analysis
        circular_refs = self.find_circular_references()
        calc_order = self.get_calculation_order()
        
        # Calculate statistics
        self.analysis_stats.update({
            'total_formulas': len(self.formulas),
            'total_dependencies': sum(len(f.direct_refs) for f in self.formulas.values()),
            'circular_references': len(circular_refs),
            'volatile_formulas': len(self.volatile_cells),
            'array_formulas': len(self.array_formulas),
            'max_dependency_chain': self._calculate_max_chain_length()
        })
        
        return {
            'summary': self.analysis_stats,
            'circular_references': [list(cycle) for cycle in circular_refs],
            'calculation_order': calc_order,
            'volatile_cells': list(self.volatile_cells),
            'array_formulas': dict(self.array_formulas),
            'complexity_analysis': self.get_formula_complexity_summary(),
            'top_impact_cells': self._find_high_impact_cells(),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_max_chain_length(self) -> int:
        """Calculate the maximum dependency chain length"""
        
        max_length = 0
        
        try:
            for node in self.dependent_graph.nodes():
                if self.dependent_graph.has_node(node):
                    distances = nx.single_source_shortest_path_length(self.dependent_graph, node)
                    if distances:
                        max_length = max(max_length, max(distances.values()))
        except:
            pass
        
        return max_length
    
    def _find_high_impact_cells(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find cells with highest impact (most dependents)"""
        
        impact_cells = []
        
        for address in self.formulas.keys():
            impact = self.analyze_impact(address)
            impact_cells.append({
                'address': address,
                'total_dependents': impact['total_dependents'],
                'chain_length': impact['dependency_chain_length'],
                'performance_impact': impact['performance_impact']
            })
        
        # Sort by total dependents and return top N
        impact_cells.sort(key=lambda x: x['total_dependents'], reverse=True)
        return impact_cells[:limit]

class SpillTracker:
    """Tracks array formula spill ranges and conflicts"""
    
    def __init__(self):
        self.a1_handler = A1NotationHandler()
        self.spill_ranges: Dict[str, List[str]] = {}  # origin -> spilled cells
        self.spill_conflicts: Dict[str, List[str]] = {}  # origin -> conflicting cells
    
    def register_spill(self, origin_address: str, spill_range: List[str]):
        """Register a spill range for an array formula"""
        
        self.spill_ranges[origin_address] = spill_range
        
        # Check for conflicts
        conflicts = self._check_spill_conflicts(origin_address, spill_range)
        if conflicts:
            self.spill_conflicts[origin_address] = conflicts
    
    def _check_spill_conflicts(self, origin_address: str, spill_range: List[str]) -> List[str]:
        """Check for spill conflicts with existing data or other spills"""
        
        conflicts = []
        
        # Check against other spill ranges
        for other_origin, other_range in self.spill_ranges.items():
            if other_origin != origin_address:
                overlap = set(spill_range) & set(other_range)
                if overlap:
                    conflicts.extend(overlap)
        
        return conflicts
    
    def get_spill_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get spill information for a cell"""
        
        # Check if it's a spill origin
        if address in self.spill_ranges:
            return {
                'is_origin': True,
                'spill_range': self.spill_ranges[address],
                'has_conflicts': address in self.spill_conflicts,
                'conflicts': self.spill_conflicts.get(address, [])
            }
        
        # Check if it's part of a spill range
        for origin, spill_range in self.spill_ranges.items():
            if address in spill_range:
                return {
                    'is_origin': False,
                    'spill_origin': origin,
                    'is_spilled_cell': True
                }
        
        return None

# Utility functions for integration
def analyze_sheet_dependencies(formulas: Dict[str, str]) -> Dict[str, Any]:
    """Analyze dependencies for a collection of formulas"""
    
    tracker = DependencyTracker()
    
    # Add all formulas
    for address, formula in formulas.items():
        tracker.add_formula(address, formula)
    
    # Generate report
    return tracker.generate_dependency_report()

def find_circular_dependencies(formulas: Dict[str, str]) -> List[List[str]]:
    """Quick function to find circular dependencies"""
    
    tracker = DependencyTracker()
    
    for address, formula in formulas.items():
        tracker.add_formula(address, formula)
    
    return tracker.find_circular_references()

def get_calculation_order(formulas: Dict[str, str]) -> List[str]:
    """Get optimal calculation order for formulas"""
    
    tracker = DependencyTracker()
    
    for address, formula in formulas.items():
        tracker.add_formula(address, formula)
    
    return tracker.get_calculation_order()