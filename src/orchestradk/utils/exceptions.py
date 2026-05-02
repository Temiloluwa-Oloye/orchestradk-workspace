"""Custom exceptions for the OrchestrADK framework."""

class OrchestradkError(Exception):
    """Base exception for all OrchestrADK errors."""
    pass

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