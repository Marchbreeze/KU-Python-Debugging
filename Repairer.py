from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import ast
import traceback
import warnings
import copy
import inspect
import random
from StatementVisitor import all_statements_and_functions, all_statements
from PrintContent import print_content
from StackInspector import StackInspector
from RankingDebugger import RankingDebugger
from StatementMutator import StatementMutator
from CrossoverOperator import CrossoverOperator, CrossoverError
from DefinitionVisitor import DefinitionVisitor
# from Middle import middle, middle_test, MIDDLE_PASSING_TESTCASES, MIDDLE_FAILING_TESTCASES
# from OchiaiDebugger import OchiaiDebugger

WEIGHT_PASSING = 0.99
WEIGHT_FAILING = 0.01
POPULATION_SIZE = 40

class Repairer(StackInspector):
    def __init__(self, 
				debugger: RankingDebugger, *,
                targets: Optional[List[Any]] = None, # 수리할 함수/모듈 목록
                sources: Optional[List[Any]] = None, # 수리에서 사용할 함수/모듈 목록
                log: Union[bool, int] = False,
                mutator_class: Type = StatementMutator, # 변이를 수행할 클래스
                crossover_class: Type = CrossoverOperator, # 교차를 수행할 클래스
                globals: Optional[Dict[str, Any]] = None):

        # 입력된 디버거가 RankingDebugger인지 검증
        assert isinstance(debugger, RankingDebugger)
        self.debugger = debugger  # 통계적 디버거 설정
        self.log = log  # 로깅 설정

        # 수리 대상 설정: targets가 없으면 기본 함수 목록 설정
        if targets is None:
            targets = self.default_functions()
        if not targets:  # targets가 비어있으면 오류 발생
            raise ValueError("No targets to repair")

        # 수리 소스 설정: sources가 없으면 기본 함수 목록 설정
        if sources is None:
            sources = self.default_functions()
        if not sources:  # sources가 비어있으면 오류 발생
            raise ValueError("No sources to take repairs from")

        # 디버거에서 함수 진입점 검증
        if self.debugger.function() is None:
            raise ValueError("Multiple entry points observed")

        # 수리 대상 코드와 소스 코드를 AST로 변환
        self.target_tree: ast.AST = self.parse(targets)  # 수리할 대상 코드
        self.source_tree: ast.AST = self.parse(sources)  # 수리에 사용할 코드

        # 수리 대상 코드 출력 (디버깅용)
        self.log_tree("Target code to be repaired:", self.target_tree)
        if ast.dump(self.target_tree) != ast.dump(self.source_tree):
            self.log_tree("Source code to take repairs from:", self.source_tree)

        # 적합도 캐시: 수리 과정에서 계산된 적합도를 저장
        self.fitness_cache: Dict[str, float] = {}

        # 변이, 교차 도구 설정
        self.mutator: StatementMutator = mutator_class(
            source=all_statements(self.source_tree),  # 소스 코드의 모든 문장 목록
            suspiciousness_func=self.debugger.suspiciousness,  # 결함 위치 의심 점수
            log=(self.log >= 3))  # 로깅 수준
        self.crossover: CrossoverOperator = crossover_class(log=(self.log >= 3))

        # globals 설정: 코드 실행 시 사용할 전역 변수
        if globals is None:
            globals = self.caller_globals()  # 호출자의 globals 값 가져오기
        self.globals = globals

    # 주어진 함수의 소스 코드를 반환
    def getsource(self, item: Union[str, Any]) -> str:
        if isinstance(item, str):  # 문자열이면
            item = self.globals[item]  # globals에서 객체 가져오기
        return inspect.getsource(item)  # 객체의 소스 코드 반환

    #  수리 대상 함수 목록을 반환 (test 포함 제외)
    def default_functions(self) -> List[Callable]:
            # 이름이 'test'로 시작하거나 끝나는지 확인
        def is_test(name: str) -> bool:
            return name.startswith('test') or name.endswith('test')
        # 커버된 함수 중 테스트 함수가 아닌 함수만 반환
        return [func for func in self.debugger.covered_functions()
                if not is_test(func.__name__)]

    # tree를 소스 코드 형태로 출력
    def log_tree(self, description: str, tree: Any) -> None:
        if self.log:  # 로깅 활성화된 경우
            print(description)
            print_content(ast.unparse(tree), '.py')  # AST를 소스 코드로 변환하여 출력
            print()
            print()

    # 주어진 항목 목록을 단일 AST 트리로 파싱
    def parse(self, items: List[Any]) -> ast.AST:
        tree = ast.parse("")  # 빈 AST 트리 생성
        for item in items:
            if isinstance(item, str):  # 문자열이면
                item = self.globals[item]  # globals에서 객체 가져오기
            # 소스 코드 라인과 시작 라인 번호 가져오기
            item_lines, item_first_lineno = inspect.getsourcelines(item)
            try:
                # 소스 코드 라인을 AST 트리로 파싱
                item_tree = ast.parse("".join(item_lines))
            except IndentationError:
                # 중첩 함수 등으로 파싱 실패 시 경고 출력
                warnings.warn(f"Can't parse {item.__name__}")
                continue
            # AST 라인 번호를 원래 소스 코드의 라인 번호에 맞게 조정
            ast.increment_lineno(item_tree, item_first_lineno - 1)
            tree.body += item_tree.body  # 합쳐진 트리의 body에 추가
        return tree

    # 주어진 테스트 집합을 실행
    def run_test_set(self, test_set: str, validate: bool = False) -> int:
        passed = 0  # 통과한 테스트 수 초기화
        collectors = self.debugger.collectors[test_set]  # 테스트 케이스 수집기 목록
        function = self.debugger.function()  # 디버거에서 함수 가져오기
        assert function is not None  # 함수가 None이 아닌지 확인
        for c in collectors:  # 테스트 케이스마다 실행
            if self.log >= 4:  # 로그 수준이 4 이상이면 테스트 시작 메시지 출력
                print(f"Testing {c.id()}...", end="")
            try:
                # 테스트 케이스 실행: 함수에 테스트 케이스의 인자 전달
                function(**c.args())
            except Exception as err:
                # 테스트 실패 시 처리
                if self.log >= 4:  # 로그 수준이 4 이상이면 실패 메시지 출력
                    print(f"failed ({err.__class__.__name__})")
                # `validate`가 True이고, 통과해야 할 테스트(PASS)가 실패한 경우 오류 발생
                if validate and test_set == self.debugger.PASS:
                    raise err.__class__(
                        f"{c.id()} should have passed, but failed")
                continue  # 다음 테스트 케이스로 이동
            passed += 1  # 테스트 통과 수 증가
            if self.log >= 4:  # 로그 수준이 4 이상이면 통과 메시지 출력
                print("passed")
            # `validate`가 True이고, 실패해야 할 테스트(FAIL)가 통과한 경우 오류 발생
            if validate and test_set == self.debugger.FAIL:
                raise FailureNotReproducedError(
                    f"{c.id()} should have failed, but passed")
        return passed  # 통과한 테스트 수 반환

    # 주어진 테스트 집합의 가중치(Weight)를 반환
    def weight(self, test_set: str) -> float:
        return {
            self.debugger.PASS: WEIGHT_PASSING,  # PASS 테스트에 대한 가중치
            self.debugger.FAIL: WEIGHT_FAILING   # FAIL 테스트에 대한 가중치
        }[test_set]

    # 테스트를 실행하고, 가중치를 적용한 적합도(fitness)를 반환
    def run_tests(self, validate: bool = False) -> float:
        fitness = 0.0  # 초기 적합도 점수
        # PASS 및 FAIL 테스트 실행
        for test_set in [self.debugger.PASS, self.debugger.FAIL]:
            passed = self.run_test_set(test_set, validate=validate)  # 통과한 테스트 수
            ratio = passed / len(self.debugger.collectors[test_set])  # 통과 비율 계산
            fitness += self.weight(test_set) * ratio  # 가중치를 곱해 적합도 점수 계산
        return fitness  # 최종 적합도 점수 반환

    # 테스트 결과를 검증
    def validate(self) -> None:
        fitness = self.run_tests(validate=True)  # 검증 모드에서 테스트 실행
        assert fitness == self.weight(self.debugger.PASS)  # PASS의 가중치와 적합도가 일치하는지 확인

    # 주어진 수리 후보(tree)의 적합도(fitness)를 계산
    def fitness(self, tree: ast.AST) -> float:
        # AST를 문자열로 변환해 캐시 키 생성
        key = cast(str, ast.dump(tree))
        if key in self.fitness_cache:  # 캐시에 이미 결과가 있으면 반환
            return self.fitness_cache[key]
        # 원래 정의를 저장
        original_defs: Dict[str, Any] = {}
        for name in self.toplevel_defs(tree):  # 최상위 함수/클래스 정의 찾기
            if name in self.globals:  # 정의가 globals에 존재하면 저장
                original_defs[name] = self.globals[name]
            else:
                warnings.warn(f"Couldn't find definition of {repr(name)}")
        assert original_defs, f"Couldn't find any definition"  # 정의가 없으면 오류 발생
        if self.log >= 3:  # 로그 출력
            print("Repair candidate:")
            print_content(ast.unparse(tree), '.py')  # AST를 소스 코드로 출력
            print()
        # 수리 후보를 컴파일
        try:
            code = compile(cast(ast.Module, tree), '<Repairer>', 'exec')
        except ValueError:  # 컴파일 오류 발생 시
            code = None
        if code is None:  # 컴파일 실패 시 적합도 0.0 반환
            if self.log >= 3:
                print(f"Fitness = 0.0 (compilation error)")
            fitness = 0.0
            return fitness
        # 컴파일된 코드를 실행해 새 정의를 `self.globals`에 설정
        exec(code, self.globals)
        # 테스트에서 호출될 함수의 네임스페이스(`__globals__`)에 새 정의 설정
        function = self.debugger.function()
        assert function is not None
        assert hasattr(function, '__globals__')
        for name in original_defs:  # 수정된 정의를 함수의 네임스페이스에 복사
            function.__globals__[name] = self.globals[name]  # type: ignore
        # 테스트를 실행해 적합도 점수 계산
        fitness = self.run_tests(validate=False)
        # 원래 정의로 복원
        for name in original_defs:
            function.__globals__[name] = original_defs[name]  # type: ignore
            self.globals[name] = original_defs[name]
        if self.log >= 3:  # 로그 출력
            print(f"Fitness = {fitness}")
        # 적합도 결과를 캐시에 저장
        self.fitness_cache[key] = fitness
        return fitness

    # tree에서 최상위 함수 및 클래스 정의의 이름 목록을 반환
    def toplevel_defs(self, tree: ast.AST) -> List[str]:
        visitor = DefinitionVisitor()  # DefinitionVisitor 인스턴스 생성
        visitor.visit(tree)  # AST를 방문하여 정의된 이름 수집
        assert hasattr(visitor, 'definitions')  # 'definitions' 속성이 존재하는지 확인
        return visitor.definitions  # 수집된 정의 목록 반환

    # 초기 개체군을 생성
    def initial_population(self, size: int) -> List[ast.AST]:
        # AST(추상 구문 트리)로 이루어진 개체군 목록 반환
        return [self.target_tree] + [self.mutator.mutate(copy.deepcopy(self.target_tree)) for i in range(size - 1)]

    # 결함이 있는 프로그램을 수리
    def repair(self, population_size: int = POPULATION_SIZE, iterations: int = 100) -> Tuple[ast.AST, float]:
        # 테스트 실행 결과 검증
        self.validate()
        # 초기 개체군 생성
        population = self.initial_population(population_size)
        last_key = ast.dump(self.target_tree)  # 마지막 최고 코드 키 저장
        # 진화 알고리즘 실행
        for iteration in range(iterations):
            population = self.evolve(population)  # 개체군 진화
            best_tree = population[0]  # 최고 적합도 수리안
            fitness = self.fitness(best_tree)  # 적합도 계산
            # 로그 출력 (진행 상황 및 적합도)
            if self.log:
                print(f"Evolving population: "
                    f"iteration{iteration:4}/{iterations} "
                    f"fitness = {fitness:.5}   \r", end="")
            # 로그 출력 (새로운 최고 코드 발견 시)
            if self.log >= 2:
                best_key = ast.dump(best_tree)
                if best_key != last_key:
                    print()
                    print()
                    self.log_tree(f"New best code (fitness = {fitness}):",
                                best_tree)
                    last_key = best_key
            # 적합도가 1.0이면 조기 종료
            if fitness >= 1.0:
                break
        # 최종 결과 로그 출력
        if self.log:
            print()
        if self.log and self.log < 2:
            self.log_tree(f"Best code (fitness = {fitness}):", best_tree)
        return best_tree, fitness  # 수리된 코드와 적합도 반환

    # 개체군 진화 (교차와 변이를 통해 새 후보를 생성하고, 적합도에 따라 상위 개체군만 유지)
    def evolve(self, population: List[ast.AST]) -> List[ast.AST]:
        # 개체군의 크기
        n = len(population)
        # 부모 교차를 통해 자식 후보 생성
        offspring: List[ast.AST] = []
        while len(offspring) < n:
            # 부모 개체 랜덤 선택 및 복사
            parent_1 = copy.deepcopy(random.choice(population))
            parent_2 = copy.deepcopy(random.choice(population))
            try:
                # 부모 교차 시도
                self.crossover.crossover(parent_1, parent_2)
            except CrossoverError:
                pass  # 교차 실패 시 부모 그대로 유지
            offspring += [parent_1, parent_2]  # 교차 결과 추가
        # 자식 후보들에 대해 변이(Mutation) 적용
        offspring = [self.mutator.mutate(tree) for tree in offspring]
        # 자식 후보를 기존 개체군에 추가
        population += offspring
        # 적합도에 따라 개체군 정렬 (내림차순)
        population.sort(key=self.fitness_key, reverse=True)
        # 상위 n개의 개체만 유지 (기존 개체군 크기 유지)
        population = population[:n]
        return population  # 진화된 개체군 반환

    # 개체군 정렬 시 사용할 키 값을 반환
    def fitness_key(self, tree: ast.AST) -> Tuple[float, int]:
        # 트리 크기 계산: AST의 모든 노드 개수를 세어 트리 크기 구하기
        tree_size = len([node for node in ast.walk(tree)])
        # 반환 값: (적합도, 트리 크기의 음수)
        return (self.fitness(tree), -tree_size)


class FailureNotReproducedError(ValueError):
    pass


# middle_debugger = OchiaiDebugger()
# for x, y, z in MIDDLE_PASSING_TESTCASES + MIDDLE_FAILING_TESTCASES:
#     with middle_debugger:
#         middle_test(x, y, z)

# repairer = Repairer(middle_debugger, log=True)
# best_tree, fitness = repairer.repair()