from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
from SpectrumDebugger import SpectrumDebugger

class DiscreteSpectrumDebugger(SpectrumDebugger):
    def suspiciousness(self, event: Any) -> Optional[float]:
        passing = self.all_pass_events()
        failing = self.all_fail_events()
        if event in passing and event in failing:
            return 0.5
        elif event in failing:
            return 1.0
        elif event in passing:
            return 0.0
        else:
            return None

    def color(self, event: Any) -> Optional[str]:
        suspiciousness = self.suspiciousness(event)
        if suspiciousness is None:
            return None
        if suspiciousness > 0.8:
            return 'mistyrose'
        if suspiciousness >= 0.5:
            return 'lightyellow'
        return 'honeydew'

    def tooltip(self, event: Any) -> str:
        passing = self.all_pass_events()
        failing = self.all_fail_events()
        if event in passing and event in failing:
            return "in passing and failing runs"
        elif event in failing:
            return "only in failing runs"
        elif event in passing:
            return "only in passing runs"
        else:
            return "never"

# d = DiscreteSpectrumDebugger()
# with d:
#     remove_html_markup('abc')
# with d:
#     remove_html_markup('<b>abc</b>')
# with d:
#     remove_html_markup('"abc"')
#     assert False  
# print(d)