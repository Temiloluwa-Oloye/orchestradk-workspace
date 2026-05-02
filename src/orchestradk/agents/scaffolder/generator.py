"""
Code generator for scaffolder agent.

This module generates Python LangGraph boilerplate code from parsed requests.
"""

from typing import Dict, Any, List
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .parser import ParsedRequest
from ...utils.exceptions import GenerationError, TemplateError

logger = logging.getLogger(__name__)


class CodeGenerator:
    """
    Generator for LangGraph Python code.
    
    Uses Jinja2 templates to generate state definitions, node implementations,
    and graph construction code.
    """
    
    def __init__(self, template_dir: str = None):
        """
        Initialize the code generator.
        
        Args:
            template_dir: Path to template directory (defaults to ./templates)
        """
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")
        
        try:
            self.env = Environment(
                loader=FileSystemLoader(template_dir),
                trim_blocks=True,
                lstrip_blocks=True
            )
            logger.info(f"CodeGenerator initialized with templates from: {template_dir}")
        except Exception as e:
            raise TemplateError(
                f"Failed to initialize template environment: {str(e)}",
                {"template_dir": template_dir}
            )
    
    def generate_all(self, parsed: ParsedRequest) -> Dict[str, str]:
        """
        Generate all code files for the agent.
        
        Args:
            parsed: Parsed request with agent structure
            
        Returns:
            Dictionary mapping filenames to generated code
            
        Raises:
            GenerationError: If code generation fails
        """
        logger.info(f"Generating code for agent: {parsed.agent_name}")
        
        try:
            generated = {
                "state.py": self.generate_state(parsed),
                "nodes.py": self.generate_nodes(parsed),
                "graph.py": self.generate_graph(parsed),
                "__init__.py": self.generate_init(parsed)
            }
            
            logger.info(f"Successfully generated {len(generated)} files")
            return generated
            
        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            raise GenerationError(
                "Failed to generate agent code",
                {"error": str(e), "agent": parsed.agent_name}
            )
    
    def generate_state(self, parsed: ParsedRequest) -> str:
        """
        Generate state definition code.
        
        Args:
            parsed: Parsed request
            
        Returns:
            Generated Python code for state class
        """
        try:
            template = self.env.get_template("state.py.jinja2")
            
            # Prepare state fields with proper type annotations
            state_fields = []
            for field in parsed.state_fields:
                state_fields.append({
                    "name": field["name"],
                    "type": field["type"],
                    "description": f"State field for {field['name']}"
                })
            
            code = template.render(
                agent_name=parsed.agent_name,
                description=parsed.description,
                state_fields=state_fields
            )
            
            logger.debug(f"Generated state.py ({len(code)} chars)")
            return code
            
        except TemplateNotFound:
            raise TemplateError("state.py.jinja2 template not found")
        except Exception as e:
            raise GenerationError(
                "Failed to generate state code",
                {"error": str(e)}
            )
    
    def generate_nodes(self, parsed: ParsedRequest) -> str:
        """
        Generate node implementation code.
        
        Args:
            parsed: Parsed request
            
        Returns:
            Generated Python code for node functions
        """
        try:
            template = self.env.get_template("nodes.py.jinja2")
            
            # Prepare node information
            nodes = []
            for node in parsed.nodes:
                nodes.append({
                    "name": node["name"],
                    "purpose": node["purpose"],
                    "description": f"Node: {node['purpose']}"
                })
            
            code = template.render(
                agent_name=parsed.agent_name,
                description=parsed.description,
                nodes=nodes,
                state_fields=parsed.state_fields
            )
            
            logger.debug(f"Generated nodes.py ({len(code)} chars)")
            return code
            
        except TemplateNotFound:
            raise TemplateError("nodes.py.jinja2 template not found")
        except Exception as e:
            raise GenerationError(
                "Failed to generate nodes code",
                {"error": str(e)}
            )
    
    def generate_graph(self, parsed: ParsedRequest) -> str:
        """
        Generate graph construction code.
        
        Args:
            parsed: Parsed request
            
        Returns:
            Generated Python code for graph construction
        """
        try:
            template = self.env.get_template("graph.py.jinja2")
            
            # Prepare edge information
            edges = []
            for edge in parsed.edges:
                edges.append({
                    "from": edge["from"],
                    "to": edge["to"],
                    "conditional": edge.get("conditional", False)
                })
            
            # Prepare node names
            node_names = [node["name"] for node in parsed.nodes]
            
            code = template.render(
                agent_name=parsed.agent_name,
                description=parsed.description,
                nodes=node_names,
                edges=edges,
                entry_point=parsed.entry_point,
                exit_points=parsed.exit_points
            )
            
            logger.debug(f"Generated graph.py ({len(code)} chars)")
            return code
            
        except TemplateNotFound:
            raise TemplateError("graph.py.jinja2 template not found")
        except Exception as e:
            raise GenerationError(
                "Failed to generate graph code",
                {"error": str(e)}
            )
    
    def generate_init(self, parsed: ParsedRequest) -> str:
        """
        Generate __init__.py for the agent package.
        
        Args:
            parsed: Parsed request
            
        Returns:
            Generated Python code for __init__.py
        """
        code = f'''"""
{parsed.agent_name} - {parsed.description}

This agent was generated by OrchestrADK.
"""

from .state import AgentState
from .nodes import {", ".join(node["name"] for node in parsed.nodes)}
from .graph import create_graph

__all__ = [
    "AgentState",
    {", ".join(f'"{node["name"]}"' for node in parsed.nodes)},
    "create_graph"
]
'''
        
        logger.debug(f"Generated __init__.py ({len(code)} chars)")
        return code
    
    def validate_generated_code(self, code: str) -> bool:
        """
        Validate generated Python code syntax.
        
        Args:
            code: Python code to validate
            
        Returns:
            True if valid, False otherwise
        """
        import ast
        
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.error(f"Syntax error in generated code: {str(e)}")
            return False
    
    def format_code(self, code: str) -> str:
        """
        Format generated code (basic formatting).
        
        Args:
            code: Code to format
            
        Returns:
            Formatted code
        """
        # Basic formatting: ensure consistent line endings and spacing
        lines = code.split('\n')
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in lines]
        
        # Remove multiple consecutive blank lines
        formatted_lines = []
        prev_blank = False
        for line in lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue
            formatted_lines.append(line)
            prev_blank = is_blank
        
        return '\n'.join(formatted_lines)
    
    def generate_package_structure(self, parsed: ParsedRequest) -> Dict[str, Any]:
        """
        Generate complete package structure information.
        
        Args:
            parsed: Parsed request
            
        Returns:
            Dictionary with package structure details
        """
        return {
            "package_name": parsed.agent_name,
            "files": ["state.py", "nodes.py", "graph.py", "__init__.py"],
            "entry_point": "graph.create_graph",
            "dependencies": [
                "langgraph>=0.2.0",
                "langchain>=0.3.0",
                "pydantic>=2.0"
            ],
            "metadata": {
                "description": parsed.description,
                "num_nodes": len(parsed.nodes),
                "num_state_fields": len(parsed.state_fields)
            }
        }

# Made with Bob
