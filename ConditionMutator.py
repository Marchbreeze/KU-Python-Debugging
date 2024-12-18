from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
import copy
import random
from StatementMutator import StatementMutator
from ConditionVisitor import all_conditions

class ConditionMutator(StatementMutator):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)  # 부모 클래스의 생성자 호출
        # 소스 코드에서 조건식 수집
        self.conditions = all_conditions(self.source)
        if self.log:  # 로깅이 활성화된 경우
            print("Found conditions", [ast.unparse(cond).strip() for cond in self.conditions])

	# 소스 코드에서 조건식 중 하나를 랜덤하게 선택하여 반환
    def choose_condition(self) -> ast.expr:
        return copy.deepcopy(random.choice(self.conditions))

	# 조건식 변이에 사용할 논리 연산자를 랜덤하게 선택
    def choose_bool_op(self) -> str:
        return random.choice(['set', 'not', 'and', 'or'])
        
	# 제어 구조의 조건식을 변이
    def swap(self, node: ast.AST) -> ast.AST:
        if not hasattr(node, 'test'):  # 조건식이 없는 노드는 처리하지 않음
            return super().swap(node)  # 기본 swap 메서드 호출
        node = cast(ast.If, node)  # 노드를 `if` 문으로 캐스팅

        # 새로운 조건식 선택
        cond = self.choose_condition()
        new_test = None  # 변이된 조건식 초기화

        # 논리 연산자 또는 조건 대체 선택
        choice = self.choose_bool_op()

        if choice == 'set':  # 조건식 대체
            new_test = cond
        elif choice == 'not':  # 기존 조건식에 'not' 적용
            new_test = ast.UnaryOp(op=ast.Not(), operand=node.test)
        elif choice == 'and':  # 기존 조건식과 새로운 조건식을 'and'로 결합
            new_test = ast.BoolOp(op=ast.And(), values=[cond, node.test])
        elif choice == 'or':  # 기존 조건식과 새로운 조건식을 'or'로 결합
            new_test = ast.BoolOp(op=ast.Or(), values=[cond, node.test])
        else:
            raise ValueError("Unknown boolean operand")  # 알 수 없는 연산자 처리

        if new_test:  # 새로운 조건식이 생성된 경우
            ast.copy_location(new_test, node)  # 위치 정보 복사
            node.test = new_test  # 기존 조건식을 새로운 조건식으로 교체

        return node  # 변이된 노드 반환


# 활용
# condition_repairer = Repairer(html_debugger,
#                               mutator_class=ConditionMutator,
#                               log=2)