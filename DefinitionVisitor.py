from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
from ast import NodeVisitor

class DefinitionVisitor(NodeVisitor):
    def __init__(self) -> None:
        self.definitions: List[str] = []

    def add_definition(self, node: Union[ast.ClassDef, 
                                        ast.FunctionDef, 
                                        ast.AsyncFunctionDef]) -> None:
        self.definitions.append(node.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.add_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.add_definition(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.add_definition(node)