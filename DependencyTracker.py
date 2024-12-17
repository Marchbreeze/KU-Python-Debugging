from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import sys
import inspect
import warnings
import copy
from ast import AST
import itertools
from DataTracker import DataTracker
from StackInspector import StackInspector
from Dependencies import Dependencies

TEST = '<test>'
Location = Tuple[Callable, int]
Node = Tuple[str, Location]
Dependency = Dict[Node, Set[Node]]

class DependencyTracker(DataTracker):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.origins: Dict[str, Location] = {}  # 현재 변수가 마지막으로 설정된 위치
        self.data_dependencies: Dependency = {} 
        self.control_dependencies: Dependency = {}

        self.last_read: List[str] = []  # 최근에 읽힌 변수 리스트
        self.last_checked_location = (StackInspector.unknown, 1) # 마지막으로 확인된 코드 위치
        self._ignore_location_change = False # 코드 실행 중 위치 변경을 무시할지 여부
        
        self.data: List[List[str]] = [[]]  # Data stack
        self.control: List[List[str]] = [[]]  # Control stack

        self.frames: List[Dict[Union[int, str], Any]] = [{}]  # Argument stack
        self.args: Dict[Union[int, str], Any] = {}  # Current args
    
    def get(self, name: str, value: Any) -> Any:
        self.check_location()
        self.last_read.append(name)
        return super().get(name, value)

    def clear_read(self) -> None:
        if self.log:
            direct_caller = inspect.currentframe().f_back.f_code.co_name  # type: ignore
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: "
                f"clearing read variables {self.last_read} "
                f"(from {direct_caller})")
        self.last_read = []

    def check_location(self) -> None:
        location = self.caller_location()
        func, lineno = location
        last_func, last_lineno = self.last_checked_location
        if self.last_checked_location != location:
            if self._ignore_location_change:
                self._ignore_location_change = False
            elif func.__name__.startswith('<'):
                pass
            elif last_func.__name__.startswith('<'):
                pass
            else:
                self.clear_read()
        self.last_checked_location = location

    def ignore_next_location_change(self) -> None:
        self._ignore_location_change = True

    def ignore_location_change(self) -> None:
        self.last_checked_location = self.caller_location()

    def set(self, name: str, value: Any, loads: Optional[Set[str]] = None) -> Any:
        def add_dependencies(dependencies: Set[Node], vars_read: List[str], tp: str) -> None:
            for var_read in vars_read:
                if var_read in self.origins:
                    if var_read == self.TEST and tp == "data":
                        continue
                    origin = self.origins[var_read]
                    dependencies.add((var_read, origin))
                    if self.log:
                        origin_func, origin_lineno = origin
                        caller_func, lineno = self.caller_location()
                        print(f"{caller_func.__name__}:{lineno}: "
                            f"new {tp} dependency: "
                            f"{name} <= {var_read} "
                            f"({origin_func.__name__}:{origin_lineno})")
        self.check_location()
        ret = super().set(name, value)
        location = self.caller_location()
        add_dependencies(self.data_dependencies.setdefault
                        ((name, location), set()),
                        self.last_read, tp="data")
        add_dependencies(self.control_dependencies.setdefault
                        ((name, location), set()),
                        cast(List[str], itertools.chain.from_iterable(self.control)),
                        tp="control")
        self.origins[name] = location
        self.last_read = [name]
        self._ignore_location_change = False
        return ret

    def dependencies(self) -> Dependencies:
        return Dependencies(self.data_dependencies, self.control_dependencies)

    def test(self, value: Any) -> Any:
        self.set(self.TEST, value)
        return super().test(value)

    def __enter__(self) -> Any:
        self.control.append(self.last_read)
        self.clear_read()
        return super().__enter__()

    def __exit__(self, exc_type: Type, exc_value: BaseException, traceback: TracebackType) -> Optional[bool]:
        self.clear_read()
        self.last_read = self.control.pop()
        self.ignore_next_location_change()
        return super().__exit__(exc_type, exc_value, traceback)

    def call(self, func: Callable) -> Callable:
        func = super().call(func)
        if inspect.isgeneratorfunction(func):
            return self.call_generator(func)
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: " f"saving read variables {self.last_read}")
        self.data.append(self.last_read)
        self.clear_read()
        self.ignore_next_location_change()
        self.frames.append(self.args)
        self.args = {}
        return func

    def ret(self, value: Any) -> Any:
        value = super().ret(value)
        if self.in_generator():
            return self.ret_generator(value)
        ret_name = None
        for var in self.last_read:
            if var.startswith("<"): 
                ret_name = var
        self.last_read = self.data.pop()
        if ret_name:
            self.last_read.append(ret_name)
        if self.args:
            for key, deps in self.args.items():
                self.last_read += deps
        self.ignore_location_change()
        self.args = self.frames.pop()
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: " f"restored read variables {self.last_read}")
        return value

    def arg(self, value: Any, pos: Optional[int] = None, kw: Optional[str] = None) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: " f"saving args read {self.last_read}")
        if pos:
            self.args[pos] = self.last_read
        if kw:
            self.args[kw] = self.last_read
        self.clear_read()
        return super().arg(value, pos, kw)

    def param(self, name: str, value: Any, pos: Optional[int] = None, vararg: str = "", last: bool = False) -> Any:
        self.clear_read()
        if vararg == '*':
            for index in self.args:
                if isinstance(index, int) and pos is not None and index >= pos:
                    self.last_read += self.args[index]
        elif vararg == '**':
            for index in self.args:
                if isinstance(index, str):
                    self.last_read += self.args[index]
        elif name in self.args:
            self.last_read = self.args[name]
        elif pos in self.args:
            self.last_read = self.args[pos]
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: " f"restored params read {self.last_read}")
        self.ignore_location_change()
        ret = super().param(name, value, pos)
        if last:
            self.clear_read()
            self.args = {}
        return ret