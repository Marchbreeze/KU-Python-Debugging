from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
from ast import NodeVisitor

class StatementVisitor(NodeVisitor):
    def __init__(self) -> None:
        # 문장과 함수 이름을 저장하는 리스트
        self.statements: List[Tuple[ast.AST, str]] = []
        # 현재 탐색 중인 함수의 이름
        self.func_name = ""
        # 이미 본 문장을 저장하는 집합 (중복 방지)
        self.statements_seen: Set[Tuple[ast.AST, str]] = set()
        super().__init__()

	# 노드에서 특정 속성(attr)을 가져와 문장으로 추가
    def add_statements(self, node: ast.AST, attr: str) -> None:
        elems: List[ast.AST] = getattr(node, attr, [])
        if not isinstance(elems, list):
            elems = [elems]  # 리스트가 아닐 경우, 단일 요소를 리스트로 변환
        for elem in elems:
            stmt = (elem, self.func_name)
            if stmt in self.statements_seen:
                continue  # 이미 본 문장은 추가하지 않음
            self.statements.append(stmt)  # 문장 추가
            self.statements_seen.add(stmt)  # 중복 방지를 위해 집합에 추가

	# 기본 노드 방문 메서드: 'body'와 'orelse' 속성을 탐색
    def visit_node(self, node: ast.AST) -> None:
        self.add_statements(node, 'body')
        self.add_statements(node, 'orelse')

	# 모듈 노드를 방문 - 자식은 문장 추가 X
    def visit_Module(self, node: ast.Module) -> None:
        super().generic_visit(node)

	# 클래스 정의 노드 방문 - 자식은 문장 추가 X
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        super().generic_visit(node)

	# AST의 모든 노드를 방문하는 기본 메서드
    def generic_visit(self, node: ast.AST) -> None:
        self.visit_node(node)  # 노드의 body와 orelse 탐색
        super().generic_visit(node)

	# 함수 정의 노드를 방문
    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        if not self.func_name:
            self.func_name = node.name  # 현재 함수의 이름 설정
        self.visit_node(node)  # 함수 내부의 body와 orelse 탐색
        super().generic_visit(node)  # 자식 노드 탐색
        self.func_name = ""  # 함수 탐색이 끝나면 함수 이름 초기화

	# 비동기 함수 정의 노드를 방문
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return self.visit_FunctionDef(node)  # 함수 정의 방문 메서드를 호출


# tree에서 모든 문장과 해당 문장이 속한 함수명을 반환
def all_statements_and_functions(tree: ast.AST, tp: Optional[Type] = None) -> List[Tuple[ast.AST, str]]:
    visitor = StatementVisitor()  # StatementVisitor 인스턴스 생성
    visitor.visit(tree)           # AST 방문 시작
    statements = visitor.statements  # 수집된 문장과 함수명
    if tp is not None:
        # 특정 클래스(tp)에 해당하는 문장만 필터링
        statements = [s for s in statements if isinstance(s[0], tp)]
    return statements  # 필터링된 문장과 함수명 반환

# tree에서 모든 문장만 반환
def all_statements(tree: ast.AST, tp: Optional[Type] = None) -> List[ast.AST]:
    # all_statements_and_functions를 호출해 문장만 추출
    return [stmt for stmt, func_name in all_statements_and_functions(tree, tp)]