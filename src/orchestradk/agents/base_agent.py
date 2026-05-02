"""
Base agent interface for OrchestrADK.

This module defines the abstract base class that all agents must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentMessage(BaseModel):
    """Standard message format for inter-agent communication."""
    
    sender: str = Field(..., description="Agent identifier")
    receiver: str = Field(..., description="Target agent")
    message_type: str = Field(..., description="Message type: request, response, or error")
    payload: Dict[str, Any] = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "sender": "scaffolder",
                "receiver": "configurator",
                "message_type": "response",
                "payload": {"code": "...", "nodes": ["node1", "node2"]},
                "metadata": {"duration": 2.5},
                "timestamp": "2026-05-02T17:30:00.000Z"
            }
        }


class AgentResponse(BaseModel):
    """Standard response format from agents."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"generated_code": "...", "nodes": 3},
                "error": None,
                "metadata": {"execution_time": 2.5}
            }
        }


class BaseAgent(ABC):
    """
    Abstract base class for all OrchestrADK agents.
    
    All agents must implement the process() method and provide
    a unique agent_id.
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentResponse:
        """
        Process an incoming message and return a response.
        
        Args:
            message: The incoming agent message
            
        Returns:
            AgentResponse with the processing result
            
        Raises:
            OrchestrADKError: If processing fails
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the agent (load models, connect to services, etc.).
        
        This method is called once before the agent starts processing messages.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleanup resources when the agent is shutting down.
        
        This method is called when the agent is no longer needed.
        """
        pass
    
    async def validate_input(self, message: AgentMessage) -> bool:
        """
        Validate incoming message format and content.
        
        Args:
            message: The message to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not message.sender or not message.receiver:
            return False
        if message.message_type not in ["request", "response", "error"]:
            return False
        if not message.payload:
            return False
        return True
    
    def create_response(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Create a standardized agent response.
        
        Args:
            success: Whether the operation succeeded
            data: Response data
            error: Error message if failed
            metadata: Additional metadata
            
        Returns:
            AgentResponse object
        """
        return AgentResponse(
            success=success,
            data=data,
            error=error,
            metadata=metadata
        )
    
    def create_message(
        self,
        receiver: str,
        message_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """
        Create a standardized agent message.
        
        Args:
            receiver: Target agent identifier
            message_type: Type of message (request, response, error)
            payload: Message content
            metadata: Additional metadata
            
        Returns:
            AgentMessage object
        """
        return AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            payload=payload,
            metadata=metadata
        )

# Made with Bob
