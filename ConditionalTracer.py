from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import sys
from Tracer import Tracer

class ConditionalTracer(Tracer):
    def __init__(self, *, condition: Optional[str] = None) -> None:
        if condition is None:
            condition = 'False'
        self.condition: str = condition
        self.last_report: Optional[bool] = None
        super().__init__()
    
    def eval_in_context(self, expr: str, frame: FrameType) -> Optional[bool]:
        try:
            cond = eval(expr, None, frame.f_locals)
        except NameError:
            cond = None
        return cond

    def do_report(self, frame: FrameType, event: str, arg: Any) -> Optional[bool]:
        return self.eval_in_context(self.condition, frame)

    def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
        report = self.do_report(frame, event, arg)
        if report != self.last_report:
            if report:
                self.log("...")
            self.last_report = report

        if report:
            self.print_debugger_status(frame, event, arg)