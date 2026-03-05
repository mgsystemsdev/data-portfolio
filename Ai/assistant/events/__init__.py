"""Event system: append-only store and projections."""
from .event_store import append_event, get_all_events
from .projector import project_event

__all__ = ["append_event", "get_all_events", "project_event"]
