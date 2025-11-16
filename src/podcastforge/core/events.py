from typing import Any, Callable, Dict, List
import threading


class EventBus:
    """Lightweight publish/subscribe EventBus for in‑process events.

    - subscribe(event_name, callback)
    - unsubscribe(event_name, callback)
    - publish(event_name, data)

    Thread-safe.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_name: str, callback: Callable[[Any], None]):
        with self._lock:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            if callback not in self._listeners[event_name]:
                self._listeners[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Any], None]):
        with self._lock:
            if event_name in self._listeners and callback in self._listeners[event_name]:
                self._listeners[event_name].remove(callback)

    def publish(self, event_name: str, data: Any = None):
        with self._lock:
            listeners = list(self._listeners.get(event_name, []))

        for cb in listeners:
            try:
                cb(data)
            except Exception:
                # Do not let a subscriber crash the publisher
                pass


# Module‑level default bus
_default_bus: EventBus = EventBus()


def get_event_bus() -> EventBus:
    return _default_bus
