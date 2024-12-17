from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
from Collector import Collector
from StatisticalDebugger import StatisticalDebugger

class DifferenceDebugger(StatisticalDebugger):

    PASS = 'PASS'
    FAIL = 'FAIL'

    def collect_pass(self, *args: Any, **kwargs: Any) -> Collector:
        return self.collect(self.PASS, *args, **kwargs)

    def collect_fail(self, *args: Any, **kwargs: Any) -> Collector:
        return self.collect(self.FAIL, *args, **kwargs)

    def pass_collectors(self) -> List[Collector]:
        return self.collectors[self.PASS]

    def fail_collectors(self) -> List[Collector]:
        return self.collectors[self.FAIL]

    def all_fail_events(self) -> Set[Any]:
        return self.all_events(self.FAIL)

    def all_pass_events(self) -> Set[Any]:
        return self.all_events(self.PASS)

    def only_fail_events(self) -> Set[Any]:
        return self.all_fail_events() - self.all_pass_events()

    def only_pass_events(self) -> Set[Any]:
        return self.all_pass_events() - self.all_fail_events()

    def __enter__(self) -> Any:
        self.collector = self.collector_class()
        self.collector.add_items_to_ignore([self.__class__])
        self.collector.__enter__()
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        status = self.collector.__exit__(exc_tp, exc_value, exc_traceback)
        if status is None:
            pass
        else:
            return False 
        if exc_tp is None:
            outcome = self.PASS
        else:
            outcome = self.FAIL
        self.add_collector(outcome, self.collector)
        return True