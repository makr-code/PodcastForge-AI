"""Unit tests for podcastforge.core.events (EventBus)."""
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.core.events import EventBus, get_event_bus


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe("test.event", lambda d: received.append(d))
        bus.publish("test.event", {"value": 42})
        assert received == [{"value": 42}]

    def test_multiple_subscribers(self):
        bus = EventBus()
        a, b = [], []
        bus.subscribe("ev", lambda d: a.append(d))
        bus.subscribe("ev", lambda d: b.append(d))
        bus.publish("ev", 1)
        assert a == [1]
        assert b == [1]

    def test_unsubscribe_stops_delivery(self):
        bus = EventBus()
        received = []
        cb = lambda d: received.append(d)
        bus.subscribe("ev", cb)
        bus.publish("ev", "first")
        bus.unsubscribe("ev", cb)
        bus.publish("ev", "second")
        assert received == ["first"]

    def test_unsubscribe_nonexistent_is_harmless(self):
        bus = EventBus()
        bus.unsubscribe("no_such_event", lambda d: None)  # must not raise

    def test_duplicate_subscribe_ignored(self):
        bus = EventBus()
        received = []
        cb = lambda d: received.append(d)
        bus.subscribe("ev", cb)
        bus.subscribe("ev", cb)  # duplicate
        bus.publish("ev", 1)
        assert received == [1]  # only one delivery

    def test_no_subscribers_no_error(self):
        bus = EventBus()
        bus.publish("unknown.event", "data")  # must not raise

    def test_crashing_subscriber_does_not_stop_others(self):
        bus = EventBus()
        good = []

        def bad_cb(d):
            raise RuntimeError("intentional crash")

        bus.subscribe("ev", bad_cb)
        bus.subscribe("ev", lambda d: good.append(d))
        bus.publish("ev", "ping")
        assert good == ["ping"]

    def test_publish_without_data(self):
        bus = EventBus()
        received = []
        bus.subscribe("ev", lambda d: received.append(d))
        bus.publish("ev")
        assert received == [None]

    def test_thread_safe_concurrent_publish(self):
        bus = EventBus()
        received = []
        lock = threading.Lock()

        def cb(d):
            with lock:
                received.append(d)

        bus.subscribe("ev", cb)

        threads = [threading.Thread(target=bus.publish, args=("ev", i)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(received) == 20

    def test_get_event_bus_returns_singleton(self):
        b1 = get_event_bus()
        b2 = get_event_bus()
        assert b1 is b2
