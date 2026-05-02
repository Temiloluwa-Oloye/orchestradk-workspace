"""
JSON Generator for Agent B: The Configurator.

This module generates ADK-compliant JSON configuration files
(config.json and schema.json) from scaffolder output.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from ...utils.exceptions import GenerationError

logger = logging.getLogger(__name__)


class JSONGenerator:
    """
    Generates JSON configuration files for watsonx Orchestrate ADK.
    
    Produces:
    - config.json: Runtime configuration
    - schema.json: Input/output schemas
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the JSON generator.
        
        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.info(f"JSONGenerator initialized with template dir: {template_dir}")
    
    def generate_config_json(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate config.json runtime configuration.
        
        Args:
            scaffolder_output: Output from Agent A (Scaffolder)
            additional_config: Additional configuration parameters
            
        Returns:
            Generated JSON content as string
            
        Raises:
            GenerationError: If generation fails
        """
        logger.info("Generating config.json")
        
        try:
            # Prepare template context
            context = self._prepare_config_context(
                scaffolder_output,
                additional_config or {}
            )
            
            # Load and render template
            template = self.env.get_template("config.json.jinja2")
            json_content = template.render(**context)
            
            # Validate JSON syntax
            self._validate_json_syntax(json_content, "config.json")
            
            # Pretty print JSON
            json_obj = json.loads(json_content)
            json_content = json.dumps(json_obj, indent=2)
            
            logger.info("config.json generated successfully")
            return json_content
            
        except Exception as e:
            logger.error(f"Failed to generate config.json: {str(e)}")
            raise GenerationError(f"config.json generation failed: {str(e)}")
    
    def generate_schema_json(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate schema.json for input/output validation.
        
        Args:
            scaffolder_output: Output from Agent A (Scaffolder)
            additional_config: Additional configuration parameters
            
        Returns:
            Generated JSON content as string
            
        Raises:
            GenerationError: If generation fails
        """
        logger.info("Generating schema.json")
        
        try:
            # Build JSON schema
            schema = self._build_json_schema(scaffolder_output, additional_config or {})
            
            # Convert to JSON string
            json_content = json.dumps(schema, indent=2)
            
            # Validate JSON syntax
            self._validate_json_syntax(json_content, "schema.json")
            
            logger.info("schema.json generated successfully")
            return json_content
            
        except Exception as e:
            logger.error(f"Failed to generate schema.json: {str(e)}")
            raise GenerationError(f"schema.json generation failed: {str(e)}")
    
    def _prepare_config_context(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare context for config.json template.
        
        Args:
            scaffolder_output: Scaffolder output
            additional_config: Additional configuration
            
        Returns:
            Template context dictionary
        """
        metadata = scaffolder_output.get("metadata", {})
        structure = scaffolder_output.get("structure", {})
        
        # Extract basic information
        agent_name = scaffolder_output.get("agent_name", "unnamed_agent")
        description = scaffolder_output.get("description", "Generated agent")
        
        # Extract state fields
        state_fields = self._extract_state_fields(scaffolder_output)
        
        # Extract nodes with enhanced information
        nodes = self._extract_nodes_for_config(scaffolder_output)
        
        # Extract edges
        edges = self._extract_edges(scaffolder_output)
        
        # Prepare context with all configuration parameters
        context = {
            # Agent info
            "agent_name": agent_name,
            "version": additional_config.get("version", "1.0.0"),
            "description": description,
            
            # Runtime config
            "python_version": additional_config.get("python_version", "3.10"),
            "entry_point": structure.get("entry_point", "main.py"),
            "timeout": additional_config.get("timeout", 300),
            "max_retries": additional_config.get("max_retries", 3),
            "memory_limit": additional_config.get("memory_limit", "512MB"),
            
            # LLM config
            "llm_provider": additional_config.get("llm_provider", "watsonx"),
            "llm_model": additional_config.get("llm_model", "ibm/granite-13b-chat-v2"),
            "llm_temperature": additional_config.get("llm_temperature", 0.7),
            "llm_max_tokens": additional_config.get("llm_max_tokens", 2048),
            "llm_top_p": additional_config.get("llm_top_p", 0.9),
            "llm_top_k": additional_config.get("llm_top_k", 50),
            
            # State config
            "state_persistence": additional_config.get("state_persistence", False),
            "state_backend": additional_config.get("state_backend", "memory"),
            "state_fields": state_fields,
            
            # Workflow config
            "nodes": nodes,
            "edges": edges,
            "workflow_entry_point": metadata.get("entry_point", "start"),
            "exit_points": metadata.get("exit_points", ["end"]),
            
            # Error handling
            "error_strategy": additional_config.get("error_strategy", "retry"),
            "error_max_retries": additional_config.get("error_max_retries", 3),
            "error_fallback_node": additional_config.get("error_fallback_node", ""),
            
            # Logging
            "log_level": additional_config.get("log_level", "INFO"),
            "log_format": additional_config.get("log_format", "json"),
            "log_destinations": additional_config.get("log_destinations", ["console"]),
            
            # Monitoring
            "monitoring_enabled": additional_config.get("monitoring_enabled", True),
            "monitoring_metrics": additional_config.get("monitoring_metrics", ["latency", "throughput", "errors"]),
            "monitoring_tracing": additional_config.get("monitoring_tracing", False),
            
            # Security
            "security_auth": additional_config.get("security_auth", True),
            "security_authz": additional_config.get("security_authz", True),
            "security_encryption_rest": additional_config.get("security_encryption_rest", False),
            "security_encryption_transit": additional_config.get("security_encryption_transit", True),
            
            # Metadata
            "created_at": datetime.utcnow().isoformat(),
            "created_by": additional_config.get("created_by", "OrchestrADK"),
            "framework_version": additional_config.get("framework_version", "0.1.0"),
            "tags": additional_config.get("tags", [])
        }
        
        return context
    
    def _build_json_schema(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build JSON schema for agent input/output validation.
        
        Args:
            scaffolder_output: Scaffolder output
            additional_config: Additional configuration
            
        Returns:
            JSON schema dictionary
        """
        agent_name = scaffolder_output.get("agent_name", "unnamed_agent")
        description = scaffolder_output.get("description", "Generated agent")
        
        # Build input schema
        input_schema = self._build_input_schema(scaffolder_output)
        
        # Build output schema
        output_schema = self._build_output_schema(scaffolder_output)
        
        # Build state schema
        state_schema = self._build_state_schema(scaffolder_output)
        
        # Combine into full schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"https://orchestrate.ibm.com/schemas/{agent_name}/v1",
            "title": agent_name.replace("_", " ").title(),
            "description": description,
            "type": "object",
            "definitions": {
                "state": state_schema,
                "input": input_schema,
                "output": output_schema
            },
            "properties": {
                "input": {
                    "$ref": "#/definitions/input"
                },
                "output": {
                    "$ref": "#/definitions/output"
                },
                "state": {
                    "$ref": "#/definitions/state"
                }
            },
            "required": ["input"],
            "additionalProperties": False
        }
        
        return schema
    
    def _build_input_schema(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build input schema definition.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            Input schema dictionary
        """
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "User input message"
                },
                "context": {
                    "type": "object",
                    "description": "Additional context",
                    "additionalProperties": True
                },
                "session_id": {
                    "type": "string",
                    "description": "Session identifier"
                }
            },
            "required": ["message"],
            "additionalProperties": False
        }
    
    def _build_output_schema(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build output schema definition.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            Output schema dictionary
        """
        return {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "Agent response message"
                },
                "metadata": {
                    "type": "object",
                    "description": "Response metadata",
                    "properties": {
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        },
                        "sources": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    }
                },
                "next_action": {
                    "type": "string",
                    "description": "Suggested next action"
                }
            },
            "required": ["response"],
            "additionalProperties": False
        }
    
    def _build_state_schema(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build state schema definition.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            State schema dictionary
        """
        state_fields = self._extract_state_fields(scaffolder_output)
        
        properties = {}
        required = []
        
        for field_name, field_info in state_fields.items():
            properties[field_name] = {
                "type": self._map_type_to_json_schema(field_info.get("type", "string")),
                "description": field_info.get("description", f"State field: {field_name}")
            }
            
            if field_info.get("required", False):
                required.append(field_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": True
        }
    
    def _extract_state_fields(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract state fields from scaffolder output.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            Dictionary of state fields with metadata
        """
        # Default state fields
        state_fields = {
            "messages": {
                "type": "array",
                "description": "Conversation messages",
                "required": True
            },
            "context": {
                "type": "object",
                "description": "Conversation context",
                "required": False
            }
        }
        
        return state_fields
    
    def _extract_nodes_for_config(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract node information for config.json.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            List of node dictionaries with config
        """
        structure = scaffolder_output.get("structure", {})
        nodes_info = structure.get("nodes", [])
        
        nodes = []
        for node_info in nodes_info:
            if isinstance(node_info, dict):
                node = {
                    "name": node_info.get("name", "unknown"),
                    "type": node_info.get("type", "function"),
                    "function": node_info.get("function", node_info.get("name", "unknown")),
                    "description": node_info.get("description", "Node function"),
                    "timeout": node_info.get("timeout", 60),
                    "retries": node_info.get("retries", 2)
                }
                if "dependencies" in node_info:
                    node["dependencies"] = node_info["dependencies"]
                nodes.append(node)
            elif isinstance(node_info, str):
                nodes.append({
                    "name": node_info,
                    "type": "function",
                    "function": node_info,
                    "description": f"{node_info} node",
                    "timeout": 60,
                    "retries": 2
                })
        
        return nodes
    
    def _extract_edges(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract edge information from scaffolder output.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            List of edge dictionaries
        """
        structure = scaffolder_output.get("structure", {})
        edges_info = structure.get("edges", [])
        
        edges = []
        for edge_info in edges_info:
            if isinstance(edge_info, dict):
                edge = {
                    "from": edge_info.get("from", ""),
                    "to": edge_info.get("to", "")
                }
                if "condition" in edge_info:
                    edge["condition"] = edge_info["condition"]
                if "condition_type" in edge_info:
                    edge["condition_type"] = edge_info["condition_type"]
                edges.append(edge)
            elif isinstance(edge_info, (list, tuple)) and len(edge_info) >= 2:
                edges.append({
                    "from": edge_info[0],
                    "to": edge_info[1]
                })
        
        return edges
    
    def _map_type_to_json_schema(self, python_type: str) -> str:
        """
        Map Python type to JSON schema type.
        
        Args:
            python_type: Python type string
            
        Returns:
            JSON schema type string
        """
        type_mapping = {
            "str": "string",
            "string": "string",
            "int": "integer",
            "integer": "integer",
            "float": "number",
            "number": "number",
            "bool": "boolean",
            "boolean": "boolean",
            "list": "array",
            "array": "array",
            "dict": "object",
            "object": "object",
            "any": "string"
        }
        
        return type_mapping.get(python_type.lower(), "string")
    
    def _validate_json_syntax(self, json_content: str, filename: str) -> None:
        """
        Validate JSON syntax.
        
        Args:
            json_content: JSON content to validate
            filename: Filename for error messages
            
        Raises:
            GenerationError: If JSON is invalid
        """
        try:
            json.loads(json_content)
            logger.debug(f"{filename} syntax validation passed")
        except json.JSONDecodeError as e:
            logger.error(f"{filename} syntax validation failed: {str(e)}")
            raise GenerationError(f"Invalid JSON syntax in {filename}: {str(e)}")
    
    def generate_all(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate all JSON configuration files.
        
        Args:
            scaffolder_output: Output from Agent A (Scaffolder)
            additional_config: Additional configuration parameters
            
        Returns:
            Dictionary mapping filenames to JSON content
            
        Raises:
            GenerationError: If generation fails
        """
        logger.info("Generating all JSON configuration files")
        
        try:
            config_json = self.generate_config_json(scaffolder_output, additional_config)
            schema_json = self.generate_schema_json(scaffolder_output, additional_config)
            
            return {
                "config.json": config_json,
                "schema.json": schema_json
            }
            
        except Exception as e:
            logger.error(f"Failed to generate JSON files: {str(e)}")
            raise GenerationError(f"JSON generation failed: {str(e)}")


# Made with Bob