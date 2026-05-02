"""
Coordinator module for the OrchestrADK orchestrator layer.

This module manages the lifecycle of agents and handles inter-agent communication,
coordinating the sequential execution of Agent A (Scaffolder) and Agent B (Configurator).
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from ..agents.base_agent import BaseAgent, AgentMessage, AgentResponse
from ..agents.scaffolder.agent import ScaffolderAgent
from ..agents.configurator.agent import ConfiguratorAgent
from ..utils.exceptions import OrchestradkError

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent in the coordinator."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class CoordinationResult(dict):
    """Result of a coordination operation."""
    
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            success=success,
            data=data or {},
            error=error,
            metadata=metadata or {}
        )
        self.success = success
        self.data = data or {}
        self.error = error
        self.metadata = metadata or {}


class AgentCoordinator:
    """
    Coordinates the lifecycle and communication between agents.
    
    Responsibilities:
    - Initialize and manage agent instances
    - Handle inter-agent message passing
    - Coordinate sequential execution (Scaffolder → Configurator)
    - Track agent status and health
    - Manage graceful shutdown
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent coordinator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_status: Dict[str, AgentStatus] = {}
        self.message_history: List[AgentMessage] = []
        self._initialized = False
        
        logger.info("AgentCoordinator initialized")
    
    async def initialize(
        self,
        scaffolder: ScaffolderAgent,
        configurator: ConfiguratorAgent
    ) -> None:
        """
        Initialize the coordinator with agent instances.
        
        Args:
            scaffolder: The scaffolder agent instance
            configurator: The configurator agent instance
            
        Raises:
            OrchestradkError: If initialization fails
        """
        if self._initialized:
            logger.warning("Coordinator already initialized")
            return
        
        logger.info("Initializing coordinator with agents...")
        
        try:
            # Register agents
            self.agents["scaffolder"] = scaffolder
            self.agents["configurator"] = configurator
            
            # Initialize agent status
            self.agent_status["scaffolder"] = AgentStatus.INITIALIZING
            self.agent_status["configurator"] = AgentStatus.INITIALIZING
            
            # Initialize scaffolder
            logger.info("Initializing scaffolder agent...")
            await scaffolder.initialize()
            self.agent_status["scaffolder"] = AgentStatus.READY
            logger.info("Scaffolder agent ready")
            
            # Initialize configurator
            logger.info("Initializing configurator agent...")
            await configurator.initialize()
            self.agent_status["configurator"] = AgentStatus.READY
            logger.info("Configurator agent ready")
            
            self._initialized = True
            logger.info("Coordinator initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize coordinator: {str(e)}", exc_info=True)
            # Mark agents as error state
            for agent_id in self.agents.keys():
                self.agent_status[agent_id] = AgentStatus.ERROR
            raise OrchestradkError(f"Coordinator initialization failed: {str(e)}")
    
    async def coordinate_workflow(
        self,
        user_request: str,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> CoordinationResult:
        """
        Coordinate the complete workflow from user request to final output.
        
        This orchestrates the sequential execution:
        1. User Request → Scaffolder (Agent A)
        2. Scaffolder Output → Configurator (Agent B)
        3. Configurator Output → Complete Package
        
        Args:
            user_request: Natural language developer request
            additional_config: Optional additional configuration
            
        Returns:
            CoordinationResult with complete package or error
        """
        if not self._initialized:
            return CoordinationResult(
                success=False,
                error="Coordinator not initialized. Call initialize() first."
            )
        
        logger.info("Starting coordinated workflow")
        start_time = datetime.utcnow()
        workflow_metadata = {
            "start_time": start_time.isoformat(),
            "stages": []
        }
        
        try:
            # Stage 1: Execute Scaffolder
            logger.info("Stage 1: Executing scaffolder agent")
            scaffolder_result = await self._execute_scaffolder(user_request)
            
            workflow_metadata["stages"].append({
                "stage": "scaffolder",
                "success": scaffolder_result.success,
                "duration": (scaffolder_result.metadata or {}).get("execution_time", 0)
            })
            
            if not scaffolder_result.success:
                logger.error(f"Scaffolder failed: {scaffolder_result.error}")
                return CoordinationResult(
                    success=False,
                    error=f"Scaffolder stage failed: {scaffolder_result.error}",
                    metadata=workflow_metadata
                )
            
            logger.info("Scaffolder stage completed successfully")
            
            # Stage 2: Execute Configurator
            logger.info("Stage 2: Executing configurator agent")
            
            # Ensure scaffolder data is not None
            if not scaffolder_result.data:
                return CoordinationResult(
                    success=False,
                    error="Scaffolder returned no data",
                    metadata=workflow_metadata
                )
            
            configurator_result = await self._execute_configurator(
                scaffolder_result.data,
                additional_config
            )
            
            workflow_metadata["stages"].append({
                "stage": "configurator",
                "success": configurator_result.success,
                "duration": (configurator_result.metadata or {}).get("execution_time", 0)
            })
            
            if not configurator_result.success:
                logger.error(f"Configurator failed: {configurator_result.error}")
                return CoordinationResult(
                    success=False,
                    error=f"Configurator stage failed: {configurator_result.error}",
                    metadata=workflow_metadata
                )
            
            logger.info("Configurator stage completed successfully")
            
            # Stage 3: Combine outputs into complete package
            logger.info("Stage 3: Assembling complete package")
            
            # Ensure configurator data is not None
            if not configurator_result.data:
                return CoordinationResult(
                    success=False,
                    error="Configurator returned no data",
                    metadata=workflow_metadata
                )
            
            complete_package = self._assemble_complete_package(
                scaffolder_result.data,
                configurator_result.data
            )
            
            # Calculate total execution time
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            
            workflow_metadata.update({
                "end_time": end_time.isoformat(),
                "total_duration": total_duration,
                "success": True
            })
            
            logger.info(f"Workflow completed successfully in {total_duration:.2f}s")
            
            return CoordinationResult(
                success=True,
                data=complete_package,
                metadata=workflow_metadata
            )
            
        except Exception as e:
            logger.error(f"Workflow coordination failed: {str(e)}", exc_info=True)
            
            end_time = datetime.utcnow()
            workflow_metadata.update({
                "end_time": end_time.isoformat(),
                "total_duration": (end_time - start_time).total_seconds(),
                "success": False,
                "error_type": type(e).__name__
            })
            
            return CoordinationResult(
                success=False,
                error=f"Workflow failed: {str(e)}",
                metadata=workflow_metadata
            )
    
    async def _execute_scaffolder(self, user_request: str) -> AgentResponse:
        """
        Execute the scaffolder agent.
        
        Args:
            user_request: Natural language developer request
            
        Returns:
            AgentResponse from scaffolder
        """
        scaffolder = self.agents["scaffolder"]
        self.agent_status["scaffolder"] = AgentStatus.PROCESSING
        
        try:
            # Create message for scaffolder
            message = AgentMessage(
                sender="coordinator",
                receiver="scaffolder",
                message_type="request",
                payload={"request": user_request},
                metadata={"workflow_stage": "scaffolder"}
            )
            
            # Store message in history
            self.message_history.append(message)
            
            # Process request
            response = await scaffolder.process(message)
            
            # Update status
            self.agent_status["scaffolder"] = AgentStatus.READY
            
            return response
            
        except Exception as e:
            self.agent_status["scaffolder"] = AgentStatus.ERROR
            logger.error(f"Scaffolder execution failed: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Scaffolder execution error: {str(e)}"
            )
    
    async def _execute_configurator(
        self,
        scaffolder_output: Dict[str, Any],
        additional_config: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute the configurator agent.
        
        Args:
            scaffolder_output: Output from scaffolder agent
            additional_config: Optional additional configuration
            
        Returns:
            AgentResponse from configurator
        """
        configurator = self.agents["configurator"]
        self.agent_status["configurator"] = AgentStatus.PROCESSING
        
        try:
            # Create message for configurator
            message = AgentMessage(
                sender="coordinator",
                receiver="configurator",
                message_type="request",
                payload={
                    "scaffolder_output": scaffolder_output,
                    "additional_config": additional_config or {}
                },
                metadata={"workflow_stage": "configurator"}
            )
            
            # Store message in history
            self.message_history.append(message)
            
            # Process request
            response = await configurator.process(message)
            
            # Update status
            self.agent_status["configurator"] = AgentStatus.READY
            
            return response
            
        except Exception as e:
            self.agent_status["configurator"] = AgentStatus.ERROR
            logger.error(f"Configurator execution failed: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Configurator execution error: {str(e)}"
            )
    
    def _assemble_complete_package(
        self,
        scaffolder_output: Dict[str, Any],
        configurator_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assemble the complete ADK package from both agent outputs.
        
        Args:
            scaffolder_output: Output from scaffolder
            configurator_output: Output from configurator
            
        Returns:
            Complete package dictionary
        """
        agent_name = scaffolder_output.get("agent_name", "unnamed_agent")
        
        # Combine all files
        python_files = scaffolder_output.get("files", {})
        config_files = configurator_output.get("files", {})
        all_files = {**python_files, **config_files}
        
        # Create complete package
        complete_package = {
            "agent_name": agent_name,
            "description": scaffolder_output.get("description", "Generated agent"),
            "version": "1.0.0",
            "files": all_files,
            "structure": {
                "python": {
                    "files": list(python_files.keys()),
                    "metadata": scaffolder_output.get("metadata", {})
                },
                "config": {
                    "files": list(config_files.keys()),
                    "metadata": configurator_output.get("metadata", {})
                }
            },
            "validation": {
                "scaffolder": scaffolder_output.get("metadata", {}).get("validation_passed", False),
                "configurator": configurator_output.get("validation", {}).get("all_valid", False)
            },
            "deployment": {
                "ready": True,
                "platform": "watsonx Orchestrate",
                "adk_compliant": True
            },
            "metadata": {
                "total_files": len(all_files),
                "python_files": len(python_files),
                "config_files": len(config_files),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        return complete_package
    
    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the status of agents.
        
        Args:
            agent_id: Optional specific agent ID, or None for all agents
            
        Returns:
            Dictionary with agent status information
        """
        if agent_id:
            if agent_id not in self.agents:
                return {"error": f"Agent '{agent_id}' not found"}
            
            return {
                "agent_id": agent_id,
                "status": self.agent_status.get(agent_id, AgentStatus.UNINITIALIZED).value,
                "initialized": agent_id in self.agents
            }
        
        # Return status for all agents
        return {
            "coordinator_initialized": self._initialized,
            "agents": {
                agent_id: {
                    "status": status.value,
                    "initialized": True
                }
                for agent_id, status in self.agent_status.items()
            },
            "total_agents": len(self.agents),
            "message_history_count": len(self.message_history)
        }
    
    def get_message_history(
        self,
        limit: Optional[int] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the message history.
        
        Args:
            limit: Optional limit on number of messages to return
            agent_id: Optional filter by sender or receiver
            
        Returns:
            List of message dictionaries
        """
        messages = self.message_history
        
        # Filter by agent if specified
        if agent_id:
            messages = [
                msg for msg in messages
                if msg.sender == agent_id or msg.receiver == agent_id
            ]
        
        # Apply limit if specified
        if limit:
            messages = messages[-limit:]
        
        # Convert to dictionaries
        return [msg.model_dump() for msg in messages]
    
    async def cleanup(self) -> None:
        """
        Cleanup all agents and coordinator resources.
        
        This should be called when shutting down the system.
        """
        logger.info("Cleaning up coordinator and agents...")
        
        # Cleanup each agent
        for agent_id, agent in self.agents.items():
            try:
                logger.info(f"Cleaning up {agent_id} agent")
                await agent.cleanup()
                self.agent_status[agent_id] = AgentStatus.SHUTDOWN
            except Exception as e:
                logger.error(f"Error cleaning up {agent_id}: {str(e)}")
        
        # Clear state
        self.agents.clear()
        self.agent_status.clear()
        self.message_history.clear()
        self._initialized = False
        
        logger.info("Coordinator cleanup complete")
    
    def __repr__(self) -> str:
        """String representation of coordinator."""
        return (
            f"AgentCoordinator(initialized={self._initialized}, "
            f"agents={list(self.agents.keys())}, "
            f"messages={len(self.message_history)})"
        )


# Made with Bob