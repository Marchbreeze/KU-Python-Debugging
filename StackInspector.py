from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import warnings

Location = Tuple[Callable, int]

class StackInspector:
    def caller_frame(self) -> FrameType:
        frame = cast(FrameType, inspect.currentframe())
        while self.our_frame(frame):
            frame = cast(FrameType, frame.f_back)
        return frame

    def our_frame(self, frame: FrameType) -> bool:
        return isinstance(frame.f_locals.get('self'), self.__class__)
    
    def search_frame(self, name: str, frame: Optional[FrameType] = None) -> Tuple[Optional[FrameType], Optional[Callable]]:
        if frame is None:
            frame = self.caller_frame()
        while frame:
            item = None
            if name in frame.f_globals:
                item = frame.f_globals[name]
            if name in frame.f_locals:
                item = frame.f_locals[name]
            if item and callable(item):
                return frame, item
            frame = cast(FrameType, frame.f_back)
        return None, None

    def search_func(self, name: str, frame: Optional[FrameType] = None) -> Optional[Callable]:
        frame, func = self.search_frame(name, frame)
        return func
    
    _generated_function_cache: Dict[Tuple[str, int], Callable] = {}

    def create_function(self, frame: FrameType) -> Callable:
        name = frame.f_code.co_name
        cache_key = (name, frame.f_lineno)
        if cache_key in self._generated_function_cache:
            return self._generated_function_cache[cache_key]
        try:
            generated_function = cast(Callable,FunctionType(frame.f_code,globals=frame.f_globals,name=name))
        except TypeError:
            generated_function = self.unknown
        except Exception as exc:
            warnings.warn(f"Couldn't create function for {name} " f" ({type(exc).__name__}: {exc})")
            generated_function = self.unknown
        self._generated_function_cache[cache_key] = generated_function
        return generated_function
    
    def caller_location(self) -> Location:
        return self.caller_function(), self.caller_frame().f_lineno

    def caller_function(self) -> Callable:
        frame = self.caller_frame()
        name = frame.f_code.co_name
        func = self.search_func(name)
        if func:
            return func
        return self.create_function(frame)

    def unknown(self) -> None:
        pass

    def is_internal_error(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> bool:
        if not exc_tp:
            return False
        for frame, lineno in traceback.walk_tb(exc_traceback):
            if self.our_frame(frame):
                return True
        return False