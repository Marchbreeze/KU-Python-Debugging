from types import FunctionType, FrameType, TracebackType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import typing
from DependencyTracker import DependencyTracker
import ast


class StackInspector:
    def caller_frame(self) -> FrameType:
        frame = cast(FrameType, inspect.currentframe())
        while self.our_frame(frame):
            frame = cast(FrameType, frame.f_back)
        return frame

    def our_frame(self, frame: FrameType) -> bool:
        return isinstance(frame.f_locals.get('self'), self.__class__)
    
    def is_internal_error(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> bool:
        if not exc_tp:
            return False
        for frame, lineno in traceback.walk_tb(exc_traceback):
            if self.our_frame(frame):
                return True
        return False


class Instrumenter(StackInspector):
    def __init__(self, *items_to_instrument: Callable,
                 globals: Optional[Dict[str, Any]] = None,
                 log: Union[bool, int] = False) -> None:
        self.log = log
        self.items_to_instrument: List[Callable] = list(items_to_instrument)
        self.instrumented_items: Set[Any] = set()
        if globals is None:
            globals = self.caller_globals()
        self.globals = globals

    def caller_globals(self) -> Dict[str, Any]:
        frame = self.caller_frame()
        return frame.f_globals

    def __enter__(self) -> Any:
        items = self.items_to_instrument
        if not items:
            items = self.default_items_to_instrument()
        for item in items:
            self.instrument(item)
        return self

    def default_items_to_instrument(self) -> List[Callable]:
        return []

    def instrument(self, item: Any) -> Any:
        if self.log:
            print("Instrumenting", item)
        self.instrumented_items.add(item)
        return item

    def __exit__(self, exc_type: Type, exc_value: BaseException, traceback: TracebackType) -> Optional[bool]:
        self.restore()
        return None

    def restore(self) -> None:
        for item in self.instrumented_items:
            self.globals[item.__name__] = item


def is_internal(id: str) -> bool:
    return (id in dir(__builtins__) or id in dir(typing))

def set_ast_node_location(node: ast.AST, lineno: int, col_offset: int = 0) -> ast.AST:
    node.lineno = lineno
    node.col_offset = col_offset
    for child in ast.iter_child_nodes(node):
        set_ast_node_location(child, lineno, col_offset)
    return node

class Slicer(Instrumenter):
    def __init__(self, *items_to_instrument: Any,
                 dependency_tracker: Optional[DependencyTracker] = None,
                 globals: Optional[Dict[str, Any]] = None,
                 log: Union[bool, int] = False):
        super().__init__(*items_to_instrument, globals=globals, log=log)
        if dependency_tracker is None:
            dependency_tracker = DependencyTracker(log=(log > 1))
        self.dependency_tracker = dependency_tracker
        self.saved_dependencies = None
        self.globals["track_dependency"] = self.dependency_tracker.set

    def default_items_to_instrument(self) -> List[Callable]:
        raise ValueError("Need one or more items to instrument")

    def parse(self, item: Any) -> ast.AST:
        source_lines, lineno = inspect.getsourcelines(item)
        source = "".join(source_lines)
        if self.log >= 2:
            print(source)
        tree = ast.parse(source)
        ast.increment_lineno(tree, lineno - 1)
        return tree

    def instrument(self, item: Any) -> Any:
        if is_internal(item.__name__):
            return item  
        if inspect.isbuiltin(item):
            return item
        item = super().instrument(item)
        tree = self.parse(item)
        tree = self.transform(tree)
        self.execute(tree, item)
        new_item = self.globals[item.__name__]
        return new_item

    def transform(self, tree: ast.AST) -> ast.AST:
        class DependencyTransformer(ast.NodeTransformer):
            def __init__(self, tracker_name: str):
                self.tracker_name = tracker_name

            def visit_Assign(self, node: ast.Assign) -> ast.AST:
                targets = [ast.Str(s=target.id) for target in node.targets if isinstance(target, ast.Name)]
                values = [ast.Str(s=repr(node.value))] if isinstance(node.value, ast.expr) else []
                tracking_call = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id=self.tracker_name, ctx=ast.Load()),
                        args=targets + values,
                        keywords=[]
                    )
                )
                set_ast_node_location(tracking_call, node.lineno, node.col_offset)
                return [node, tracking_call]

        transformer = DependencyTransformer(tracker_name="track_dependency")
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)
        return tree

    def execute(self, tree: ast.AST, item: Any) -> None:
        filename = inspect.getsourcefile(item) or "<unknown>"
        compiled_code = compile(tree, filename=filename, mode="exec")
        exec(compiled_code, self.globals)
