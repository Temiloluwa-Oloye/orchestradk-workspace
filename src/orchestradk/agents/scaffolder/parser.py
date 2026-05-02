"""
Natural language parser for scaffolder agent.

This module parses developer requests and extracts LangGraph components.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from ...llm.client import LLMClient
from ...utils.exceptions import ParseError

logger = logging.getLogger(__name__)


class ParsedRequest(BaseModel):
    """Structured representation of a parsed developer request."""
    
    agent_name: str = Field(..., description="Name of the agent to create")
    description: str = Field(..., description="Description of agent functionality")
    nodes: List[Dict[str, str]] = Field(..., description="List of nodes with name and purpose")
    state_fields: List[Dict[str, str]] = Field(..., description="State fields with name and type")
    edges: List[Dict[str, str]] = Field(..., description="Edges connecting nodes")
    entry_point: str = Field(..., description="Entry node name")
    exit_points: List[str] = Field(..., description="Exit node names")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "customer_support_agent",
                "description": "Agent for handling customer support queries",
                "nodes": [
                    {"name": "classify_query", "purpose": "Classify the type of customer query"},
                    {"name": "lookup_faq", "purpose": "Search FAQ database"},
                    {"name": "generate_response", "purpose": "Generate response to customer"}
                ],
                "state_fields": [
                    {"name": "query", "type": "str"},
                    {"name": "query_type", "type": "str"},
                    {"name": "faq_results", "type": "List[str]"},
                    {"name": "response", "type": "str"}
                ],
                "edges": [
                    {"from": "classify_query", "to": "lookup_faq"},
                    {"from": "lookup_faq", "to": "generate_response"}
                ],
                "entry_point": "classify_query",
                "exit_points": ["generate_response"]
            }
        }


class RequestParser:
    """
    Parser for natural language developer requests.
    
    Uses LLM to extract structured information about the desired
    LangGraph agent from natural language descriptions.
    """
    
    SYSTEM_PROMPT = """You are an expert at analyzing developer requests for creating LangGraph agents.
Your task is to parse natural language descriptions and extract structured information about:
1. Agent name and purpose
2. Required nodes (processing steps)
3. State fields (data to track)
4. Edges (connections between nodes)
5. Entry and exit points

Respond with valid JSON matching this schema:
{
  "agent_name": "snake_case_name",
  "description": "Brief description",
  "nodes": [{"name": "node_name", "purpose": "what it does"}],
  "state_fields": [{"name": "field_name", "type": "python_type"}],
  "edges": [{"from": "source_node", "to": "target_node"}],
  "entry_point": "first_node_name",
  "exit_points": ["final_node_name"]
}

Guidelines:
- Use snake_case for all names
- Keep node names descriptive but concise
- Infer reasonable state fields based on the workflow
- Create a logical flow from entry to exit
- Include conditional edges if the request implies branching logic
"""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the parser.
        
        Args:
            llm_client: LLM client for parsing
        """
        self.llm_client = llm_client
        logger.info("RequestParser initialized")
    
    async def parse(self, request: str) -> ParsedRequest:
        """
        Parse a natural language request into structured format.
        
        Args:
            request: Natural language description of desired agent
            
        Returns:
            ParsedRequest with extracted information
            
        Raises:
            ParseError: If parsing fails
        """
        if not request or not request.strip():
            raise ParseError("Empty request provided")
        
        logger.info(f"Parsing request: {request[:100]}...")
        
        try:
            # Generate structured output using LLM
            prompt = f"""Parse this developer request for creating a LangGraph agent:

"{request}"

Extract the agent structure and respond with JSON."""
            
            parsed_json = await self.llm_client.generate_structured(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            # Validate and create ParsedRequest
            parsed = ParsedRequest(**parsed_json)
            
            # Post-process and validate
            self._validate_parsed_request(parsed)
            
            logger.info(f"Successfully parsed request: {parsed.agent_name}")
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse request: {str(e)}")
            raise ParseError(
                "Failed to parse developer request",
                {"error": str(e), "request": request[:200]}
            )
    
    def _validate_parsed_request(self, parsed: ParsedRequest) -> None:
        """
        Validate the parsed request for consistency.
        
        Args:
            parsed: The parsed request to validate
            
        Raises:
            ParseError: If validation fails
        """
        # Check that entry point exists in nodes
        node_names = {node["name"] for node in parsed.nodes}
        
        if parsed.entry_point not in node_names:
            raise ParseError(
                f"Entry point '{parsed.entry_point}' not found in nodes",
                {"nodes": list(node_names)}
            )
        
        # Check that exit points exist in nodes
        for exit_point in parsed.exit_points:
            if exit_point not in node_names:
                raise ParseError(
                    f"Exit point '{exit_point}' not found in nodes",
                    {"nodes": list(node_names)}
                )
        
        # Check that edges reference valid nodes
        for edge in parsed.edges:
            if edge["from"] not in node_names:
                raise ParseError(
                    f"Edge source '{edge['from']}' not found in nodes",
                    {"nodes": list(node_names)}
                )
            if edge["to"] not in node_names:
                raise ParseError(
                    f"Edge target '{edge['to']}' not found in nodes",
                    {"nodes": list(node_names)}
                )
        
        # Ensure at least one node exists
        if not parsed.nodes:
            raise ParseError("No nodes defined in parsed request")
        
        # Ensure at least one state field exists
        if not parsed.state_fields:
            raise ParseError("No state fields defined in parsed request")
        
        logger.debug("Parsed request validation successful")
    
    def extract_requirements(self, parsed: ParsedRequest) -> Dict[str, Any]:
        """
        Extract additional requirements from parsed request.
        
        Args:
            parsed: The parsed request
            
        Returns:
            Dictionary of extracted requirements
        """
        return {
            "num_nodes": len(parsed.nodes),
            "num_state_fields": len(parsed.state_fields),
            "num_edges": len(parsed.edges),
            "has_branching": self._has_branching_logic(parsed),
            "complexity": self._estimate_complexity(parsed)
        }
    
    def _has_branching_logic(self, parsed: ParsedRequest) -> bool:
        """Check if the graph has branching logic."""
        # Count outgoing edges from each node
        outgoing_counts: Dict[str, int] = {}
        for edge in parsed.edges:
            source = edge["from"]
            outgoing_counts[source] = outgoing_counts.get(source, 0) + 1
        
        # If any node has multiple outgoing edges, there's branching
        return any(count > 1 for count in outgoing_counts.values())
    
    def _estimate_complexity(self, parsed: ParsedRequest) -> str:
        """Estimate the complexity of the agent."""
        num_nodes = len(parsed.nodes)
        num_edges = len(parsed.edges)
        
        if num_nodes <= 3 and num_edges <= 3:
            return "simple"
        elif num_nodes <= 6 and num_edges <= 8:
            return "moderate"
        else:
            return "complex"

# Made with Bob
