"""
Router module for the OrchestrADK orchestrator layer.

This module handles task routing, manages execution flow, and determines
which agent should handle specific tasks based on the workflow stage.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
from datetime import datetime

from ..agents.base_agent import AgentMessage, AgentResponse
from ..utils.exceptions import OrchestradkError

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Stages in the OrchestrADK workflow."""
    INITIAL = "initial"
    SCAFFOLDING = "scaffolding"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    COMPLETE = "complete"
    ERROR = "error"


class TaskType(Enum):
    """Types of tasks that can be routed."""
    PARSE_REQUEST = "parse_request"
    GENERATE_CODE = "generate_code"
    GENERATE_CONFIG = "generate_config"
    VALIDATE_OUTPUT = "validate_output"
    PACKAGE_AGENT = "package_agent"


class RoutingDecision(dict):
    """Result of a routing decision."""
    
    def __init__(
        self,
        target_agent: str,
        task_type: TaskType,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            target_agent=target_agent,
            task_type=task_type.value,
            priority=priority,
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat()
        )
        self.target_agent = target_agent
        self.task_type = task_type
        self.priority = priority
        self.metadata = metadata or {}


class TaskRouter:
    """
    Routes tasks to appropriate agents based on workflow stage and task type.
    
    Responsibilities:
    - Determine which agent should handle a task
    - Manage task dependencies and execution order
    - Track workflow progression through stages
    - Handle conditional routing based on intermediate results
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the task router.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.current_stage = WorkflowStage.INITIAL
        self.stage_history: List[Dict[str, Any]] = []
        self.routing_rules: Dict[TaskType, str] = self._initialize_routing_rules()
        
        logger.info("TaskRouter initialized")
    
    def _initialize_routing_rules(self) -> Dict[TaskType, str]:
        """
        Initialize the routing rules mapping tasks to agents.
        
        Returns:
            Dictionary mapping task types to agent IDs
        """
        return {
            TaskType.PARSE_REQUEST: "scaffolder",
            TaskType.GENERATE_CODE: "scaffolder",
            TaskType.GENERATE_CONFIG: "configurator",
            TaskType.VALIDATE_OUTPUT: "validator",
            TaskType.PACKAGE_AGENT: "configurator"
        }
    
    def route_task(
        self,
        task_type: TaskType,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a task to the appropriate agent.
        
        Args:
            task_type: Type of task to route
            context: Optional context information for routing decision
            
        Returns:
            RoutingDecision with target agent and metadata
        """
        logger.info(f"Routing task: {task_type.value}")
        
        # Get target agent from routing rules
        target_agent = self.routing_rules.get(task_type)
        
        if not target_agent:
            logger.error(f"No routing rule found for task type: {task_type.value}")
            raise OrchestradkError(f"Unknown task type: {task_type.value}")
        
        # Determine priority based on task type and context
        priority = self._calculate_priority(task_type, context)
        
        # Create routing decision
        decision = RoutingDecision(
            target_agent=target_agent,
            task_type=task_type,
            priority=priority,
            metadata={
                "current_stage": self.current_stage.value,
                "context": context or {}
            }
        )
        
        logger.info(f"Task routed to: {target_agent} (priority: {priority})")
        
        return decision
    
    def _calculate_priority(
        self,
        task_type: TaskType,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate task priority based on type and context.
        
        Args:
            task_type: Type of task
            context: Optional context information
            
        Returns:
            Priority value (higher = more urgent)
        """
        # Base priorities
        base_priorities = {
            TaskType.PARSE_REQUEST: 100,
            TaskType.GENERATE_CODE: 90,
            TaskType.GENERATE_CONFIG: 80,
            TaskType.VALIDATE_OUTPUT: 70,
            TaskType.PACKAGE_AGENT: 60
        }
        
        priority = base_priorities.get(task_type, 50)
        
        # Adjust based on context
        if context:
            # Increase priority for retry attempts
            if context.get("retry_count", 0) > 0:
                priority += 10
            
            # Increase priority for critical tasks
            if context.get("critical", False):
                priority += 20
        
        return priority
    
    def determine_next_stage(
        self,
        current_result: Dict[str, Any]
    ) -> WorkflowStage:
        """
        Determine the next workflow stage based on current results.
        
        Args:
            current_result: Results from current stage
            
        Returns:
            Next workflow stage
        """
        current_stage = self.current_stage
        
        # Stage transition logic
        if current_stage == WorkflowStage.INITIAL:
            next_stage = WorkflowStage.SCAFFOLDING
        
        elif current_stage == WorkflowStage.SCAFFOLDING:
            # Check if scaffolding was successful
            if current_result.get("success", False):
                next_stage = WorkflowStage.CONFIGURATION
            else:
                next_stage = WorkflowStage.ERROR
        
        elif current_stage == WorkflowStage.CONFIGURATION:
            # Check if configuration was successful
            if current_result.get("success", False):
                next_stage = WorkflowStage.VALIDATION
            else:
                next_stage = WorkflowStage.ERROR
        
        elif current_stage == WorkflowStage.VALIDATION:
            # Check if validation passed
            if current_result.get("success", False):
                next_stage = WorkflowStage.COMPLETE
            else:
                next_stage = WorkflowStage.ERROR
        
        elif current_stage == WorkflowStage.COMPLETE:
            next_stage = WorkflowStage.COMPLETE
        
        else:  # ERROR or unknown
            next_stage = WorkflowStage.ERROR
        
        logger.info(f"Stage transition: {current_stage.value} → {next_stage.value}")
        
        return next_stage
    
    def advance_stage(
        self,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowStage:
        """
        Advance to the next workflow stage.
        
        Args:
            result: Results from current stage
            metadata: Optional metadata about the stage completion
            
        Returns:
            New workflow stage
        """
        # Record current stage in history
        self.stage_history.append({
            "stage": self.current_stage.value,
            "result": result,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Determine and set next stage
        next_stage = self.determine_next_stage(result)
        self.current_stage = next_stage
        
        logger.info(f"Advanced to stage: {next_stage.value}")
        
        return next_stage
    
    def get_execution_plan(
        self,
        start_stage: Optional[WorkflowStage] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the execution plan for the workflow.
        
        Args:
            start_stage: Optional starting stage (defaults to current)
            
        Returns:
            List of planned execution steps
        """
        stage = start_stage or self.current_stage
        
        # Define the standard execution plan
        plan = []
        
        if stage == WorkflowStage.INITIAL or stage == WorkflowStage.SCAFFOLDING:
            plan.append({
                "stage": WorkflowStage.SCAFFOLDING.value,
                "agent": "scaffolder",
                "tasks": [
                    TaskType.PARSE_REQUEST.value,
                    TaskType.GENERATE_CODE.value
                ],
                "description": "Parse request and generate LangGraph code"
            })
        
        if stage in [WorkflowStage.INITIAL, WorkflowStage.SCAFFOLDING, WorkflowStage.CONFIGURATION]:
            plan.append({
                "stage": WorkflowStage.CONFIGURATION.value,
                "agent": "configurator",
                "tasks": [
                    TaskType.GENERATE_CONFIG.value,
                    TaskType.PACKAGE_AGENT.value
                ],
                "description": "Generate ADK configuration files"
            })
        
        if stage in [WorkflowStage.INITIAL, WorkflowStage.SCAFFOLDING, 
                     WorkflowStage.CONFIGURATION, WorkflowStage.VALIDATION]:
            plan.append({
                "stage": WorkflowStage.VALIDATION.value,
                "agent": "validator",
                "tasks": [TaskType.VALIDATE_OUTPUT.value],
                "description": "Validate complete package"
            })
        
        return plan
    
    def can_proceed_to_stage(
        self,
        target_stage: WorkflowStage,
        current_results: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Check if workflow can proceed to target stage.
        
        Args:
            target_stage: Target stage to check
            current_results: Current results to validate
            
        Returns:
            Tuple of (can_proceed, reason_if_not)
        """
        current = self.current_stage
        
        # Can't go backwards (except to ERROR)
        if target_stage != WorkflowStage.ERROR:
            stage_order = [
                WorkflowStage.INITIAL,
                WorkflowStage.SCAFFOLDING,
                WorkflowStage.CONFIGURATION,
                WorkflowStage.VALIDATION,
                WorkflowStage.COMPLETE
            ]
            
            try:
                current_idx = stage_order.index(current)
                target_idx = stage_order.index(target_stage)
                
                if target_idx < current_idx:
                    return False, f"Cannot go backwards from {current.value} to {target_stage.value}"
            except ValueError:
                pass
        
        # Check if current stage completed successfully
        if not current_results.get("success", False) and target_stage != WorkflowStage.ERROR:
            return False, f"Current stage {current.value} did not complete successfully"
        
        # Stage-specific checks
        if target_stage == WorkflowStage.CONFIGURATION:
            if not current_results.get("data", {}).get("files"):
                return False, "No code files generated in scaffolding stage"
        
        elif target_stage == WorkflowStage.VALIDATION:
            if not current_results.get("data", {}).get("files"):
                return False, "No configuration files generated"
        
        return True, None
    
    def reset(self) -> None:
        """Reset the router to initial state."""
        logger.info("Resetting router to initial state")
        self.current_stage = WorkflowStage.INITIAL
        self.stage_history.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current router status.
        
        Returns:
            Dictionary with router status information
        """
        return {
            "current_stage": self.current_stage.value,
            "stages_completed": len(self.stage_history),
            "routing_rules": {
                task.value: agent
                for task, agent in self.routing_rules.items()
            },
            "stage_history": self.stage_history[-5:]  # Last 5 stages
        }
    
    def __repr__(self) -> str:
        """String representation of router."""
        return (
            f"TaskRouter(stage={self.current_stage.value}, "
            f"history={len(self.stage_history)})"
        )


# Made with Bob