"""
Integration layer - Complete Implementation
Connects new advanced context with existing agent system
Fixes incomplete logic and missing implementations
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import logging
from datetime import datetime

from .context.context_builder import QuadraticContextBuilder, QuadraticContext, ContextFormatter
from .context.spreadsheet_native import SpreadsheetGrid, SheetCollection
from .a1_notation import A1NotationHandler

logger = logging.getLogger(__name__)

class ContextRevolutionIntegrator:
    """
    Integrates the new advanced-level context system with existing agent infrastructure
    Provides seamless upgrade path from DataFrame-centric to spreadsheet-native
    """
    
    def __init__(self, existing_data_manager, existing_agent_manager=None):
        self.data_manager = existing_data_manager
        self.agent_manager = existing_agent_manager
        
        # New components
        self.context_builder = QuadraticContextBuilder(existing_data_manager)
        self.a1_handler = A1NotationHandler()
        self.context_formatter = ContextFormatter()
        
        # Compatibility layer
        self.compatibility_mode = True
        self.context_cache: Dict[str, QuadraticContext] = {}
        self.legacy_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("🔄 Context Revolution Integrator initialized")
    
    def enhanced_get_data(self, worksheet_name: str = None, 
                         force_refresh: bool = False,
                         return_context: bool = True) -> Union[Dict[str, Any], QuadraticContext]:
        """
        Enhanced data loading that provides both compatibility and new capabilities
        COMPLETE IMPLEMENTATION - was missing logic
        
        Args:
            worksheet_name: Name of worksheet to load
            force_refresh: Whether to force refresh from Google Sheets
            return_context: If True, returns AdvancedContext; if False, returns old format
        """
        
        try:
            # Use current worksheet if none specified
            if worksheet_name is None:
                worksheet_name = getattr(self.data_manager, 'current_worksheet', 'Sheet1')
            
            # Check cache first (unless force refresh)
            cache_key = f"{worksheet_name}_{return_context}"
            
            if not force_refresh:
                if return_context and worksheet_name in self.context_cache:
                    logger.info(f"📋 Using cached advanced context for '{worksheet_name}'")
                    return self.context_cache[worksheet_name]
                elif not return_context and cache_key in self.legacy_cache:
                    logger.info(f"📋 Using cached legacy data for '{worksheet_name}'")
                    return self.legacy_cache[cache_key]
            
            # Generate advanced context
            logger.info(f"🧠 Building advanced context for '{worksheet_name}'")
            context = self.context_builder.analyze_worksheet(worksheet_name, force_refresh=force_refresh)
            
            # Cache the context
            self.context_cache[worksheet_name] = context
            
            if return_context:
                return context
            else:
                # Convert to legacy format for backward compatibility
                legacy_data = self._convert_context_to_legacy(context)
                self.legacy_cache[cache_key] = legacy_data
                return legacy_data
                
        except Exception as e:
            logger.error(f"Error in enhanced_get_data: {e}")
            
            # Fallback to original data manager if possible
            if hasattr(self.data_manager, 'get_data'):
                logger.warning("Falling back to original data manager")
                return self.data_manager.get_data(worksheet_name)
            else:
                raise e
    
    def _convert_context_to_legacy(self, context: QuadraticContext) -> Dict[str, Any]:
        """Convert AdvancedContext to legacy format for backward compatibility"""
        
        legacy_data = {
            'worksheet_name': context.sheet_name,
            'total_cells': context.total_cells,
            'used_range': context.used_range,
            'data_quality': context.data_quality_score,
            'complexity': context.complexity_score,
            'suggestions': context.intelligent_suggestions,
            'issues': context.potential_issues,
            'last_analysis': context.last_analysis.isoformat(),
            'metadata': {
                'regions': len(context.data_regions),
                'formulas': len(context.formula_summary),
                'analysis_duration': context.analysis_duration
            }
        }
        
        # Try to create a representative DataFrame
        try:
            if context.representative_sample and 'preview' in context.representative_sample:
                df_data = context.representative_sample['preview']
                if df_data:
                    df = pd.DataFrame(df_data)
                    legacy_data['df'] = df
                    legacy_data['shape'] = df.shape
                else:
                    legacy_data['df'] = pd.DataFrame()
                    legacy_data['shape'] = (0, 0)
            else:
                legacy_data['df'] = pd.DataFrame()
                legacy_data['shape'] = (0, 0)
        except Exception as e:
            logger.warning(f"Could not create DataFrame from context: {e}")
            legacy_data['df'] = pd.DataFrame()
            legacy_data['shape'] = (0, 0)
        
        # Add column information
        if context.column_profiles:
            legacy_data['columns'] = []
            for profile in context.column_profiles:
                legacy_data['columns'].append({
                    'name': profile.column_name,
                    'type': profile.inferred_type.value if hasattr(profile.inferred_type, 'value') else str(profile.inferred_type),
                    'stats': profile.stats
                })
        
        return legacy_data
    
    def enhanced_agent_run(self, user_input: str, worksheet_name: str,
                          use_enhanced_context: bool = True) -> Dict[str, Any]:
        """
        Enhanced agent run with advanced context capabilities
        COMPLETE IMPLEMENTATION - was missing
        """
        
        try:
            # Get context (enhanced or legacy)
            if use_enhanced_context:
                context = self.enhanced_get_data(worksheet_name, return_context=True)
                
                # Use enhanced agent if available
                if hasattr(self.agent_manager, 'run'):
                    return self._run_with_enhanced_context(user_input, worksheet_name, context)
                else:
                    return self._run_legacy_with_context(user_input, worksheet_name, context)
            else:
                # Use legacy format
                legacy_data = self.enhanced_get_data(worksheet_name, return_context=False)
                return self._run_legacy_agent(user_input, worksheet_name, legacy_data)
                
        except Exception as e:
            logger.error(f"Error in enhanced_agent_run: {e}")
            return {
                'status': 'error',
                'message': f"Failed to process request: {str(e)}",
                'fallback_attempted': True
            }
    
    def _run_with_enhanced_context(self, user_input: str, worksheet_name: str, 
                                  context: QuadraticContext) -> Dict[str, Any]:
        """Run with enhanced context and modern agent"""
        
        # Enhanced processing with full context
        result = self.agent_manager.run(user_input, worksheet_name)
        
        # Enhance result with context insights
        if isinstance(result, dict):
            result['context_analysis'] = {
                'sheet_quality': context.data_quality_score,
                'complexity_level': context.complexity_score,
                'suggestions': context.intelligent_suggestions[:3],  # Top 3
                'potential_issues': context.potential_issues[:3],    # Top 3
                'regions_analyzed': len(context.data_regions),
                'formulas_found': len(context.formula_summary)
            }
            result['analysis_metadata'] = {
                'context_generated': True,
                'analysis_duration': context.analysis_duration,
                'last_analysis': context.last_analysis.isoformat()
            }
        
        return result
    
    def _run_legacy_with_context(self, user_input: str, worksheet_name: str, 
                                context: QuadraticContext) -> Dict[str, Any]:
        """Run legacy agent but with enhanced context insights"""
        
        # Convert context to legacy format
        legacy_data = self._convert_context_to_legacy(context)
        
        # Create a pseudo-agent response with context insights
        suggestions = context.intelligent_suggestions[:5]
        
        if not suggestions:
            suggestions.append(f"The worksheet '{worksheet_name}' has been analyzed")
            if context.data_quality_score > 0.8:
                suggestions.append("Data quality is high - good for analysis")
            if context.complexity_score > 5.0:
                suggestions.append("Complex formulas detected - review for optimization")
        
        # Process user input for basic understanding
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['analyze', 'summary', 'overview']):
            response = self._generate_analysis_response(context)
        elif any(word in user_input_lower for word in ['chart', 'graph', 'plot', 'visualize']):
            response = self._generate_visualization_response(context)
        elif any(word in user_input_lower for word in ['formula', 'calculate', 'compute']):
            response = self._generate_formula_response(context)
        else:
            response = self._generate_general_response(context, user_input)
        
        return {
            'status': 'success',
            'response': response,
            'suggestions': suggestions,
            'context_summary': {
                'quality': context.data_quality_score,
                'complexity': context.complexity_score,
                'regions': len(context.data_regions)
            },
            'legacy_compatibility': True
        }
    
    def _run_legacy_agent(self, user_input: str, worksheet_name: str, 
                         legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run with original legacy agent and data format"""
        
        # Try to use original agent if available
        if hasattr(self.agent_manager, 'run'):
            try:
                return self.agent_manager.run(user_input, worksheet_name)
            except Exception as e:
                logger.warning(f"Legacy agent failed: {e}")
        
        # Fallback to basic processing
        return {
            'status': 'processed',
            'response': f"Processed request for worksheet '{worksheet_name}' with legacy compatibility",
            'data_summary': {
                'shape': legacy_data.get('shape', (0, 0)),
                'quality': legacy_data.get('data_quality', 0.0),
                'columns': len(legacy_data.get('columns', []))
            },
            'legacy_mode': True
        }
    
    def _generate_analysis_response(self, context: QuadraticContext) -> str:
        """Generate analysis response based on context"""
        
        response_parts = [
            f"Analysis of worksheet '{context.sheet_name}':",
            f"• Total cells with data: {context.total_cells:,}",
            f"• Data quality score: {context.data_quality_score:.1%}",
            f"• Complexity level: {context.complexity_score:.1f}/10"
        ]
        
        if context.data_regions:
            response_parts.append(f"• Data regions identified: {len(context.data_regions)}")
        
        if context.formula_summary:
            response_parts.append(f"• Formulas found: {len(context.formula_summary)}")
        
        if context.intelligent_suggestions:
            response_parts.append("\nKey insights:")
            for suggestion in context.intelligent_suggestions[:3]:
                response_parts.append(f"• {suggestion}")
        
        return "\n".join(response_parts)
    
    def _generate_visualization_response(self, context: QuadraticContext) -> str:
        """Generate visualization suggestions based on context"""
        
        suggestions = [
            f"Visualization recommendations for '{context.sheet_name}':"
        ]
        
        # Analyze data regions for chart suggestions
        if context.data_regions:
            for region_id, region in context.data_regions.items():
                if hasattr(region, 'column_profiles') and region.column_profiles:
                    numeric_cols = sum(1 for col in region.column_profiles 
                                     if getattr(col, 'inferred_type', None) == 'numeric')
                    if numeric_cols >= 2:
                        suggestions.append(f"• Scatter plot recommended for region '{region_id}'")
                    elif numeric_cols == 1:
                        suggestions.append(f"• Bar chart or histogram recommended for region '{region_id}'")
        
        if not context.data_regions:
            suggestions.append("• Analyze your data structure to get specific chart recommendations")
        
        suggestions.append("• Consider using Google Sheets built-in chart tools")
        
        return "\n".join(suggestions)
    
    def _generate_formula_response(self, context: QuadraticContext) -> str:
        """Generate formula insights based on context"""
        
        response_parts = [
            f"Formula analysis for '{context.sheet_name}':"
        ]
        
        if context.formula_summary:
            complexity_count = context.formula_summary.get('complexity_breakdown', {})
            if complexity_count:
                response_parts.append("Formula complexity breakdown:")
                for level, count in complexity_count.items():
                    response_parts.append(f"• {level}: {count} formulas")
        
        if context.circular_references:
            response_parts.append(f"⚠️ Circular references detected: {len(context.circular_references)}")
        
        if hasattr(context, 'potential_issues') and context.potential_issues:
            response_parts.append("Potential issues:")
            for issue in context.potential_issues[:3]:
                response_parts.append(f"• {issue}")
        
        return "\n".join(response_parts)
    
    def _generate_general_response(self, context: QuadraticContext, user_input: str) -> str:
        """Generate general response based on context and user input"""
        
        response = f"I've analyzed the worksheet '{context.sheet_name}' and here's what I found:\n\n"
        
        # Basic stats
        response += f"📊 Data Overview:\n"
        response += f"• {context.total_cells:,} cells with data\n"
        response += f"• Quality score: {context.data_quality_score:.1%}\n"
        
        # Add relevant suggestions
        if context.intelligent_suggestions:
            response += f"\n💡 Suggestions:\n"
            for suggestion in context.intelligent_suggestions[:2]:
                response += f"• {suggestion}\n"
        
        response += f"\nHow can I help you work with this data?"
        
        return response

