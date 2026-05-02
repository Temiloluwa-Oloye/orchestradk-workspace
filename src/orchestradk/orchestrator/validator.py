"""
Validator module for the OrchestrADK orchestrator layer.

This module validates agent outputs, checks cross-agent consistency,
and ensures the complete package meets all requirements.
"""

import logging
import ast
import json
import yaml
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from ..utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ValidationResult(dict):
    """Result of a validation operation."""
    
    def __init__(
        self,
        valid: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            valid=valid,
            errors=errors or [],
            warnings=warnings or [],
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat()
        )
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}


class PackageValidator:
    """
    Validates complete agent packages for consistency and completeness.
    
    Responsibilities:
    - Validate scaffolder output (Python code syntax, structure)
    - Validate configurator output (YAML/JSON syntax, ADK compliance)
    - Check cross-agent consistency (references, naming, schemas)
    - Ensure complete package structure
    - Verify deployment readiness
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the package validator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.validation_history: List[Dict[str, Any]] = []
        
        logger.info("PackageValidator initialized")
    
    def validate_complete_package(
        self,
        package: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a complete agent package.
        
        Args:
            package: Complete package from coordinator
            
        Returns:
            ValidationResult with overall validation status
        """
        logger.info(f"Validating complete package: {package.get('agent_name', 'unknown')}")
        
        errors: List[str] = []
        warnings: List[str] = []
        
        try:
            # 1. Validate package structure
            structure_result = self._validate_package_structure(package)
            errors.extend(structure_result.errors)
            warnings.extend(structure_result.warnings)
            
            # 2. Validate Python files
            python_result = self._validate_python_files(package)
            errors.extend(python_result.errors)
            warnings.extend(python_result.warnings)
            
            # 3. Validate configuration files
            config_result = self._validate_config_files(package)
            errors.extend(config_result.errors)
            warnings.extend(config_result.warnings)
            
            # 4. Validate cross-agent consistency
            consistency_result = self._validate_cross_agent_consistency(package)
            errors.extend(consistency_result.errors)
            warnings.extend(consistency_result.warnings)
            
            # 5. Validate deployment readiness
            deployment_result = self._validate_deployment_readiness(package)
            errors.extend(deployment_result.errors)
            warnings.extend(deployment_result.warnings)
            
            # Determine overall validity
            is_valid = len(errors) == 0
            
            # Record validation
            self.validation_history.append({
                "package_name": package.get("agent_name", "unknown"),
                "valid": is_valid,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            result = ValidationResult(
                valid=is_valid,
                errors=errors,
                warnings=warnings,
                metadata={
                    "checks_performed": 5,
                    "package_name": package.get("agent_name", "unknown"),
                    "total_files": len(package.get("files", {}))
                }
            )
            
            if is_valid:
                logger.info("Package validation passed")
            else:
                logger.warning(f"Package validation failed with {len(errors)} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}", exc_info=True)
            return ValidationResult(
                valid=False,
                errors=[f"Validation exception: {str(e)}"],
                metadata={"error_type": type(e).__name__}
            )
    
    def _validate_package_structure(
        self,
        package: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate the overall package structure.
        
        Args:
            package: Package to validate
            
        Returns:
            ValidationResult for structure
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Check required top-level fields
        required_fields = ["agent_name", "description", "files", "structure"]
        for field in required_fields:
            if field not in package:
                errors.append(f"Missing required field: {field}")
        
        # Check agent name format
        agent_name = package.get("agent_name", "")
        if not agent_name:
            errors.append("Agent name is empty")
        elif not agent_name.replace("_", "").replace("-", "").isalnum():
            warnings.append(f"Agent name '{agent_name}' contains special characters")
        
        # Check files dictionary
        files = package.get("files", {})
        if not files:
            errors.append("No files in package")
        elif len(files) < 2:
            warnings.append("Package has very few files (expected Python + config files)")
        
        # Check structure
        structure = package.get("structure", {})
        if not structure:
            warnings.append("Package structure information missing")
        else:
            if "python" not in structure:
                errors.append("Python files structure missing")
            if "config" not in structure:
                errors.append("Config files structure missing")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_python_files(
        self,
        package: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate Python code files.
        
        Args:
            package: Package to validate
            
        Returns:
            ValidationResult for Python files
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        files = package.get("files", {})
        python_files = {k: v for k, v in files.items() if k.endswith(".py")}
        
        if not python_files:
            errors.append("No Python files found in package")
            return ValidationResult(valid=False, errors=errors)
        
        # Validate each Python file
        for filename, content in python_files.items():
            # Check syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"Syntax error in {filename}: {str(e)}")
            except Exception as e:
                errors.append(f"Failed to parse {filename}: {str(e)}")
            
            # Check for required imports
            if "state.py" in filename:
                if "TypedDict" not in content and "BaseModel" not in content:
                    warnings.append(f"{filename}: No state type definition found")
            
            if "nodes.py" in filename:
                if "def " not in content:
                    warnings.append(f"{filename}: No function definitions found")
            
            if "graph.py" in filename:
                if "StateGraph" not in content:
                    errors.append(f"{filename}: Missing StateGraph import/usage")
                if "compile()" not in content:
                    warnings.append(f"{filename}: Graph may not be compiled")
        
        # Check for expected files
        expected_files = ["state.py", "nodes.py", "graph.py"]
        found_files = [f for f in expected_files if any(f in pf for pf in python_files.keys())]
        
        if len(found_files) < len(expected_files):
            missing = set(expected_files) - set(found_files)
            warnings.append(f"Expected Python files not found: {', '.join(missing)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={"python_files_validated": len(python_files)}
        )
    
    def _validate_config_files(
        self,
        package: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate configuration files (YAML and JSON).
        
        Args:
            package: Package to validate
            
        Returns:
            ValidationResult for config files
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        files = package.get("files", {})
        
        # Validate YAML files
        yaml_files = {k: v for k, v in files.items() if k.endswith(".yaml") or k.endswith(".yml")}
        for filename, content in yaml_files.items():
            try:
                parsed = yaml.safe_load(content)
                if not parsed:
                    warnings.append(f"{filename}: Empty YAML file")
                
                # Check for required fields in agent.yaml
                if "agent.yaml" in filename:
                    if not isinstance(parsed, dict):
                        errors.append(f"{filename}: Invalid YAML structure")
                    else:
                        required = ["name", "version", "description"]
                        for field in required:
                            if field not in parsed:
                                errors.append(f"{filename}: Missing required field '{field}'")
                
                # Check for required fields in skills.yaml
                if "skills.yaml" in filename:
                    if not isinstance(parsed, dict):
                        errors.append(f"{filename}: Invalid YAML structure")
                    elif "skills" not in parsed:
                        errors.append(f"{filename}: Missing 'skills' section")
                
            except yaml.YAMLError as e:
                errors.append(f"YAML syntax error in {filename}: {str(e)}")
            except Exception as e:
                errors.append(f"Failed to parse {filename}: {str(e)}")
        
        # Validate JSON files
        json_files = {k: v for k, v in files.items() if k.endswith(".json")}
        for filename, content in json_files.items():
            try:
                parsed = json.loads(content)
                if not parsed:
                    warnings.append(f"{filename}: Empty JSON file")
                
                # Check for required fields in config.json
                if "config.json" in filename:
                    if not isinstance(parsed, dict):
                        errors.append(f"{filename}: Invalid JSON structure")
                
                # Check for required fields in schema.json
                if "schema.json" in filename:
                    if not isinstance(parsed, dict):
                        errors.append(f"{filename}: Invalid JSON structure")
                    elif "type" not in parsed:
                        warnings.append(f"{filename}: Missing 'type' field in schema")
                
            except json.JSONDecodeError as e:
                errors.append(f"JSON syntax error in {filename}: {str(e)}")
            except Exception as e:
                errors.append(f"Failed to parse {filename}: {str(e)}")
        
        # Check for expected config files
        if not yaml_files:
            errors.append("No YAML configuration files found")
        if not json_files:
            warnings.append("No JSON configuration files found")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "yaml_files_validated": len(yaml_files),
                "json_files_validated": len(json_files)
            }
        )
    
    def _validate_cross_agent_consistency(
        self,
        package: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate consistency between scaffolder and configurator outputs.
        
        Args:
            package: Package to validate
            
        Returns:
            ValidationResult for cross-agent consistency
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        try:
            # Extract agent name from different sources
            package_name = package.get("agent_name", "")
            
            files = package.get("files", {})
            
            # Parse agent.yaml to get name
            agent_yaml_content = None
            for filename, content in files.items():
                if "agent.yaml" in filename:
                    agent_yaml_content = content
                    break
            
            if agent_yaml_content:
                try:
                    agent_yaml = yaml.safe_load(agent_yaml_content)
                    yaml_name = agent_yaml.get("name", "")
                    
                    # Check name consistency
                    if yaml_name and yaml_name != package_name:
                        errors.append(
                            f"Agent name mismatch: package='{package_name}', "
                            f"agent.yaml='{yaml_name}'"
                        )
                except Exception as e:
                    warnings.append(f"Could not parse agent.yaml for consistency check: {str(e)}")
            
            # Check that Python files reference matches config
            structure = package.get("structure", {})
            python_structure = structure.get("python", {})
            config_structure = structure.get("config", {})
            
            python_files = set(python_structure.get("files", []))
            config_files = set(config_structure.get("files", []))
            
            # Verify all files are accounted for
            all_files = set(files.keys())
            expected_files = python_files | config_files
            
            missing_in_structure = all_files - expected_files
            if missing_in_structure:
                warnings.append(
                    f"Files not listed in structure: {', '.join(missing_in_structure)}"
                )
            
            # Check validation flags consistency
            validation = package.get("validation", {})
            scaffolder_valid = validation.get("scaffolder", False)
            configurator_valid = validation.get("configurator", False)
            
            if not scaffolder_valid:
                errors.append("Scaffolder validation flag indicates failure")
            if not configurator_valid:
                errors.append("Configurator validation flag indicates failure")
            
        except Exception as e:
            warnings.append(f"Error during consistency check: {str(e)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_deployment_readiness(
        self,
        package: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate that the package is ready for deployment.
        
        Args:
            package: Package to validate
            
        Returns:
            ValidationResult for deployment readiness
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Check deployment metadata
        deployment = package.get("deployment", {})
        
        if not deployment:
            warnings.append("No deployment metadata found")
        else:
            if not deployment.get("ready", False):
                errors.append("Package marked as not ready for deployment")
            
            platform = deployment.get("platform", "")
            if platform != "watsonx Orchestrate":
                warnings.append(f"Unexpected deployment platform: {platform}")
            
            if not deployment.get("adk_compliant", False):
                errors.append("Package not marked as ADK compliant")
        
        # Check for required files
        files = package.get("files", {})
        
        # Must have at least one Python file
        has_python = any(f.endswith(".py") for f in files.keys())
        if not has_python:
            errors.append("No Python files for deployment")
        
        # Must have agent.yaml
        has_agent_yaml = any("agent.yaml" in f for f in files.keys())
        if not has_agent_yaml:
            errors.append("Missing required agent.yaml file")
        
        # Should have skills.yaml
        has_skills_yaml = any("skills.yaml" in f for f in files.keys())
        if not has_skills_yaml:
            warnings.append("Missing skills.yaml file")
        
        # Check metadata completeness
        metadata = package.get("metadata", {})
        if not metadata:
            warnings.append("Package metadata is empty")
        else:
            if metadata.get("total_files", 0) != len(files):
                warnings.append("File count mismatch in metadata")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all validations performed.
        
        Returns:
            Dictionary with validation summary
        """
        if not self.validation_history:
            return {
                "total_validations": 0,
                "successful": 0,
                "failed": 0
            }
        
        total = len(self.validation_history)
        successful = sum(1 for v in self.validation_history if v["valid"])
        failed = total - successful
        
        return {
            "total_validations": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "recent_validations": self.validation_history[-5:]
        }
    
    def __repr__(self) -> str:
        """String representation of validator."""
        return f"PackageValidator(validations={len(self.validation_history)})"


# Made with Bob