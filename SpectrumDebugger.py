from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import html
from DifferenceDebugger import DifferenceDebugger

class SpectrumDebugger(DifferenceDebugger):
    def suspiciousness(self, event: Any) -> Optional[float]:
        return None

    def tooltip(self, event: Any) -> str:
        return self.percentage(event)

    def percentage(self, event: Any) -> str:
        suspiciousness = self.suspiciousness(event)
        if suspiciousness is not None:
            return str(int(suspiciousness * 100)).rjust(3) + '%'
        else:
            return ' ' * len('100%')

    def code(self, functions: Optional[Set[Callable]] = None, *, 
            color: bool = False, suspiciousness: bool = False,
            line_numbers: bool = True) -> str:
        if not functions:
            functions = self.covered_functions()
        out = ""
        seen = set()
        for function in functions:
            source_lines, starting_line_number = inspect.getsourcelines(function)
            if (function.__name__, starting_line_number) in seen:
                continue
            seen.add((function.__name__, starting_line_number))
            if out:
                out += '\n'
                if color:
                    out += '<p/>'
            line_number = starting_line_number
            for line in source_lines:
                if color:
                    line = html.escape(line)
                    if line.strip() == '':
                        line = '&nbsp;'
                location = (function.__name__, line_number)
                location_suspiciousness = self.suspiciousness(location)
                if location_suspiciousness is not None:
                    tooltip = f"Line {line_number}: {self.tooltip(location)}"
                else:
                    tooltip = f"Line {line_number}: not executed"
                if suspiciousness:
                    line = self.percentage(location) + ' ' + line
                if line_numbers:
                    line = str(line_number).rjust(4) + ' ' + line
                line_color = self.color(location)
                if color and line_color:
                    line = f'''<pre style="background-color:{line_color}"
                    title="{tooltip}">{line.rstrip()}</pre>'''
                elif color:
                    line = f'<pre title="{tooltip}">{line}</pre>'
                else:
                    line = line.rstrip()
                out += line + '\n'
                line_number += 1
        return out

    def _repr_html_(self) -> str:
        return self.code(color=True)

    def __str__(self) -> str:
        return self.code(color=False, suspiciousness=True)

    def __repr__(self) -> str:
        return self.code(color=False, suspiciousness=True)