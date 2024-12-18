from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
from ast import NodeVisitor

class ConditionVisitor(NodeVisitor):
    def __init__(self) -> None:
        self.conditions: List[ast.expr] = []  # 수집된 조건식 노드 목록
        self.conditions_seen: Set[str] = set()  # 이미 방문한 조건식 문자열 집합
        super().__init__()

	# 노드의 특정 속성에 포함된 조건식을 추가 (중복 제외)
    def add_conditions(self, node: ast.AST, attr: str) -> None:
        # 속성 가져오기
        elems = getattr(node, attr, [])
        if not isinstance(elems, list):  # 속성이 리스트가 아니면 리스트로 변환
            elems = [elems]
        elems = cast(List[ast.expr], elems)  # 타입 캐스팅
        # 조건식 추가 (중복 확인)
        for elem in elems:
            elem_str = ast.unparse(elem)  # 조건식을 문자열로 변환
            if elem_str not in self.conditions_seen:  # 중복 조건 확인
                self.conditions.append(elem)  # 조건식 추가
                self.conditions_seen.add(elem_str)  # 방문한 조건식 기록

	# 논리 연산자(`and`, `or`)를 방문하여 조건식 수집
    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.add_conditions(node, 'values')  # 논리 연산자에 연결된 값들 추가
        return super().generic_visit(node)  # 하위 노드 탐색

# AST 트리에서 제어 구조의 조건식을 찾아 반환
def all_conditions(trees: Union[ast.AST, List[ast.AST]], tp: Optional[Type] = None) -> List[ast.expr]:
    # 입력이 리스트가 아니면 리스트로 변환
    if not isinstance(trees, list):
        assert isinstance(trees, ast.AST)
        trees = [trees]
    # ConditionVisitor를 사용해 조건식 수집
    visitor = ConditionVisitor()
    for tree in trees:  # 모든 트리에 대해 방문 실행
        visitor.visit(tree)
    # 수집된 조건식 가져오기
    conditions = visitor.conditions
    # 특정 타입(tp) 필터링
    if tp is not None:
        conditions = [c for c in conditions if isinstance(c, tp)]
    return conditions