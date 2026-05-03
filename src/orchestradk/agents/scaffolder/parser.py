import re
import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field, root_validator

from ...llm.client import LLMClient
from ...utils.exceptions import ParseError

logger = logging.getLogger(__name__)

class ParsedRequest(BaseModel):
    """Data contract for the IBM ADK Configurator."""
    agent_name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of functionality")
    nodes: List[Dict[str, str]] = Field(...)
    state_fields: List[Dict[str, str]] = Field(...)
    edges: List[Dict[str, str]] = Field(...)
    entry_point: str = Field(...)
    exit_points: List[str] = Field(...)

    class Config:
        # CRITICAL: This allows Pydantic to pass our injected fields to the Configurator
        extra = "allow"

    @root_validator(pre=True)
    def god_mode_injector(cls, values):
        """HACKATHON BYPASS: Inject every possible IBM schema array to satisfy hidden templates."""
        ibm_arrays = {
            "tools": [{"name": "script_executor", "description": "Run code"}],
            "skills": [{"name": "rag_search", "description": "Search docs"}],
            "collaborators": ["none"],
            "instructions": ["Analyze error logs", "Provide fixes"],
            "actions": [{"name": "script_executor", "description": "Run code"}],
            "functions": [{"name": "rag_search", "description": "Search"}],
            "inputs": [{"name": "query", "type": "string"}],
            "outputs": [{"name": "response", "type": "string"}],
            "parameters": [{"name": "logs", "type": "string"}],
            "dependencies": ["requests"],
            "capabilities": ["rag_search"],
            "memory": [{"type": "buffer"}],
            "system_prompts": ["You are a helpful DevOps agent."]
        }
        
        # Force-inject all arrays so the Jinja templates never render 'None'
        for key, default_val in ibm_arrays.items():
            if not values.get(key):
                values[key] = default_val
                
        # Ensure agent_name is a valid Python identifier
        if 'agent_name' in values:
            values['agent_name'] = re.sub(r'[^a-zA-Z0-9_]', '_', values['agent_name']).lower()
        return values

class RequestParser:
    SYSTEM_PROMPT = """You are a senior LangGraph architect. Output ONLY raw JSON.
Schema:
{
  "agent_name": "devops_agent",
  "description": "DevOps support agent",
  "nodes": [{"name": "node_a", "purpose": "process logs"}],
  "state_fields": [{"name": "logs", "type": "str"}],
  "edges": [{"from": "node_a", "to": "node_b"}],
  "entry_point": "node_a",
  "exit_points": ["node_b"]
}"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _extract_json(self, text: str) -> Dict[str, Any]:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                raise ParseError("AI returned invalid JSON syntax")
        raise ParseError("No JSON found in response")

    async def parse(self, request: str) -> ParsedRequest:
        try:
            prompt = f"Instruction: Convert to LangGraph JSON. No chatter.\nTask: '{request}'\n\nJSON:"
            raw_response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            data = self._extract_json(raw_response)
            parsed = ParsedRequest(**data)
            
            if not parsed.nodes:
                parsed.nodes = [{"name": "default_node", "purpose": "default logic"}]
            
            node_names = {node["name"] for node in parsed.nodes}
            if parsed.entry_point not in node_names:
                parsed.entry_point = parsed.nodes[0]["name"]
                
            return parsed
            
        except Exception as e:
            logger.error(f"Scaffolder Parsing failed: {str(e)}")
            raise ParseError(f"Failed to parse request: {str(e)}")