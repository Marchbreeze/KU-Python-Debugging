from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
from StackInspector import StackInspector

class Instrumenter(StackInspector):
    def __init__(self, *items_to_instrument: Callable, globals: Optional[Dict[str, Any]] = None, log: Union[bool, int] = False) -> None:
        self.log = log
        self.items_to_instrument: List[Callable] = list(items_to_instrument)
        self.instrumented_items: Set[Any] = set()
        if globals is None:
            globals = self.caller_globals()
        self.globals = globals

    def default_items_to_instrument(self) -> List[Callable]:
        return []

    def instrument(self, item: Any) -> Any:
        if self.log:
            print("Instrumenting", item)
        self.instrumented_items.add(item)
        return item

    def __enter__(self) -> Any:
        items = self.items_to_instrument
        if not items:
            items = self.default_items_to_instrument()
        for item in items:
            self.instrument(item)
        return self

    def __exit__(self, exc_type: Type, exc_value: BaseException,traceback: TracebackType) -> Optional[bool]:
        self.restore()
        return None

    def restore(self) -> None:
        for item in self.instrumented_items:
            self.globals[item.__name__] = item