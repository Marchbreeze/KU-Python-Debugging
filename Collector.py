from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
from Tracer import Tracer

Coverage = Set[Tuple[Callable, int]]

class Collector(Tracer):

    def __init__(self) -> None:
        self._function: Optional[Callable] = None
        self._args: Optional[Dict[str, Any]] = None
        self._argstring: Optional[str] = None
        self._exception: Optional[Type] = None
        self.items_to_ignore: List[Union[Type, Callable]] = [self.__class__]

    def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
        for item in self.items_to_ignore:
            if (isinstance(item, type) and 'self' in frame.f_locals and
                isinstance(frame.f_locals['self'], item)):
                return
            if item.__name__ == frame.f_code.co_name:
                return
        if self._function is None and event == 'call':
            # Save function
            self._function = self.create_function(frame)
            self._args = frame.f_locals.copy()
            self._argstring = ", ".join([f"{var}={repr(self._args[var])}" for var in self._args])
        self.collect(frame, event, arg)

    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        pass

    def id(self) -> str:
        return f"{self.function().__name__}({self.argstring()})"

    def function(self) -> Callable:
        if not self._function:
            raise ValueError("No call collected")
        return self._function

    def argstring(self) -> str:
        if not self._argstring:
            raise ValueError("No call collected")
        return self._argstring

    def args(self) -> Dict[str, Any]:
        if not self._args:
            raise ValueError("No call collected")
        return self._args

    def exception(self) -> Optional[Type]:
        return self._exception

    def __repr__(self) -> str:
        return self.id()

    def covered_functions(self) -> Set[Callable]:
        return set()

    def coverage(self) -> Coverage:
        return set()

    def events(self) -> Set:
        return set()

    def add_items_to_ignore(self,items_to_ignore: List[Union[Type, Callable]]) -> None:
        self.items_to_ignore += items_to_ignore

    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        ret = super().__exit__(exc_tp, exc_value, exc_traceback)
        if not self._function:
            if exc_tp:
                return False
            else:
                raise ValueError("No call collected")

        return ret