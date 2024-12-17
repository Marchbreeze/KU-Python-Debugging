from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import ast
from ast import AST, NodeTransformer
from Instrumenter import Instrumenter
from DependencyTracker import DependencyTracker
from Dependencies import Dependencies
from Transformer import *
from PrintContent import print_content

"""
- `log=True` (or `log=1`): Show instrumented source code
- `log=2`: Also log execution
- `log=3`: Also log individual transformer steps
- `log=4`: Also log source line numbers
"""

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

    def default_items_to_instrument(self) -> List[Callable]:
        raise ValueError("Need one or more items to instrument")

    def parse(self, item: Any) -> AST:
        """Parse `item`, returning its AST"""
        source_lines, lineno = inspect.getsourcelines(item)
        source = "".join(source_lines)
        if self.log >= 2:
            print_content(source, '.py', start_line_number=lineno)
            print()
            print()
        tree = ast.parse(source)
        ast.increment_lineno(tree, lineno - 1)
        return tree

    def transformers(self) -> List[NodeTransformer]:
        return [
            TrackCallTransformer(),
            TrackSetTransformer(),
            TrackGetTransformer(),
            TrackControlTransformer(),
            TrackReturnTransformer(),
            TrackParamsTransformer()
        ]

    def transform(self, tree: AST) -> AST:
        for transformer in self.transformers():
            if self.log >= 3:
                print(transformer.__class__.__name__ + ':')
            transformer.visit(tree)
            ast.fix_missing_locations(tree)
            if self.log >= 3:
                print_content(ast.unparse(tree), '.py')
                print()
                print()
        if 0 < self.log < 3:
            print_content(ast.unparse(tree), '.py')
            print()
            print()
        return tree

    def execute(self, tree: AST, item: Any) -> None:
        source = cast(str, inspect.getsourcefile(item))
        code = compile(cast(ast.Module, tree), source, 'exec')
        self.globals[DATA_TRACKER] = self.dependency_tracker
        exec(code, self.globals)

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

    def restore(self) -> None:
        if DATA_TRACKER in self.globals:
            self.saved_dependencies = self.globals[DATA_TRACKER]
            del self.globals[DATA_TRACKER]
        super().restore()

    def dependencies(self) -> Dependencies:
        if self.saved_dependencies is None:
            return Dependencies({}, {})
        return self.saved_dependencies.dependencies()

    def code(self, *args: Any, **kwargs: Any) -> None:
        first = True
        for item in self.instrumented_items:
            if not first:
                print()
            self.dependencies().code(item, *args, **kwargs)
            first = False