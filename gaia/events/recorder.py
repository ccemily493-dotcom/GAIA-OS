"""Direct event recorder for GAIA OS v0.1.

Records append-only events directly to the EventRepository without pub/sub overhead,
while preserving causation and correlation linkages.
"""

from typing import Any

from gaia.domain.events import Actor, Event, EventType
from gaia.storage.protocols import EventRepository


class EventRecorder:
    """Direct, causality-aware event recorder writing to an EventRepository."""

    def __init__(self, repository: EventRepository) -> None:
        self._repo = repository

    async def record(
        self,
        event_type: EventType | str,
        correlation_id: str,
        actor: Actor | str = Actor.SYSTEM,
        payload: dict[str, Any] | None = None,
        causation_id: str | None = None,
    ) -> Event:
        """Appends an event to the persistent event log.

        Args:
            event_type: The canonical event type or descriptive string.
            correlation_id: UUID grouping the interaction transaction.
            actor: Identity of the actor triggering the event.
            payload: Event data dictionary.
            causation_id: Optional UUID of the immediate causal predecessor.

        Returns:
            The persisted Event with generated UUID and timestamp.
        """
        event = Event(
            event_type=event_type,
            correlation_id=correlation_id,
            causation_id=causation_id,
            actor=actor,
            payload=payload or {},
        )
        return await self._repo.append_event(event)

    async def get_events(self, correlation_id: str | None = None, limit: int = 100) -> list[Event]:
        """Retrieves events from the event log."""
        return await self._repo.get_events(correlation_id=correlation_id, limit=limit)
