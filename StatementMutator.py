from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
import warnings
import random
import re
import copy
from ast import NodeTransformer
from StatementVisitor import all_statements_and_functions, all_statements
from PrintContent import print_content

RE_SPACE = re.compile(r'\s+')
    
class StatementMutator(NodeTransformer):
    
    NODE_MAX_LENGTH = 20

    def __init__(self,
                suspiciousness_func: Optional[Callable[[Tuple[Callable, int]], float]] = None, 
                source: Optional[List[ast.AST]] = None,
                log: Union[bool, int] = False) -> None:
        super().__init__()
        self.log = log 
        # suspiciousness_func가 제공되지 않은 경우, 모든 위치에 대해 의심 정도를 1.0으로 설정
        if suspiciousness_func is None:
            def suspiciousness_func(location: Tuple[Callable, int]) -> float:
                return 1.0
        assert suspiciousness_func is not None
        self.suspiciousness_func: Callable = suspiciousness_func  # 의심 정도를 평가하는 함수
        # source가 주어지지 않으면 빈 리스트로 초기화
        if source is None:
            source = []
        self.source = source  # 변이에 사용할 소스 코드 문장 리스트
        # 로깅 수준이 2 이상일 경우, 소스 코드 문장 리스트 출력
        if self.log > 1:
            for i, node in enumerate(self.source):
                print(f"수리 소스 #{i}:")
                print_content(ast.unparse(node), '.py')  # AST를 코드로 변환하여 출력
                print()
                print()
        self.mutations = 0  # 변이 횟수 초기화

    # AST 노드의 의심도를 평가
    def node_suspiciousness(self, stmt: ast.AST, func_name: str) -> float:
        # 노드에 'lineno' 속성이 없으면 경고를 출력하고 의심도를 0.0으로 반환
        if not hasattr(stmt, 'lineno'):
            warnings.warn(f"{self.format_node(stmt)}: 예상된 줄 번호가 없습니다.")
            return 0.0
        # suspiciousness_func를 호출하여 노드의 의심도 계산
        suspiciousness = self.suspiciousness_func((func_name, stmt.lineno))
        if suspiciousness is None:  # 실행되지 않은 경우
            return 0.0
        return suspiciousness
    
    # AST 노드의 문자열 표현을 반환
    def format_node(self, node: ast.AST) -> str:
        if node is None:
            return "None"
        if isinstance(node, list):
            # 노드가 리스트인 경우 각 노드를 순회하며 문자열로 변환 후 연결
            return "; ".join(self.format_node(elem) for elem in node)
        # AST 노드를 문자열로 변환하고, 연속된 공백을 하나의 공백으로 축소
        s = RE_SPACE.sub(' ', ast.unparse(node)).strip()
        # 문자열 길이가 NODE_MAX_LENGTH를 초과하면 잘라서 "..."를 추가
        if len(s) > self.NODE_MAX_LENGTH - len("..."):
            s = s[:self.NODE_MAX_LENGTH] + "..."
        return repr(s)  # 문자열 표현을 반환

    # 변이할 AST 노드 선택
    def node_to_be_mutated(self, tree: ast.AST) -> ast.AST:
        # 모든 문장과 함수명
        statements = all_statements_and_functions(tree)
        assert len(statements) > 0, "No statements"  # 문장이 없는 경우 예외 처리
        # 각 문장의 의심도를 계산하여 가중치 리스트 생성
        weights = [self.node_suspiciousness(stmt, func_name) 
                for stmt, func_name in statements]
        # 문장만 따로 리스트로 추출
        stmts = [stmt for stmt, func_name in statements]
        # 로깅 모드가 2 이상인 경우, 각 노드의 가중치를 출력
        if self.log > 1:
            print("Weights:")
            for i, stmt in enumerate(statements):
                node, func_name = stmt
                print(f"{weights[i]:.2} {self.format_node(node)}")
        # 모든 가중치의 합이 0인 경우, 가중치 없이 랜덤 선택
        if sum(weights) == 0.0:
            # 의심도가 없는 경우, 모든 문장에서 무작위로 선택
            return random.choice(stmts)
        else:
            # 의심도를 가중치로 사용하여 랜덤하게 문장 선택
            return random.choices(stmts, weights=weights)[0]

    # 변이 연산 중 하나를 랜덤하게 선택
    def choose_op(self) -> Callable:
        return random.choice([self.insert, self.swap, self.delete])
    
    # AST 노드를 방문하고 변이 연산을 적용   
    def visit(self, node: ast.AST) -> ast.AST:
        super().visit(node)  # 자식 노드들을 방문 및 변환
        # mutate_me 속성이 없는 경우 원래 노드를 반환
        if not node.mutate_me:  # type: ignore
            return node
        # 변이 연산 선택 및 적용
        op = self.choose_op()
        new_node = op(node)  # 선택된 연산 실행
        self.mutations += 1  # 변이 횟수 증가
        # 로깅 활성화 시, 변이 정보 출력
        if self.log:
            print(f"{node.lineno:4}:{op.__name__ + ':':7} "  # type: ignore
                f"{self.format_node(node)} "
                f"becomes {self.format_node(new_node)}")
        return new_node  # 변이된 노드 반환

    # 소스에서 랜덤한 문장을 선택하고 복사하여 반환
    def choose_statement(self) -> ast.AST:
        return copy.deepcopy(random.choice(self.source))
        
    # node를 소스에서 랜덤하게 선택된 노드로 교체
    def swap(self, node: ast.AST) -> ast.AST:
        new_node = self.choose_statement()  # 랜덤한 문장 선택
        if isinstance(new_node, ast.stmt):  # 선택된 노드가 문장인지 확인
            if hasattr(new_node, 'body'):
                new_node.body = [ast.Pass()]  # body를 pass 문으로 대체
            if hasattr(new_node, 'orelse'):
                new_node.orelse = []  # orelse를 빈 리스트로 초기화
            if hasattr(new_node, 'finalbody'):
                new_node.finalbody = []  # finalbody를 빈 리스트로 초기화
        # 위치 정보 복사로 라인 정보 유지
        ast.copy_location(new_node, node)
        return new_node

    # 랜덤한 노드를 node 앞이나 뒤에 삽입
    def insert(self, node: ast.AST) -> Union[ast.AST, List[ast.AST]]:
        # 소스에서 랜덤한 문장을 선택
        new_node = self.choose_statement()
        # 선택된 노드가 문장이고 body 속성이 있으면 현재 노드를 body에 추가
        if isinstance(new_node, ast.stmt) and hasattr(new_node, 'body'):
            new_node.body = [node] 
            if hasattr(new_node, 'orelse'):
                new_node.orelse = [] 
            if hasattr(new_node, 'finalbody'):
                new_node.finalbody = []
            # 위치 정보 복사로 라인 정보 유지
            ast.copy_location(new_node, node)
            return new_node
        # `return` 문 앞에 삽입
        if isinstance(node, ast.Return):
            if isinstance(new_node, ast.Return):
                # 새 노드가 `return` 문이면 원래 노드를 대체
                return new_node
            else:
                # 새 노드를 원래 노드 앞에 삽입
                return [new_node, node]
        # 기본: 원래 노드 뒤에 새 노드 삽입
        return [node, new_node]

    # 현재 노드 삭제
    def delete(self, node: ast.AST) -> None:
        # 노드에 `body`, `orelse`, `finalbody` 속성이 있는지 확인
        branches = [attr for attr in ['body', 'orelse', 'finalbody'] if hasattr(node, attr) and getattr(node, attr)]
        if branches:
            branch = random.choice(branches)  # 랜덤하게 선택된 속성
            new_node = getattr(node, branch)  # 선택된 속성의 하위 노드 반환
            return new_node
        # 노드가 `stmt`(문장)이면 빈 블록을 방지하기 위해 `pass` 문으로 대체
        if isinstance(node, ast.stmt):
            new_node = ast.Pass()  # `pass` 문 생성
            ast.copy_location(new_node, node)
            return new_node
        # 기본적으로 노드를 삭제 (None 반환)
        return None

    # 노드 변이 후 변이된 트리를 반환
    def mutate(self, tree: ast.AST) -> ast.AST:
        assert isinstance(tree, ast.AST)  # 입력이 AST인지 확인
        tree = copy.deepcopy(tree)  # 원본 트리를 깊은 복사
        # 변이에 사용할 소스 문장이 없는 경우, 트리에서 문장을 수집
        if not self.source:
            self.source = all_statements(tree)
        # 모든 노드의 `mutate_me` 속성을 초기화 (False 설정)
        for node in ast.walk(tree):
            node.mutate_me = False  # type: ignore
        # 변이할 노드를 선택하고 `mutate_me` 속성을 True로 설정
        node = self.node_to_be_mutated(tree)
        node.mutate_me = True  # type: ignore
        self.mutations = 0  # 변이 횟수 초기화
        # NodeTransformer의 visit() 호출 → 변이 실행
        tree = self.visit(tree)
        # 변이가 적용되지 않은 경우 경고 메시지 출력
        if self.mutations == 0:
            warnings.warn("No mutations found")
        # 누락된 위치 정보를 복구
        ast.fix_missing_locations(tree)
        return tree  # 변이된 AST 반환