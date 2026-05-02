"""Custom exceptions for the OrchestrADK framework."""

from typing import Any, Dict, Optional


class OrchestradkError(Exception):
    """Base exception for all OrchestrADK errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ParseError(OrchestradkError):
    """Raised when Agent A fails to parse the natural language developer request."""
    pass


class GenerationError(OrchestradkError):
    """Raised when an agent fails to generate code or configuration."""
    pass


class ValidationError(OrchestradkError):
    """Raised when generated outputs fail ADK schema or syntax validation."""
    pass


class ADKIntegrationError(OrchestradkError):
    """Raised when packaging or integrating with the watsonx Orchestrate ADK fails."""
    pass


class LLMError(OrchestradkError):
    """Raised when LLM operations fail."""
    pass


class ConfigurationError(OrchestradkError):
    """Raised when configuration is invalid or missing."""
    pass


# Alias for backward compatibility
OrchestrADKError = OrchestradkError