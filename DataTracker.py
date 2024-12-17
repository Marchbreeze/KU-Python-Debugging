from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import sys
import inspect
import warnings
from ast import AST
from StackInspector import StackInspector

class DataTracker(StackInspector):

    def __init__(self, log: bool = False) -> None:
        self.log = log

    def set(self, name: str, value: Any, loads: Optional[Set[str]] = None) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: setting {name}")
        return value

    def get(self, name: str, value: Any) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: getting {name}")
        return value

    def augment(self, name: str, value: Any) -> Any:
        self.set(name, self.get(name, value))
        return value

    def test(self, cond: AST) -> AST:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: testing condition")
        return cond

    def arg(self, value: Any, pos: Optional[int] = None, kw: Optional[str] = None) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            info = ""
            if pos:
                info += f" #{pos}"
            if kw:
                info += f" {repr(kw)}"
            print(f"{caller_func.__name__}:{lineno}: pushing arg{info}")
        return value

    def ret(self, value: Any) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: returned from call")
        return value

    def instrument_call(self, func: Callable) -> Callable:
        return func

    def call(self, func: Callable) -> Callable:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: calling {func}")
        return self.instrument_call(func)

    def param(self, name: str, value: Any, pos: Optional[int] = None, vararg: str = '', last: bool = False) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            info = ""
            if pos is not None:
                info += f" #{pos}"
            print(f"{caller_func.__name__}:{lineno}: initializing {vararg}{name}{info}")
        return self.set(name, value)

    def __enter__(self) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: entering block")
        return self

    def __exit__(self, exc_type: Type, exc_value: BaseException, traceback: TracebackType) -> Optional[bool]:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: exiting block")
        return None