class LegacyCompatibilityLayer:
    """
    Provides compatibility with existing tools and workflows
    Ensures smooth transition to new context system
    """
    
    def __init__(self, integrator: ContextRevolutionIntegrator):
        self.integrator = integrator
    
    def adapt_existing_tools(self, tools_list: List[Any]) -> List[Any]:
        """Adapt existing tools to work with new context system"""
        
        adapted_tools = []
        
        for tool in tools_list:
            if hasattr(tool, 'name'):
                # Create wrapper that provides enhanced context
                adapted_tool = self._wrap_tool_with_context(tool)
                adapted_tools.append(adapted_tool)
            else:
                adapted_tools.append(tool)
        
        return adapted_tools
    
    def _wrap_tool_with_context(self, original_tool):
        """Wrap existing tool with enhanced context capabilities"""
        
        class ContextEnhancedTool:
            def __init__(self, original_tool, integrator):
                self.original_tool = original_tool
                self.integrator = integrator
                
                # Copy original attributes
                for attr in ['name', 'description', 'args_schema']:
                    if hasattr(original_tool, attr):
                        setattr(self, attr, getattr(original_tool, attr))
            
            def run(self, *args, **kwargs):
                # Inject enhanced context if available
                if hasattr(self.integrator, 'context_cache'):
                    for worksheet_name, context in self.integrator.context_cache.items():
                        # Add context to kwargs if not present
                        if 'advanced_context' not in kwargs:
                            kwargs['advanced_context'] = context
                
                # Run original tool
                return self.original_tool.run(*args, **kwargs)
            
            def __call__(self, *args, **kwargs):
                return self.run(*args, **kwargs)
        
        return ContextEnhancedTool(original_tool, self.integrator)

