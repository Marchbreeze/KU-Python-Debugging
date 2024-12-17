from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import sys
from ConditionalTracer import ConditionalTracer

class EventTracer(ConditionalTracer):

    def __init__(self, *, condition: Optional[str] = None, events: List[str] = []) -> None:
        self.events = events
        self.last_event_values: Dict[str, Any] = {}
        super().__init__(condition=condition)

    def events_changed(self, events: List[str], frame: FrameType) -> bool:
        change = False
        for event in events:
            value = self.eval_in_context(event, frame)
            if (event not in self.last_event_values or value != self.last_event_values[event]):
                self.last_event_values[event] = value
                change = True
        return change
    
    def do_report(self, frame: FrameType, event: str, arg: Any) -> bool:
        return (self.eval_in_context(self.condition, frame) or self.events_changed(self.events, frame))