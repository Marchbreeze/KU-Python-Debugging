from types import FrameType, TracebackType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import sys
import copy

class StackInspector:
    def caller_frame(self) -> FrameType:
        frame = cast(FrameType, inspect.currentframe())
        while self.our_frame(frame):
            frame = cast(FrameType, frame.f_back)
        return frame

    def our_frame(self, frame: FrameType) -> bool:
        return isinstance(frame.f_locals.get('self'), self.__class__)
    
    def is_internal_error(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> bool:
        if not exc_tp:
            return False
        for frame, lineno in traceback.walk_tb(exc_traceback):
            if self.our_frame(frame):
                return True
        return False

class MyTracer(StackInspector):
    def __init__(self, target_func: str) -> None:
        self.target_func = target_func
        self.my_map: Dict[str, int] = {} 

    def traceit(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        if frame.f_code.co_name == self.target_func:
            if event == 'call':
                return self.traceit
        return None
                
    def log(self, *objects: Any, sep: str = ' ', end: str = '\n', flush: bool = True) -> None:
        print(*objects, sep=sep, end=end, file=sys.stdout, flush=flush)
        
    def __enter__(self) -> 'MyTracer':
        self.original_trace_function = sys.gettrace()
        sys.settrace(self.traceit)
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        sys.settrace(self.original_trace_function)
        return None

    def getLVVmap(self) -> Dict[str, int]:
        return self.my_map