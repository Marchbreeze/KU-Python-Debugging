from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import sys
import inspect
from StackInspector import StackInspector

class Tracer(StackInspector):

    def __init__(self) -> None:
        self.original_trace_function: Optional[Callable] = None
        self.last_vars: Dict[str, Any] = {}

    def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
        self.print_debugger_status(frame, event, arg)

    def _traceit(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        if self.our_frame(frame):
            pass
        else:
            self.traceit(frame, event, arg)
        return self._traceit
    
    def print_debugger_status(self, frame: FrameType, event: str, arg: Any) -> None:
        changes = self.changed_vars(frame.f_locals)
        changes_s = ", ".join([var + " = " + repr(changes[var]) for var in changes])

        if event == 'call':
            self.log("Calling " + frame.f_code.co_name + '(' + changes_s + ')')
        elif changes:
            self.log(' ' * 40, '#', changes_s)

        if event == 'line':
            try:
                module = inspect.getmodule(frame.f_code)
                if module is None:
                    source = inspect.getsource(frame.f_code)
                else:
                    source = inspect.getsource(module)
                current_line = source.split('\n')[frame.f_lineno - 1]
            except OSError as err:
                self.log(f"{err.__class__.__name__}: {err}")
                current_line = ""
            self.log(repr(frame.f_lineno) + ' ' + current_line)

        if event == 'return':
            self.log(frame.f_code.co_name + '()' + " returns " + repr(arg))
            self.last_vars = {}  #\\
    
    def changed_vars(self, new_vars: Dict[str, Any]) -> Dict[str, Any]:
        changed = {}
        for var_name, var_value in new_vars.items():
            if (var_name not in self.last_vars or self.last_vars[var_name] != var_value):
                changed[var_name] = var_value
        self.last_vars = new_vars.copy()
        return changed

    def log(self, *objects: Any, sep: str = ' ', end: str = '\n', flush: bool = True) -> None:
        print(*objects, sep=sep, end=end, flush=flush)

    def __enter__(self) -> Any:
        self.original_trace_function = sys.gettrace()
        sys.settrace(self._traceit)
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        sys.settrace(self.original_trace_function)
        if self.is_internal_error(exc_tp, exc_value, exc_traceback):
            return False
        else:
            return None