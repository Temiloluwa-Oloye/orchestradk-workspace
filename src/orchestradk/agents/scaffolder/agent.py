"""
Scaffolder Agent - Agent A of OrchestrADK.

This agent takes natural language developer requests and generates
Python LangGraph boilerplate code using a multi-step LangGraph workflow.
"""

from typing import Dict, Any, Optional, TypedDict, Annotated
import logging
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from ..base_agent import BaseAgent, AgentMessage, AgentResponse
from .parser import RequestParser, ParsedRequest
from .generator import CodeGenerator
from ...llm.client import LLMClient
from ...utils.exceptions import (
    OrchestrADKError,
    ParseError,
    GenerationError,
    ValidationError
)

logger = logging.getLogger(__name__)


# Define the state for the scaffolder agent's internal workflow
class ScaffolderState(TypedDict):
    """State for the scaffolder agent's LangGraph workflow."""
    
    # Input
    request: str
    
    # Intermediate results
    parsed_request: Optional[ParsedRequest]
    generated_code: Optional[Dict[str, str]]
    validation_results: Optional[Dict[str, bool]]
    
    # Output
    final_output: Optional[Dict[str, Any]]
    error: Optional[str]
    
    # Metadata
    step: str
    timestamp: str


class ScaffolderAgent(BaseAgent):
    """
    The Scaffolder Agent (Agent A).
    
    Responsibilities:
    - Parse natural language developer requests
    - Identify required LangGraph components (nodes, edges, state)
    - Generate Python LangGraph boilerplate code
    - Validate generated code syntax
    
    Uses LangGraph internally to orchestrate its own workflow.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the scaffolder agent.
        
        Args:
            llm_client: LLM client for parsing and generation
            config: Optional configuration dictionary
        """
        super().__init__(agent_id="scaffolder", config=config)
        
        self.llm_client = llm_client
        self.parser = RequestParser(llm_client)
        self.generator = CodeGenerator()
        self.graph: Optional[StateGraph] = None
        
        logger.info("ScaffolderAgent initialized")
    
    async def initialize(self) -> None:
        """Initialize the agent and build the LangGraph workflow."""
        if self._initialized:
            logger.warning("Agent already initialized")
            return
        
        logger.info("Building scaffolder workflow graph...")
        
        # Create the workflow graph
        workflow = StateGraph(ScaffolderState)
        
        # Add nodes for each step
        workflow.add_node("parse_request", self._parse_request_node)
        workflow.add_node("generate_code", self._generate_code_node)
        workflow.add_node("validate_code", self._validate_code_node)
        workflow.add_node("finalize_output", self._finalize_output_node)
        
        # Define the workflow edges
        workflow.set_entry_point("parse_request")
        workflow.add_edge("parse_request", "generate_code")
        workflow.add_edge("generate_code", "validate_code")
        workflow.add_edge("validate_code", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        
        self._initialized = True
        logger.info("Scaffolder workflow graph built successfully")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up scaffolder agent")
        self.graph = None
        self._initialized = False
    
    async def process(self, message: AgentMessage) -> AgentResponse:
        """
        Process an incoming message to generate LangGraph code.
        
        Args:
            message: Incoming message with developer request
            
        Returns:
            AgentResponse with generated code or error
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate input
        if not await self.validate_input(message):
            return self.create_response(
                success=False,
                error="Invalid message format"
            )
        
        # Extract request from payload
        request = message.payload.get("request")
        if not request:
            return self.create_response(
                success=False,
                error="No request found in message payload"
            )
        
        logger.info(f"Processing scaffolder request: {request[:100]}...")
        start_time = datetime.utcnow()
        
        try:
            # Create initial state
            initial_state: ScaffolderState = {
                "request": request,
                "parsed_request": None,
                "generated_code": None,
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
            logger.error(f"Scaffolder processing failed: {str(e)}", exc_info=True)
            return self.create_response(
                success=False,
                error=f"Processing failed: {str(e)}",
                metadata={"error_type": type(e).__name__}
            )
    
    # Node implementations for the internal workflow
    
    async def _parse_request_node(self, state: ScaffolderState) -> ScaffolderState:
        """
        Node: Parse the natural language request.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with parsed request
        """
        logger.info("Executing parse_request node")
        
        try:
            parsed = await self.parser.parse(state["request"])
            
            return {
                **state,
                "parsed_request": parsed,
                "step": "parsed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ParseError as e:
            logger.error(f"Parse error: {str(e)}")
            return {
                **state,
                "error": f"Failed to parse request: {str(e)}",
                "step": "parse_failed"
            }
        except Exception as e:
            logger.error(f"Unexpected error in parse node: {str(e)}")
            return {
                **state,
                "error": f"Unexpected parse error: {str(e)}",
                "step": "parse_failed"
            }
    
    async def _generate_code_node(self, state: ScaffolderState) -> ScaffolderState:
        """
        Node: Generate Python LangGraph code.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with generated code
        """
        logger.info("Executing generate_code node")
        
        # Check if parsing succeeded
        if state.get("error") or not state.get("parsed_request"):
            return state
        
        try:
            parsed = state["parsed_request"]
            generated = self.generator.generate_all(parsed)
            
            return {
                **state,
                "generated_code": generated,
                "step": "generated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except GenerationError as e:
            logger.error(f"Generation error: {str(e)}")
            return {
                **state,
                "error": f"Failed to generate code: {str(e)}",
                "step": "generation_failed"
            }
        except Exception as e:
            logger.error(f"Unexpected error in generate node: {str(e)}")
            return {
                **state,
                "error": f"Unexpected generation error: {str(e)}",
                "step": "generation_failed"
            }
    
    async def _validate_code_node(self, state: ScaffolderState) -> ScaffolderState:
        """
        Node: Validate generated code syntax.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with validation results
        """
        logger.info("Executing validate_code node")
        
        # Check if generation succeeded
        if state.get("error") or not state.get("generated_code"):
            return state
        
        try:
            generated = state["generated_code"]
            validation_results = {}
            
            # Validate each generated file
            for filename, code in generated.items():
                if filename.endswith(".py"):
                    is_valid = self.generator.validate_generated_code(code)
                    validation_results[filename] = is_valid
                    
                    if not is_valid:
                        logger.warning(f"Validation failed for {filename}")
            
            # Check if all validations passed
            all_valid = all(validation_results.values())
            
            if not all_valid:
                failed_files = [f for f, v in validation_results.items() if not v]
                return {
                    **state,
                    "error": f"Code validation failed for: {', '.join(failed_files)}",
                    "validation_results": validation_results,
                    "step": "validation_failed"
                }
            
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
                "error": f"Failed to validate code: {str(e)}",
                "step": "validation_failed"
            }
        except Exception as e:
            logger.error(f"Unexpected error in validate node: {str(e)}")
            return {
                **state,
                "error": f"Unexpected validation error: {str(e)}",
                "step": "validation_failed"
            }
    
    async def _finalize_output_node(self, state: ScaffolderState) -> ScaffolderState:
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
            parsed = state["parsed_request"]
            generated = state["generated_code"]
            validation = state["validation_results"]
            
            # Create final output package
            final_output = {
                "agent_name": parsed.agent_name,
                "description": parsed.description,
                "files": generated,
                "metadata": {
                    "num_nodes": len(parsed.nodes),
                    "num_state_fields": len(parsed.state_fields),
                    "num_edges": len(parsed.edges),
                    "entry_point": parsed.entry_point,
                    "exit_points": parsed.exit_points,
                    "validation_passed": all(validation.values())
                },
                "structure": self.generator.generate_package_structure(parsed)
            }
            
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
            "nodes": ["parse_request", "generate_code", "validate_code", "finalize_output"]
        }

# Made with Bob
