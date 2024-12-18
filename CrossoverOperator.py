from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
import random

class CrossoverOperator:
    
    # 모듈과 클래스 정의는 교차 대상에서 제외
    SKIP_LIST = {ast.Module, ast.ClassDef}
    
    def __init__(self, log: Union[bool, int] = False):
        self.log = log

	# 두 문장 리스트(body_1, body_2)를 교차
    def cross_bodies(self, body_1: List[ast.AST], body_2: List[ast.AST]) -> Tuple[List[ast.AST], List[ast.AST]]:
        # 입력으로 받은 body_1과 body_2가 리스트인지 확인
        assert isinstance(body_1, list), "body_1은 리스트여야 합니다."
        assert isinstance(body_2, list), "body_2는 리스트여야 합니다."
        # 각 문장 리스트의 중간 지점을 계산
        crossover_point_1 = len(body_1) // 2  # body_1의 중간 지점
        crossover_point_2 = len(body_2) // 2  # body_2의 중간 지점
        # 교차된 두 개의 새로운 문장 리스트를 생성하여 반환
        return (body_1[:crossover_point_1] + body_2[crossover_point_2:],
                body_2[:crossover_point_2] + body_1[crossover_point_1:])

    # 주어진 AST 노드가 교차 가능한 문장 리스트를 포함하는지 확인
    def can_cross(self, tree: ast.AST, body_attr: str = 'body') -> bool:
        # SKIP_LIST에 포함된 노드인지 확인 (모듈이나 클래스는 제외)
        if any(isinstance(tree, cls) for cls in self.SKIP_LIST):
            return False  # 교차 불가능
        # body 속성이 존재하고, 문장 리스트의 길이가 2 이상인지 확인
        body = getattr(tree, body_attr, [])
        return body is not None and len(body) >= 2

    # 두 AST `t1`과 `t2`의 `body_attr` 속성에 대해 Crossover를 수행
    def crossover_attr(self, t1: ast.AST, t2: ast.AST, body_attr: str) -> bool:
        # 입력 검증
        assert isinstance(t1, ast.AST)
        assert isinstance(t2, ast.AST)
        assert isinstance(body_attr, str)
        # body_attr가 존재하지 않으면 실패
        if not getattr(t1, body_attr, None) or not getattr(t2, body_attr, None):
            return False
        # 첫 번째 교차 시도: 두 트리의 가지를 바로 교차
        if self.crossover_branches(t1, t2):
            return True
        if self.log > 1:  # 로깅 활성화 시 출력
            print(f"Checking {t1}.{body_attr} x {t2}.{body_attr}")
        body_1 = getattr(t1, body_attr)  # t1의 body 속성
        body_2 = getattr(t2, body_attr)  # t2의 body 속성
        # 두 body가 교차 가능한 경우
        if self.can_cross(t1, body_attr) and self.can_cross(t2, body_attr):
            if self.log:
                print(f"Crossing {t1}.{body_attr} x {t2}.{body_attr}")
            # 문장 리스트를 교차하고 속성을 업데이트
            new_body_1, new_body_2 = self.cross_bodies(body_1, body_2)
            setattr(t1, body_attr, new_body_1)
            setattr(t2, body_attr, new_body_2)
            return True
        # 전략 1: 같은 이름을 가진 함수/클래스 쌍을 찾아 교차
        for child_1 in body_1:
            if hasattr(child_1, 'name'):  # 이름 속성이 있는 노드만 검사
                for child_2 in body_2:
                    if hasattr(child_2, 'name') and child_1.name == child_2.name:
                        if self.crossover_attr(child_1, child_2, body_attr):
                            return True
        # 전략 2: 랜덤하게 선택된 요소 쌍에 대해 교차 시도
        for child_1 in random.sample(body_1, len(body_1)):
            for child_2 in random.sample(body_2, len(body_2)):
                if self.crossover_attr(child_1, child_2, body_attr):
                    return True
        return False

    # if-else 노드에서 Crossover 연산
    def crossover_branches(self, t1: ast.AST, t2: ast.AST) -> bool:
        # 입력 노드가 AST 객체인지 확인
        assert isinstance(t1, ast.AST)
        assert isinstance(t2, ast.AST)
        # t1과 t2가 `body`와 `orelse` 속성을 가지고 있는지 확인
        if (hasattr(t1, 'body') and hasattr(t1, 'orelse') and
            hasattr(t2, 'body') and hasattr(t2, 'orelse')):
            # t1과 t2를 ast.If로 타입 변환 (mypy 검사를 위해 필요)
            t1 = cast(ast.If, t1)
            t2 = cast(ast.If, t2)
            # 로깅 활성화 시 출력
            if self.log:
                print(f"Crossing branches {t1} x {t2}")
            # body와 orelse를 교차
            t1.body, t1.orelse, t2.body, t2.orelse = t2.orelse, t2.body, t1.orelse, t1.body
            return True  # 교차 성공
        return False  # 교차 실패

    def crossover(self, t1: ast.AST, t2: ast.AST) -> Tuple[ast.AST, ast.AST]:
        assert isinstance(t1, ast.AST)
        assert isinstance(t2, ast.AST)
        for body_attr in ['body', 'orelse', 'finalbody']:
            if self.crossover_attr(t1, t2, body_attr):
                return t1, t2
        raise CrossoverError("No crossover found")


class CrossoverError(ValueError):
    pass