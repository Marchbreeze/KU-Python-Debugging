from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
from Collector import Collector
from StackInspector import StackInspector

Coverage = Set[Tuple[Callable, int]]


class CoverageCollector(Collector, StackInspector):

    def __init__(self) -> None:
        super().__init__()
        self._coverage: Coverage = set()

    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        name = frame.f_code.co_name
        function = self.search_func(name, frame)
        if function is None:
            function = self.create_function(frame)
        location = (function, frame.f_lineno)
        self._coverage.add(location)

    def events(self) -> Set[Tuple[str, int]]:
        return {(func.__name__, lineno) for func, lineno in self._coverage}

    def covered_functions(self) -> Set[Callable]:
        return {func for func, lineno in self._coverage}

    def coverage(self) -> Coverage:
        return self._coverage

def code_with_coverage(function: Callable, coverage: Coverage) -> None:
    source_lines, starting_line_number = inspect.getsourcelines(function)
    line_number = starting_line_number
    # 각 라인 앞에 실행 여부를 나타내는 별표 표시
    for line in source_lines:
        marker = '*' if (function, line_number) in coverage else ' '
        print(f"{line_number:4} {marker} {line}", end='')
        line_number += 1