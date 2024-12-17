from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
from ast import Load, Store, Attribute, keyword, Call, NodeVisitor, Name, AST
import typing

DATA_TRACKER = '_data'

class LeftmostNameVisitor(NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.leftmost_name: Optional[str] = None

    def visit_Name(self, node: Name) -> None:
        if self.leftmost_name is None:
            self.leftmost_name = node.id
        self.generic_visit(node)

def leftmost_name(tree: AST) -> Optional[str]:
    visitor = LeftmostNameVisitor()
    visitor.visit(tree)
    return visitor.leftmost_name


class StoreVisitor(NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.names: Set[str] = set()

    def visit(self, node: AST) -> None:
        if hasattr(node, 'ctx') and isinstance(node.ctx, Store):  # type: ignore
            name = leftmost_name(node)
            if name:
                self.names.add(name)
        self.generic_visit(node)

def store_names(tree: AST) -> Set[str]:
    visitor = StoreVisitor()
    visitor.visit(tree)
    return visitor.names


class LoadVisitor(NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.names: Set[str] = set()

    def visit(self, node: AST) -> None:
        if hasattr(node, 'ctx') and isinstance(node.ctx, Load):  # type: ignore
            name = leftmost_name(node)
            if name is not None:
                self.names.add(name)
        self.generic_visit(node)

def load_names(tree: AST) -> Set[str]:
    visitor = LoadVisitor()
    visitor.visit(tree)
    return visitor.names



def is_internal(id: str) -> bool:
    return (id in dir(__builtins__) or id in dir(typing))

def make_get_data(id: str, method: str = 'get') -> Call:
    return Call(func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()), attr=method, ctx=Load()),
                args=[ast.Str(id), Name(id=id, ctx=Load())],
                keywords=[])

def make_set_data(id: str, value: Any, loads: Optional[Set[str]] = None, method: str = 'set') -> Call:
    keywords=[]
    if loads:
        keywords = [
            keyword(arg='loads',
                    value=ast.Tuple(
                        elts=[Name(id=load, ctx=Load()) for load in loads],
                        ctx=Load()
                    ))
        ]
    new_node = Call(func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()), 
                    attr=method, ctx=Load()),
                    args=[ast.Str(id), value],
                    keywords=keywords)
    ast.copy_location(new_node, value)
    return new_node

def dump_tree(tree: AST) -> None:
    print(ast.unparse(tree), '.py')
    ast.fix_missing_locations(tree) 
    _ = compile(cast(ast.Module, tree), '<dump_tree>', 'exec')