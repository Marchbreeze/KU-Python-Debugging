from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import sys
import inspect
import warnings
from StackInspector import StackInspector
import ast
from ast import Module, Load, Store, \
    Attribute, With, withitem, keyword, Call, Expr, \
    Assign, AugAssign, AnnAssign, Assert, \
    NodeTransformer, NodeVisitor, Name, AST
from Visitor import *

class TrackGetTransformer(NodeTransformer):
    def visit_Name(self, node: Name) -> AST:
        self.generic_visit(node)
        if is_internal(node.id):
            return node
        if node.id == DATA_TRACKER:
            return node
        if not isinstance(node.ctx, Load):
            return node
        new_node = make_get_data(node.id)
        ast.copy_location(new_node, node)
        return new_node


class TrackSetTransformer(NodeTransformer):
    def visit_Assign(self, node: Assign) -> Assign:
        value = ast.unparse(node.value)
        if value.startswith(DATA_TRACKER + '.set'):
            return node
        for target in node.targets:
            loads = load_names(target)
            for store_name in store_names(target):
                node.value = make_set_data(store_name, node.value, loads=loads)
                loads = set()
        return node

    def visit_AugAssign(self, node: AugAssign) -> AugAssign:
        value = ast.unparse(node.value)
        if value.startswith(DATA_TRACKER):
            return node
        id = cast(str, leftmost_name(node.target))
        node.value = make_set_data(id, node.value, method='augment')
        return node

    def visit_AnnAssign(self, node: AnnAssign) -> AnnAssign:
        if node.value is None:
            return node
        value = ast.unparse(node.value)
        if value.startswith(DATA_TRACKER + '.set'):
            return node
        loads = load_names(node.target)
        for store_name in store_names(node.target):
            node.value = make_set_data(store_name, node.value, loads=loads)
            loads = set()
        return node

    def visit_Assert(self, node: Assert) -> Assert:
        value = ast.unparse(node.test)
        if value.startswith(DATA_TRACKER + '.set'):
            return node
        loads = load_names(node.test)
        node.test = make_set_data("<assertion>", node.test, loads=loads)
        return node


class TrackReturnTransformer(NodeTransformer):
    def __init__(self) -> None:
        self.function_name: Optional[str] = None
        super().__init__()

    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> AST:
        outer_name = self.function_name
        self.function_name = node.name  
        self.generic_visit(node)
        self.function_name = outer_name
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> AST:
        return self.visit_FunctionDef(node)

    def return_value(self, tp: str = "return") -> str:
        if self.function_name is None:
            return f"<{tp} value>"
        else:
            return f"<{self.function_name}() {tp} value>"

    def visit_return_or_yield(self, node: Union[ast.Return, ast.Yield, ast.YieldFrom], tp: str = "return") -> AST:
        if node.value is not None:
            value = ast.unparse(node.value)
            if not value.startswith(DATA_TRACKER + '.set'):
                node.value = make_set_data(self.return_value(tp), node.value)
        return node

    def visit_Return(self, node: ast.Return) -> AST:
        return self.visit_return_or_yield(node, tp="return")

    def visit_Yield(self, node: ast.Yield) -> AST:
        return self.visit_return_or_yield(node, tp="yield")

    def visit_YieldFrom(self, node: ast.YieldFrom) -> AST:
        return self.visit_return_or_yield(node, tp="yield")


class TrackControlTransformer(NodeTransformer):
    def visit_If(self, node: ast.If) -> ast.If:
        self.generic_visit(node)
        node.test = self.make_test(node.test)
        node.body = self.make_with(node.body)
        node.orelse = self.make_with(node.orelse)
        return node

    def make_with(self, block: List[ast.stmt]) -> List[ast.stmt]:
        if len(block) == 0:
            return []
        block_as_text = ast.unparse(block[0])
        if block_as_text.startswith('with ' + DATA_TRACKER):
            return block 
        new_node = With(
            items=[
                withitem(
                    context_expr=Name(id=DATA_TRACKER, ctx=Load()),
                    optional_vars=None)
            ],
            body=block
        )
        ast.copy_location(new_node, block[0])
        return [new_node]

    def make_test(self, test: ast.expr) -> ast.expr:
        test_as_text = ast.unparse(test)
        if test_as_text.startswith(DATA_TRACKER + '.test'):
            return test 
        new_test = Call(func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()),
                                        attr='test',
                                        ctx=Load()),
                                        args=[test],
                                        keywords=[])
        ast.copy_location(new_test, test)
        return new_test

    def visit_While(self, node: ast.While) -> ast.While:
        self.generic_visit(node)
        node.test = self.make_test(node.test)
        node.body = self.make_with(node.body)
        node.orelse = self.make_with(node.orelse)
        return node
    
    def visit_For(self, node: Union[ast.For, ast.AsyncFor]) -> AST:
        self.generic_visit(node)
        id = ast.unparse(node.target).strip()
        node.iter = make_set_data(id, node.iter)
        return node

    def visit_AsyncFor(self, node: ast.AsyncFor) -> AST:
        return self.visit_For(node)

    def visit_comprehension(self, node: ast.comprehension) -> AST:
        self.generic_visit(node)
        id = ast.unparse(node.target).strip()
        node.iter = make_set_data(id, node.iter)
        return node


class TrackCallTransformer(NodeTransformer):
    def make_call(self, node: AST, func: str, pos: Optional[int] = None, kw: Optional[str] = None) -> Call:
        keywords = []
        if pos:
            keywords.append(keyword(arg='pos', value=ast.Num(pos)))
        if kw:
            keywords.append(keyword(arg='kw', value=ast.Str(kw)))
        return Call(func=Attribute(value=Name(id=DATA_TRACKER,
                                            ctx=Load()),
                                            attr=func,
                                            ctx=Load()),
                                            args=[node],
                                            keywords=keywords)

    def visit_Call(self, node: Call) -> Call:
        self.generic_visit(node)
        call_as_text = ast.unparse(node)
        if call_as_text.startswith(DATA_TRACKER + '.ret'):
            return node  # Already applied
        func_as_text = ast.unparse(node)
        if func_as_text.startswith(DATA_TRACKER + '.'):
            return node  # Own function
        new_args = []
        for n, arg in enumerate(node.args):
            new_args.append(self.make_call(arg, 'arg', pos=n + 1))
        node.args = cast(List[ast.expr], new_args)
        for kw in node.keywords:
            id = kw.arg if hasattr(kw, 'arg') else None
            kw.value = self.make_call(kw.value, 'arg', kw=id)
        node.func = self.make_call(node.func, 'call')
        return self.make_call(node, 'ret')


class TrackParamsTransformer(NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        named_args = []
        for child in ast.iter_child_nodes(node.args):
            if isinstance(child, ast.arg):
                named_args.append(child)
        create_stmts = []
        for n, child in enumerate(named_args):
            keywords=[keyword(arg='pos', value=ast.Num(n + 1))]
            if child is node.args.vararg:
                keywords.append(keyword(arg='vararg', value=ast.Str('*')))
            if child is node.args.kwarg:
                keywords.append(keyword(arg='vararg', value=ast.Str('**')))
            if n == len(named_args) - 1:
                keywords.append(keyword(arg='last', value=ast.NameConstant(value=True)))
            create_stmt = Expr(
                value=Call(
                    func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()), attr='param', ctx=Load()),
                    args=[ast.Str(child.arg), Name(id=child.arg, ctx=Load())],
                    keywords=keywords
                )
            )
            ast.copy_location(create_stmt, node)
            create_stmts.append(create_stmt)
        node.body = cast(List[ast.stmt], create_stmts) + node.body
        return node