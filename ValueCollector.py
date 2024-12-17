from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
from Collector import Collector

class ValueCollector(Collector):
    def __init__(self) -> None:
        super().__init__()
        self.vars: Set[str] = set()

    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        local_vars = frame.f_locals  
        for var in local_vars:
            value = local_vars[var]
            self.vars.add(f"{var} = {repr(value)}") 

    def events(self) -> Set[str]:
        return self.vars