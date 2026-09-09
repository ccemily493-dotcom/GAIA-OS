"""Domain-specific exception hierarchy for GAIA OS."""


class GaiaError(Exception):
    """Base exception for all GAIA errors."""

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(GaiaError):
    """Raised when an entity is not found in the persistence store."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} with ID '{entity_id}' not found.",
            {"entity_type": entity_type, "entity_id": entity_id},
        )


class ValidationError(GaiaError):
    """Raised when data fails domain or input validation."""


class ToolExecutionError(GaiaError):
    """Raised when a tool encounters an error during execution."""

    def __init__(self, tool_name: str, message: str) -> None:
        super().__init__(
            f"Tool '{tool_name}' failed: {message}",
            {"tool_name": tool_name, "error": message},
        )


class ModelProviderError(GaiaError):
    """Raised when an external or local model provider fails."""
