"""
Schema Validator for Agent B: The Configurator.

This module validates generated configuration files against
ADK schemas and ensures compliance with watsonx Orchestrate requirements.
"""

import logging
import json
import yaml
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from jsonschema import validate, ValidationError as JSONSchemaValidationError, Draft7Validator

from ...utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validates configuration files against ADK schemas.
    
    Validates:
    - agent.yaml against agent schema
    - skills.yaml against skill schema
    - config.json against config schema
    - schema.json against JSON Schema Draft 7
    """
    
    def __init__(self, schema_dir: Optional[Path] = None):
        """
        Initialize the schema validator.
        
        Args:
            schema_dir: Directory containing ADK schema definitions
        """
        if schema_dir is None:
            # Default to config/adk_schemas directory
            schema_dir = Path(__file__).parent.parent.parent.parent.parent / "config" / "adk_schemas"
        
        self.schema_dir = schema_dir
        self.schemas: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"SchemaValidator initialized with schema dir: {schema_dir}")
    
    def load_schemas(self) -> None:
        """
        Load ADK schema definitions from files.
        
        Raises:
            ValidationError: If schemas cannot be loaded
        """
        logger.info("Loading ADK schemas")
        
        try:
            # Load agent schema
            agent_schema_path = self.schema_dir / "agent_schema.json"
            if agent_schema_path.exists() and agent_schema_path.stat().st_size > 0:
                with open(agent_schema_path, 'r') as f:
                    self.schemas['agent'] = json.load(f)
                logger.info("Loaded agent schema")
            else:
                logger.warning("agent_schema.json not found or empty, using default")
                self.schemas['agent'] = self._get_default_agent_schema()
            
            # Load skill schema
            skill_schema_path = self.schema_dir / "skill_schema.json"
            if skill_schema_path.exists() and skill_schema_path.stat().st_size > 0:
                with open(skill_schema_path, 'r') as f:
                    self.schemas['skill'] = json.load(f)
                logger.info("Loaded skill schema")
            else:
                logger.warning("skill_schema.json not found or empty, using default")
                self.schemas['skill'] = self._get_default_skill_schema()
            
            # Config schema is built dynamically
            self.schemas['config'] = self._get_default_config_schema()
            
        except Exception as e:
            logger.error(f"Failed to load schemas: {str(e)}")
            raise ValidationError(f"Schema loading failed: {str(e)}")
    
    def validate_agent_yaml(self, yaml_content: str) -> Tuple[bool, List[str]]:
        """
        Validate agent.yaml against ADK agent schema.
        
        Args:
            yaml_content: YAML content to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        logger.info("Validating agent.yaml")
        
        errors = []
        
        try:
            # Parse YAML
            data = yaml.safe_load(yaml_content)
            
            # Ensure schemas are loaded
            if 'agent' not in self.schemas:
                self.load_schemas()
            
            # Validate against schema
            try:
                validate(instance=data, schema=self.schemas['agent'])
            except JSONSchemaValidationError as e:
                errors.append(f"Schema validation error: {e.message}")
                logger.error(f"agent.yaml validation failed: {e.message}")
            
            # Additional ADK-specific validations
            adk_errors = self._validate_agent_adk_requirements(data)
            errors.extend(adk_errors)
            
            if errors:
                logger.warning(f"agent.yaml validation found {len(errors)} errors")
                return False, errors
            
            logger.info("agent.yaml validation passed")
            return True, []
            
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def validate_skills_yaml(self, yaml_content: str) -> Tuple[bool, List[str]]:
        """
        Validate skills.yaml against ADK skill schema.
        
        Args:
            yaml_content: YAML content to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        logger.info("Validating skills.yaml")
        
        errors = []
        
        try:
            # Parse YAML
            data = yaml.safe_load(yaml_content)
            
            # Ensure schemas are loaded
            if 'skill' not in self.schemas:
                self.load_schemas()
            
            # Validate each skill
            skills = data.get('skills', [])
            for i, skill in enumerate(skills):
                try:
                    validate(instance=skill, schema=self.schemas['skill'])
                except JSONSchemaValidationError as e:
                    errors.append(f"Skill {i} validation error: {e.message}")
                    logger.error(f"Skill {i} validation failed: {e.message}")
            
            # Additional ADK-specific validations
            adk_errors = self._validate_skills_adk_requirements(data)
            errors.extend(adk_errors)
            
            if errors:
                logger.warning(f"skills.yaml validation found {len(errors)} errors")
                return False, errors
            
            logger.info("skills.yaml validation passed")
            return True, []
            
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def validate_config_json(self, json_content: str) -> Tuple[bool, List[str]]:
        """
        Validate config.json against config schema.
        
        Args:
            json_content: JSON content to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        logger.info("Validating config.json")
        
        errors = []
        
        try:
            # Parse JSON
            data = json.loads(json_content)
            
            # Ensure schemas are loaded
            if 'config' not in self.schemas:
                self.load_schemas()
            
            # Validate against schema
            try:
                validate(instance=data, schema=self.schemas['config'])
            except JSONSchemaValidationError as e:
                errors.append(f"Schema validation error: {e.message}")
                logger.error(f"config.json validation failed: {e.message}")
            
            # Additional validations
            config_errors = self._validate_config_requirements(data)
            errors.extend(config_errors)
            
            if errors:
                logger.warning(f"config.json validation found {len(errors)} errors")
                return False, errors
            
            logger.info("config.json validation passed")
            return True, []
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def validate_schema_json(self, json_content: str) -> Tuple[bool, List[str]]:
        """
        Validate schema.json against JSON Schema Draft 7.
        
        Args:
            json_content: JSON content to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        logger.info("Validating schema.json")
        
        errors = []
        
        try:
            # Parse JSON
            data = json.loads(json_content)
            
            # Validate as a JSON Schema
            try:
                Draft7Validator.check_schema(data)
            except Exception as e:
                errors.append(f"Invalid JSON Schema: {str(e)}")
                logger.error(f"schema.json validation failed: {str(e)}")
            
            # Check required fields
            if '$schema' not in data:
                errors.append("Missing required field: $schema")
            
            if 'type' not in data:
                errors.append("Missing required field: type")
            
            if errors:
                logger.warning(f"schema.json validation found {len(errors)} errors")
                return False, errors
            
            logger.info("schema.json validation passed")
            return True, []
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def validate_all(
        self,
        generated_files: Dict[str, str]
    ) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate all generated configuration files.
        
        Args:
            generated_files: Dictionary mapping filenames to content
            
        Returns:
            Tuple of (all_valid, dict of errors per file)
        """
        logger.info("Validating all configuration files")
        
        all_errors = {}
        all_valid = True
        
        # Validate agent.yaml
        if 'agent.yaml' in generated_files:
            is_valid, errors = self.validate_agent_yaml(generated_files['agent.yaml'])
            if not is_valid:
                all_valid = False
                all_errors['agent.yaml'] = errors
        
        # Validate skills.yaml
        if 'skills.yaml' in generated_files:
            is_valid, errors = self.validate_skills_yaml(generated_files['skills.yaml'])
            if not is_valid:
                all_valid = False
                all_errors['skills.yaml'] = errors
        
        # Validate config.json
        if 'config.json' in generated_files:
            is_valid, errors = self.validate_config_json(generated_files['config.json'])
            if not is_valid:
                all_valid = False
                all_errors['config.json'] = errors
        
        # Validate schema.json
        if 'schema.json' in generated_files:
            is_valid, errors = self.validate_schema_json(generated_files['schema.json'])
            if not is_valid:
                all_valid = False
                all_errors['schema.json'] = errors
        
        if all_valid:
            logger.info("All configuration files validated successfully")
        else:
            logger.warning(f"Validation failed for {len(all_errors)} files")
        
        return all_valid, all_errors
    
    def _validate_agent_adk_requirements(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate ADK-specific requirements for agent.yaml.
        
        Args:
            data: Parsed agent.yaml data
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Check required top-level fields
        required_fields = ['name', 'version', 'description', 'agent']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check agent section
        if 'agent' in data:
            agent = data['agent']
            
            # Check for nodes
            if 'nodes' not in agent or not agent['nodes']:
                errors.append("Agent must have at least one node")
            
            # Check for workflow
            if 'workflow' not in agent:
                errors.append("Agent must have workflow definition")
            else:
                workflow = agent['workflow']
                if 'entry_point' not in workflow:
                    errors.append("Workflow must have entry_point")
        
        return errors
    
    def _validate_skills_adk_requirements(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate ADK-specific requirements for skills.yaml.
        
        Args:
            data: Parsed skills.yaml data
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Check for skills array
        if 'skills' not in data:
            errors.append("Missing required field: skills")
            return errors
        
        skills = data['skills']
        if not isinstance(skills, list):
            errors.append("skills must be an array")
            return errors
        
        if not skills:
            errors.append("At least one skill must be defined")
        
        # Validate each skill
        for i, skill in enumerate(skills):
            if 'id' not in skill:
                errors.append(f"Skill {i}: Missing required field 'id'")
            if 'name' not in skill:
                errors.append(f"Skill {i}: Missing required field 'name'")
            if 'input_schema' not in skill:
                errors.append(f"Skill {i}: Missing required field 'input_schema'")
            if 'output_schema' not in skill:
                errors.append(f"Skill {i}: Missing required field 'output_schema'")
        
        return errors
    
    def _validate_config_requirements(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate requirements for config.json.
        
        Args:
            data: Parsed config.json data
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Check required sections
        required_sections = ['agent', 'runtime', 'nodes', 'edges', 'workflow']
        for section in required_sections:
            if section not in data:
                errors.append(f"Missing required section: {section}")
        
        # Validate nodes and edges consistency
        if 'nodes' in data and 'edges' in data:
            node_names = {node['name'] for node in data['nodes']}
            
            for edge in data['edges']:
                if edge['from'] not in node_names and edge['from'] != 'START':
                    errors.append(f"Edge references unknown node: {edge['from']}")
                if edge['to'] not in node_names and edge['to'] != 'END':
                    errors.append(f"Edge references unknown node: {edge['to']}")
        
        return errors
    
    def _get_default_agent_schema(self) -> Dict[str, Any]:
        """
        Get default agent schema if file not found.
        
        Returns:
            Default agent schema
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["name", "version", "description", "agent"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
                "agent": {
                    "type": "object",
                    "required": ["nodes", "workflow"],
                    "properties": {
                        "nodes": {"type": "array"},
                        "workflow": {"type": "object"}
                    }
                }
            }
        }
    
    def _get_default_skill_schema(self) -> Dict[str, Any]:
        """
        Get default skill schema if file not found.
        
        Returns:
            Default skill schema
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["id", "name", "input_schema", "output_schema"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"}
            }
        }
    
    def _get_default_config_schema(self) -> Dict[str, Any]:
        """
        Get default config schema.
        
        Returns:
            Default config schema
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["agent", "runtime", "nodes", "edges", "workflow"],
            "properties": {
                "agent": {"type": "object"},
                "runtime": {"type": "object"},
                "nodes": {"type": "array"},
                "edges": {"type": "array"},
                "workflow": {"type": "object"}
            }
        }


# Made with Bob