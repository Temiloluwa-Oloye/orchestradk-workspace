"""
YAML Generator for Agent B: The Configurator.

This module generates ADK-compliant YAML configuration files
(agent.yaml and skills.yaml) from scaffolder output.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import yaml
from jinja2 import Environment, FileSystemLoader, Template

from ...utils.exceptions import GenerationError

logger = logging.getLogger(__name__)


class YAMLGenerator:
    """
    Generates YAML configuration files for watsonx Orchestrate ADK.
    
    Produces:
    - agent.yaml: Agent metadata and structure
    - skills.yaml: Skill definitions and schemas
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the YAML generator.
        
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
        
        logger.info(f"YAMLGenerator initialized with template dir: {template_dir}")
    
    def generate_agent_yaml(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate agent.yaml configuration.
        
        Args:
            scaffolder_output: Output from Agent A (Scaffolder)
            additional_config: Additional configuration parameters
            
        Returns:
            Generated YAML content as string
            
        Raises:
            GenerationError: If generation fails
        """
        logger.info("Generating agent.yaml")
        
        try:
            # Extract data from scaffolder output
            metadata = scaffolder_output.get("metadata", {})
            structure = scaffolder_output.get("structure", {})
            
            # Prepare template context
            context = self._prepare_agent_context(
                scaffolder_output,
                additional_config or {}
            )
            
            # Load and render template
            template = self.env.get_template("agent.yaml.jinja2")
            yaml_content = template.render(**context)
            
            # Validate YAML syntax
            self._validate_yaml_syntax(yaml_content, "agent.yaml")
            
            logger.info("agent.yaml generated successfully")
            return yaml_content
            
        except Exception as e:
            logger.error(f"Failed to generate agent.yaml: {str(e)}")
            raise GenerationError(f"agent.yaml generation failed: {str(e)}")
    
    def generate_skills_yaml(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate skills.yaml configuration.
        
        Args:
            scaffolder_output: Output from Agent A (Scaffolder)
            additional_config: Additional configuration parameters
            
        Returns:
            Generated YAML content as string
            
        Raises:
            GenerationError: If generation fails
        """
        logger.info("Generating skills.yaml")
        
        try:
            # Prepare template context
            context = self._prepare_skills_context(
                scaffolder_output,
                additional_config or {}
            )
            
            # Load and render template
            template = self.env.get_template("skills.yaml.jinja2")
            yaml_content = template.render(**context)
            
            # Validate YAML syntax
            self._validate_yaml_syntax(yaml_content, "skills.yaml")
            
            logger.info("skills.yaml generated successfully")
            return yaml_content
            
        except Exception as e:
            logger.error(f"Failed to generate skills.yaml: {str(e)}")
            raise GenerationError(f"skills.yaml generation failed: {str(e)}")
    
    def _prepare_agent_context(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare context for agent.yaml template.
        
        Args:
            scaffolder_output: Scaffolder output
            additional_config: Additional configuration
            
        Returns:
            Template context dictionary
        """
        metadata = scaffolder_output.get("metadata", {})
        structure = scaffolder_output.get("structure", {})
        
        # Extract agent information
        agent_name = scaffolder_output.get("agent_name", "unnamed_agent")
        description = scaffolder_output.get("description", "Generated agent")
        
        # Extract state fields
        state_fields = self._extract_state_fields(scaffolder_output)
        
        # Extract nodes
        nodes = self._extract_nodes(scaffolder_output)
        
        # Extract edges
        edges = self._extract_edges(scaffolder_output)
        
        # Prepare context
        context = {
            "agent_name": agent_name,
            "version": additional_config.get("version", "1.0.0"),
            "description": description,
            "author": additional_config.get("author", "OrchestrADK"),
            "created_at": datetime.utcnow().isoformat(),
            "python_version": additional_config.get("python_version", "3.10+"),
            "entry_point": structure.get("entry_point", "main.py"),
            "additional_dependencies": additional_config.get("dependencies", []),
            "capabilities": self._extract_capabilities(scaffolder_output),
            "state_fields": state_fields,
            "nodes": nodes,
            "workflow_entry_point": metadata.get("entry_point", "start"),
            "exit_points": metadata.get("exit_points", ["end"]),
            "edges": edges
        }
        
        return context
    
    def _prepare_skills_context(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare context for skills.yaml template.
        
        Args:
            scaffolder_output: Scaffolder output
            additional_config: Additional configuration
            
        Returns:
            Template context dictionary
        """
        # Convert nodes to skills
        skills = self._nodes_to_skills(scaffolder_output)
        
        # Extract skill dependencies from edges
        skill_dependencies = self._extract_skill_dependencies(scaffolder_output)
        
        context = {
            "skills": skills,
            "skill_dependencies": skill_dependencies
        }
        
        return context
    
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
        metadata = scaffolder_output.get("metadata", {})
        num_fields = metadata.get("num_state_fields", 0)
        
        # Parse state fields from structure or files
        state_fields = {}
        
        # Try to extract from files
        files = scaffolder_output.get("files", {})
        state_file = files.get("state.py", "")
        
        if state_file:
            # Simple extraction - in production, use AST parsing
            # For now, create default fields
            state_fields = {
                "messages": {
                    "type": "list",
                    "description": "Conversation messages",
                    "required": True
                },
                "context": {
                    "type": "dict",
                    "description": "Conversation context",
                    "required": False
                }
            }
        
        return state_fields
    
    def _extract_nodes(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract node information from scaffolder output.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            List of node dictionaries
        """
        structure = scaffolder_output.get("structure", {})
        nodes_info = structure.get("nodes", [])
        
        nodes = []
        for node_info in nodes_info:
            if isinstance(node_info, dict):
                nodes.append({
                    "name": node_info.get("name", "unknown"),
                    "description": node_info.get("description", "Node function"),
                    "function": node_info.get("function", node_info.get("name", "unknown")),
                    "inputs": node_info.get("inputs", []),
                    "outputs": node_info.get("outputs", [])
                })
            elif isinstance(node_info, str):
                nodes.append({
                    "name": node_info,
                    "description": f"{node_info} node",
                    "function": node_info,
                    "inputs": [],
                    "outputs": []
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
                edges.append(edge)
            elif isinstance(edge_info, (list, tuple)) and len(edge_info) >= 2:
                edges.append({
                    "from": edge_info[0],
                    "to": edge_info[1]
                })
        
        return edges
    
    def _extract_capabilities(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> List[str]:
        """
        Extract agent capabilities from scaffolder output.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            List of capability strings
        """
        # Default capabilities
        capabilities = [
            "conversational",
            "stateful",
            "multi-step"
        ]
        
        # Add based on structure
        metadata = scaffolder_output.get("metadata", {})
        if metadata.get("num_nodes", 0) > 3:
            capabilities.append("complex-workflow")
        
        return capabilities
    
    def _nodes_to_skills(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert LangGraph nodes to ADK skills.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            List of skill dictionaries
        """
        nodes = self._extract_nodes(scaffolder_output)
        agent_name = scaffolder_output.get("agent_name", "agent")
        
        skills = []
        for i, node in enumerate(nodes):
            skill = {
                "id": f"{agent_name}_{node['name']}",
                "name": node["name"].replace("_", " ").title(),
                "description": node.get("description", f"Skill for {node['name']}"),
                "version": "1.0.0",
                "input_schema": self._generate_input_schema(node),
                "output_schema": self._generate_output_schema(node),
                "required_inputs": self._get_required_inputs(node),
                "node_name": node["name"],
                "module": f"{agent_name}.nodes",
                "function": node["function"],
                "category": "agent_skill",
                "tags": ["langgraph", "generated", agent_name]
            }
            skills.append(skill)
        
        return skills
    
    def _generate_input_schema(
        self,
        node: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate input schema for a node/skill.
        
        Args:
            node: Node information
            
        Returns:
            Input schema dictionary
        """
        # Default input schema
        schema = {
            "state": {
                "type": "object",
                "description": "Current agent state",
                "required": True
            }
        }
        
        # Add node-specific inputs
        for input_field in node.get("inputs", []):
            schema[input_field] = {
                "type": "string",
                "description": f"Input: {input_field}",
                "required": False
            }
        
        return schema
    
    def _generate_output_schema(
        self,
        node: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate output schema for a node/skill.
        
        Args:
            node: Node information
            
        Returns:
            Output schema dictionary
        """
        # Default output schema
        schema = {
            "state": {
                "type": "object",
                "description": "Updated agent state"
            }
        }
        
        # Add node-specific outputs
        for output_field in node.get("outputs", []):
            schema[output_field] = {
                "type": "string",
                "description": f"Output: {output_field}"
            }
        
        return schema
    
    def _get_required_inputs(
        self,
        node: Dict[str, Any]
    ) -> List[str]:
        """
        Get required input fields for a node.
        
        Args:
            node: Node information
            
        Returns:
            List of required input field names
        """
        # State is always required
        return ["state"]
    
    def _extract_skill_dependencies(
        self,
        scaffolder_output: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Extract skill dependencies from edges.
        
        Args:
            scaffolder_output: Scaffolder output
            
        Returns:
            List of dependency dictionaries
        """
        edges = self._extract_edges(scaffolder_output)
        agent_name = scaffolder_output.get("agent_name", "agent")
        
        dependencies = []
        for edge in edges:
            dependencies.append({
                "from": f"{agent_name}_{edge['from']}",
                "to": f"{agent_name}_{edge['to']}",
                "type": "sequential"
            })
        
        return dependencies
    
    def _validate_yaml_syntax(self, yaml_content: str, filename: str) -> None:
        """
        Validate YAML syntax.
        
        Args:
            yaml_content: YAML content to validate
            filename: Filename for error messages
            
        Raises:
            GenerationError: If YAML is invalid
        """
        try:
            yaml.safe_load(yaml_content)
            logger.debug(f"{filename} syntax validation passed")
        except yaml.YAMLError as e:
            logger.error(f"{filename} syntax validation failed: {str(e)}")
            raise GenerationError(f"Invalid YAML syntax in {filename}: {str(e)}")
    
    def generate_all(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate all YAML configuration files.
        
        Args:
            scaffolder_output: Output from Agent A (Scaffolder)
            additional_config: Additional configuration parameters
            
        Returns:
            Dictionary mapping filenames to YAML content
            
        Raises:
            GenerationError: If generation fails
        """
        logger.info("Generating all YAML configuration files")
        
        try:
            agent_yaml = self.generate_agent_yaml(scaffolder_output, additional_config)
            skills_yaml = self.generate_skills_yaml(scaffolder_output, additional_config)
            
            return {
                "agent.yaml": agent_yaml,
                "skills.yaml": skills_yaml
            }
            
        except Exception as e:
            logger.error(f"Failed to generate YAML files: {str(e)}")
            raise GenerationError(f"YAML generation failed: {str(e)}")


# Made with Bob