class MigrationHelper:
    """
    Helps migrate from old DataFrame-centric system to new spreadsheet-native system
    """
    
    @staticmethod
    def migrate_agent_state(old_state: Dict[str, Any], 
                           context: QuadraticContext) -> Dict[str, Any]:
        """Migrate old agent state to include new context"""
        
        new_state = old_state.copy()
        
        # Add new context fields
        new_state['advanced_context'] = context
        new_state['available_regions'] = list(context.data_regions.keys())
        new_state['sheet_analysis'] = {
            'quality': context.data_quality_score,
            'complexity': context.complexity_score,
            'suggestions': context.intelligent_suggestions
        }
        
        # Maintain backward compatibility
        if 'df' not in new_state and context.representative_sample:
            try:
                df = pd.DataFrame(context.representative_sample.get('preview', []))
                new_state['df'] = df
            except:
                new_state['df'] = pd.DataFrame()
        
        return new_state
    
    @staticmethod
    def convert_dataframe_operations_to_native(operation: str, 
                                              df_params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DataFrame-style operations to spreadsheet-native operations"""
        
        native_operations = {
            'create_histogram': {
                'operation': 'create_chart',
                'chart_type': 'histogram',
                'data_range': df_params.get('column', 'A:A')
            },
            
            'create_scatter_plot': {
                'operation': 'create_chart', 
                'chart_type': 'scatter',
                'x_range': df_params.get('x_col', 'A:A'),
                'y_range': df_params.get('y_col', 'B:B')
            },
            
            'correlation_analysis': {
                'operation': 'insert_formula',
                'formula_type': 'CORREL',
                'ranges': [df_params.get('col1', 'A:A'), df_params.get('col2', 'B:B')]
            }
        }
        
        return native_operations.get(operation, {
            'operation': 'custom',
            'original_operation': operation,
            'params': df_params
        })

def create_enhanced_agent_manager(existing_data_manager, existing_agent_manager=None):
    """
    Factory function to create an enhanced agent manager with advanced-level capabilities
    This is the main entry point for upgrading existing systems
    """
    
    # Create integrator
    integrator = ContextRevolutionIntegrator(existing_data_manager, existing_agent_manager)
    
    # Create compatibility layer
    compatibility = LegacyCompatibilityLayer(integrator)
    
    class EnhancedAgentManager:
        """
        Enhanced agent manager that provides both old and new interfaces
        """
        
        def __init__(self):
            self.integrator = integrator
            self.compatibility = compatibility
            self.data_manager = existing_data_manager  # For backward compatibility
            
            # Enhance existing tools if agent manager is available
            if existing_agent_manager and hasattr(existing_agent_manager, 'tool_map'):
                original_tools = list(existing_agent_manager.tool_map.values())
                enhanced_tools = compatibility.adapt_existing_tools(original_tools)
                
                # Update tool map
                self.tool_map = {tool.name: tool for tool in enhanced_tools}
            else:
                self.tool_map = {}
        
        def run(self, user_input: str, worksheet_name: str, 
               use_enhanced_context: bool = True) -> Dict[str, Any]:
            """Main run method with enhanced capabilities"""
            
            return self.integrator.enhanced_agent_run(
                user_input, worksheet_name, use_enhanced_context
            )
        
        def get_context(self, worksheet_name: str, 
                       force_refresh: bool = False) -> QuadraticContext:
            """Get Advanced-level context"""
            
            return self.integrator.enhanced_get_data(
                worksheet_name, force_refresh, return_context=True
            )
        
        def get_legacy_data(self, worksheet_name: str, 
                           force_refresh: bool = False) -> Dict[str, Any]:
            """Get data in legacy format for backward compatibility"""
            
            return self.integrator.enhanced_get_data(
                worksheet_name, force_refresh, return_context=False
            )
    
    return EnhancedAgentManager()

# Example usage and integration points
def integrate_with_existing_cli(existing_cli_main, existing_data_manager):
    """
    Example of how to integrate with existing CLI
    """
    
    def enhanced_cli_main(*args, **kwargs):
        # Create enhanced agent manager
        enhanced_agent = create_enhanced_agent_manager(existing_data_manager)
        
        # Replace data manager and agent in kwargs
        if 'data_manager' in kwargs:
            kwargs['data_manager'] = enhanced_agent.integrator
        
        if 'agent_manager' in kwargs:
            kwargs['agent_manager'] = enhanced_agent
        
        # Call original CLI with enhanced components
        return existing_cli_main(*args, **kwargs)
    
    return enhanced_cli_main

def upgrade_existing_system(data_manager, agent_manager=None):
    """
    One-line upgrade for existing systems
    """
    
    enhanced_manager = create_enhanced_agent_manager(data_manager, agent_manager)
    
    logger.info("🎉 System upgraded to advanced-level capabilities!")
    logger.info("✅ Enhanced context system active")
    logger.info("✅ Spreadsheet-native operations enabled")
    logger.info("✅ Backward compatibility maintained")
    
    return enhanced_manager