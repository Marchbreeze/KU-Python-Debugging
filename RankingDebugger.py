from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
from DiscreteSpectrumDebugger import DiscreteSpectrumDebugger

class RankingDebugger(DiscreteSpectrumDebugger):
    def rank(self) -> List[Any]:
        
        def susp(event: Any) -> float:
            suspiciousness = self.suspiciousness(event)
            assert suspiciousness is not None
            return suspiciousness
        
        events = list(self.all_events())
        events.sort(key=susp, reverse=True)
        return events

    def __repr__(self) -> str:
        return repr(self.rank())