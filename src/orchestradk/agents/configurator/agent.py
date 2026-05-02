"""
Configurator Agent - Agent B of OrchestrADK.

This agent takes scaffolder output and generates ADK-compliant
configuration files (YAML and JSON) using a multi-step LangGraph workflow.
"""

from typing import Dict, Any, Optional, TypedDict
import logging
from datetime import datetime

from langgraph.graph import StateGraph, END

from ..base_agent import BaseAgent, AgentMessage, AgentResponse
from .yaml_generator import YAMLGenerator
from .json_generator import JSONGenerator
from .schema_validator import SchemaValidator
from ...utils.exceptions import (
    OrchestradkError,
    GenerationError,
    ValidationError
)

logger = logging.getLogger(__name__)


# Define the state for the configurator agent's internal workflow
class ConfiguratorState(TypedDict):
    """State for the configurator agent's LangGraph workflow."""
    
    # Input
    scaffolder_output: Dict[str, Any]
    additional_config: Optional[Dict[str, Any]]
    
    # Intermediate results
    yaml_files: Optional[Dict[str, str]]
    json_files: Optional[Dict[str, str]]
    validation_results: Optional[Dict[str, Any]]
    
    # Output
    final_output: Optional[Dict[str, Any]]
    error: Optional[str]
    
    # Metadata
    step: str
    timestamp: str


