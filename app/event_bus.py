"""Event Bus Module for pub/sub communication."""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict


@dataclass
class Event:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    priority: int = 0


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history: int = 1000
        self._lock = threading.RLock()
        
    def subscribe(self, event_type: str, callback: Callable, async_callback: bool = False):
        with self._lock:
            self._subscribers[event_type].append(callback)
        
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    return True
                except ValueError:
                    pass
        return False
    
    def publish(self, event_type: str, data: Dict[str, Any] = None, 
                source: Optional[str] = None, priority: int = 0) -> Event:
        if data is None:
            data = {}
        
        event = Event(
            type=event_type,
            data=data,
            source=source,
            priority=priority
        )
        
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        self._notify_subscribers(event_type, event)
        return event
    
    def _notify_subscribers(self, event_type: str, event: Event):
        with self._lock:
            for callback in self._subscribers.get(event_type, []):
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in callback for {event_type}: {e}")
    
    def get_recent_events(self, limit: int = 100) -> List[Event]:
        with self._lock:
            return list(self._event_history[-limit:])
    
    def clear_history(self):
        with self._lock:
            self._event_history.clear()


event_bus = EventBus()


def get_event_bus():
    return event_bus


def publish(event_type: str, data: Dict[str, Any] = None, source: Optional[str] = None, priority: int = 0):
    return event_bus.publish(event_type, data, source, priority)


def subscribe(event_type: str, callback: Callable, async_callback: bool = False):
    event_bus.subscribe(event_type, callback, async_callback)