class ConfiguratorAgent(BaseAgent):
    """
    The Configurator Agent (Agent B).
    
    Responsibilities:
    - Generate ADK-compliant YAML configurations (agent.yaml, skills.yaml)
    - Create JSON schema definitions (config.json, schema.json)
    - Map LangGraph components to ADK metadata
    - Validate against ADK specifications
    
    Uses LangGraph internally to orchestrate its own workflow.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the configurator agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(agent_id="configurator", config=config)
        
        self.yaml_generator = YAMLGenerator()
        self.json_generator = JSONGenerator()
        self.schema_validator = SchemaValidator()
        self.graph: Optional[StateGraph] = None
        
        logger.info("ConfiguratorAgent initialized")
    
    async def initialize(self) -> None:
        """Initialize the agent and build the LangGraph workflow."""
        if self._initialized:
            logger.warning("Agent already initialized")
            return
        
        logger.info("Building configurator workflow graph...")
        
        # Load validation schemas
        try:
            self.schema_validator.load_schemas()
        except Exception as e:
            logger.warning(f"Failed to load schemas, will use defaults: {str(e)}")
        
        # Create the workflow graph
        workflow = StateGraph(ConfiguratorState)
        
        # Add nodes for each step
        workflow.add_node("generate_yaml", self._generate_yaml_node)
        workflow.add_node("generate_json", self._generate_json_node)
        workflow.add_node("validate_configs", self._validate_configs_node)
        workflow.add_node("finalize_output", self._finalize_output_node)
        
        # Define the workflow edges
        workflow.set_entry_point("generate_yaml")
        workflow.add_edge("generate_yaml", "generate_json")
        workflow.add_edge("generate_json", "validate_configs")
        workflow.add_edge("validate_configs", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        
        self._initialized = True
        logger.info("Configurator workflow graph built successfully")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up configurator agent")
        self.graph = None
        self._initialized = False
    
    async def process(self, message: AgentMessage) -> AgentResponse:
        """
        Process an incoming message to generate configuration files.
        
        Args:
            message: Incoming message with scaffolder output
            
        Returns:
            AgentResponse with generated configs or error
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate input
        if not await self.validate_input(message):
            return self.create_response(
                success=False,
                error="Invalid message format"
            )
        
        # Extract scaffolder output from payload
        scaffolder_output = message.payload.get("scaffolder_output")
        if not scaffolder_output:
            return self.create_response(
                success=False,
                error="No scaffolder_output found in message payload"
            )
        
        # Extract additional configuration
        additional_config = message.payload.get("additional_config", {})
        
        logger.info(f"Processing configurator request for agent: {scaffolder_output.get('agent_name', 'unknown')}")
        start_time = datetime.utcnow()
        
        try:
            # Create initial state
            initial_state: ConfiguratorState = {
                "scaffolder_output": scaffolder_output,
                "additional_config": additional_config,
                "yaml_files": None,
                "json_files": None,
                "validation_results": None,
                "final_output": None,
                "error": None,
                "step": "initialized",
                "timestamp": start_time.isoformat()
            }
            
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Check for errors
            if final_state.get("error"):
                return self.create_response(
                    success=False,
                    error=final_state["error"],
                    metadata={"step": final_state.get("step")}
                )
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Return successful response
            return self.create_response(
                success=True,
                data=final_state["final_output"],
                metadata={
                    "execution_time": execution_time,
                    "steps_completed": final_state.get("step"),
                    "timestamp": end_time.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Configurator processing failed: {str(e)}", exc_info=True)
            return self.create_response(
                success=False,
                error=f"Processing failed: {str(e)}",
                metadata={"error_type": type(e).__name__}
            )
    
    # Node implementations for the internal workflow
    
    async def _generate_yaml_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """
        Node: Generate YAML configuration files.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with YAML files
        """
        logger.info("Executing generate_yaml node")
        
        try:
            scaffolder_output = state["scaffolder_output"]
            additional_config = state.get("additional_config", {})
            
            # Generate YAML files
            yaml_files = self.yaml_generator.generate_all(
                scaffolder_output,
                additional_config
            )
            
            logger.info(f"Generated {len(yaml_files)} YAML files")
            
            return {
                **state,
                "yaml_files": yaml_files,
                "step": "yaml_generated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except GenerationError as e:
            logger.error(f"YAML generation error: {str(e)}")
            return {
                **state,
                "error": f"Failed to generate YAML files: {str(e)}",
                "step": "yaml_generation_failed"
            }
        except Exception as e:
            logger.error(f"Unexpected error in generate_yaml node: {str(e)}")
            return {
                **state,
                "error": f"Unexpected YAML generation error: {str(e)}",
                "step": "yaml_generation_failed"
            }
    
    async def _generate_json_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """
        Node: Generate JSON configuration files.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with JSON files
        """
        logger.info("Executing generate_json node")
        
        # Check if YAML generation succeeded
        if state.get("error") or not state.get("yaml_files"):
            return state
        
        try:
            scaffolder_output = state["scaffolder_output"]
            additional_config = state.get("additional_config", {})
            
            # Generate JSON files
            json_files = self.json_generator.generate_all(
                scaffolder_output,
                additional_config
            )
            
            logger.info(f"Generated {len(json_files)} JSON files")
            
            return {
                **state,
                "json_files": json_files,
                "step": "json_generated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except GenerationError as e:
            logger.error(f"JSON generation error: {str(e)}")
            return {
                **state,
                "error": f"Failed to generate JSON files: {str(e)}",
                "step": "json_generation_failed"
            }
        except Exception as e:
            logger.error(f"Unexpected error in generate_json node: {str(e)}")
            return {
                **state,
                "error": f"Unexpected JSON generation error: {str(e)}",
                "step": "json_generation_failed"
            }
    
    async def _validate_configs_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """
        Node: Validate all generated configuration files.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with validation results
        """
        logger.info("Executing validate_configs node")
        
        # Check if generation succeeded
        if state.get("error") or not state.get("yaml_files") or not state.get("json_files"):
            return state
        
        try:
            # Combine all generated files
            all_files = {**state["yaml_files"], **state["json_files"]}
            
            # Validate all files
            all_valid, errors = self.schema_validator.validate_all(all_files)
            
            validation_results = {
                "all_valid": all_valid,
                "errors": errors,
                "files_validated": list(all_files.keys())
            }
            
            if not all_valid:
                # Format error message
                error_summary = []
                for filename, file_errors in errors.items():
                    error_summary.append(f"{filename}: {len(file_errors)} errors")
                
                logger.warning(f"Validation failed: {', '.join(error_summary)}")
                
                return {
                    **state,
                    "validation_results": validation_results,
                    "error": f"Configuration validation failed: {', '.join(error_summary)}",
                    "step": "validation_failed"
                }
            
            logger.info("All configuration files validated successfully")
            
            return {
                **state,
                "validation_results": validation_results,
                "step": "validated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                **state,
                "error": f"Failed to validate configurations: {str(e)}",
                "step": "validation_failed"
            }
        except Exception as e:
            logger.error(f"Unexpected error in validate_configs node: {str(e)}")
            return {
                **state,
                "error": f"Unexpected validation error: {str(e)}",
                "step": "validation_failed"
            }
    
    async def _finalize_output_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """
        Node: Finalize the output package.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final output
        """
        logger.info("Executing finalize_output node")
        
        # Check if validation succeeded
        if state.get("error"):
            return state
        
        try:
            scaffolder_output = state["scaffolder_output"]
            yaml_files = state["yaml_files"]
            json_files = state["json_files"]
            validation_results = state["validation_results"]
            
            # Combine all files
            all_files = {**yaml_files, **json_files}
            
            # Create final output package
            final_output = {
                "agent_name": scaffolder_output.get("agent_name", "unnamed_agent"),
                "description": scaffolder_output.get("description", "Generated agent"),
                "files": all_files,
                "metadata": {
                    "num_yaml_files": len(yaml_files),
                    "num_json_files": len(json_files),
                    "total_files": len(all_files),
                    "validation_passed": validation_results.get("all_valid", False),
                    "files_generated": list(all_files.keys())
                },
                "validation": validation_results,
                "package_structure": self._generate_package_structure(
                    scaffolder_output,
                    all_files
                )
            }
            
            logger.info("Configuration package finalized successfully")
            
            return {
                **state,
                "final_output": final_output,
                "step": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error finalizing output: {str(e)}")
            return {
                **state,
                "error": f"Failed to finalize output: {str(e)}",
                "step": "finalization_failed"
            }
    
    def _generate_package_structure(
        self,
        scaffolder_output: Dict[str, Any],
        config_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate the complete package structure.
        
        Args:
            scaffolder_output: Output from scaffolder
            config_files: Generated configuration files
            
        Returns:
            Package structure dictionary
        """
        agent_name = scaffolder_output.get("agent_name", "unnamed_agent")
        
        # Get Python files from scaffolder
        python_files = scaffolder_output.get("files", {})
        
        structure = {
            "root": agent_name,
            "directories": {
                "src": {
                    "files": list(python_files.keys()),
                    "description": "Python LangGraph implementation"
                },
                "config": {
                    "files": list(config_files.keys()),
                    "description": "ADK configuration files"
                }
            },
            "files": {
                "README.md": "Agent documentation",
                "requirements.txt": "Python dependencies"
            },
            "deployment": {
                "ready": True,
                "platform": "watsonx Orchestrate",
                "adk_version": "1.0.0"
            }
        }
        
        return structure
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get the current status of the workflow.
        
        Returns:
            Dictionary with workflow status information
        """
        return {
            "agent_id": self.agent_id,
            "initialized": self._initialized,
            "graph_compiled": self.graph is not None,
            "nodes": [
                "generate_yaml",
                "generate_json",
                "validate_configs",
                "finalize_output"
            ],
            "generators": {
                "yaml": self.yaml_generator is not None,
                "json": self.json_generator is not None
            },
            "validator": self.schema_validator is not None
        }


# Made with Bob