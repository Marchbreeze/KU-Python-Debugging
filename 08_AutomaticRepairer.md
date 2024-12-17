## 0. Automatic Code Repairer

- 자동 코드 수리
    - 프로그램에서 오류(결함)가 발생했을 때, 해당 오류를 자동으로 수정하는 기술
    - Mutation (변이) : 프로그램 코드의 일부를 삽입, 변경, 또는 삭제하는 방식으로 체계적으로 변경을 시도
    - Diagnosis (진단) : 수리를 위해서는 원인 분석이 중요
        1. 인과성 (Causality): 결함이 어떻게 실패를 유발했는지를 설명
        2. 부정확성 (Incorrectness): 해당 결함이 왜 잘못되었는지를 설명

- 유전 최적화 (Genetic Optimization)
    - 자연 선택의 원리에서 영감을 받은 메타휴리스틱 방법, 최적의 해결책을 찾기 위해 후보 솔루션을 진화시키는 과정
    - 자동 코드 수리에 적용:
        1. Test Suite 준비
            - 실패하는 테스트와 성공하는 테스트를 포함하는 테스트 스위트를 사용
            - 후보 수정안이 올바른지를 검증하는 기준
        2. 결합 위치 파악
            - 수정이 필요한 코드 위치 파악
        3. 후보 수정안 생성
            - 코드의 일부를 변이 (추가, 변경, 삭제)하거나 교차시켜 다양한 수정안 후보 생성
        4. 적합도 평가
            - 생성된 수정안 중에서 테스트를 가장 많이 통과하는 후보를 찾아 적합도(fitness)를 평가
        5. 진화 및 반복
            - 가장 적합한 후보들을 진화시켜 새로운 수정안을 계속 생성하고 평가

## 1. Test Suite

- **테스트 스위트**가 크고 철저할수록 자동 수리의 결과물인 수정안의 **품질이 높아짐**
- 테스트 스위트가 크면 그만큼 **추가 비용**이 발생할 수 있음
- ex.
    
    ```python
    from StatisticalDebugger import MIDDLE_PASSING_TESTCASES, MIDDLE_FAILING_TESTCASES
    ```
    
- ex.
    
    ```python
    from ExpectError import ExpectError
    
    def middle_test(x: int, y: int, z: int) -> None:
        m = middle(x, y, z)
        assert m == sorted([x, y, z])[1]
        
    with ExpectError():
        middle_test(2, 1, 3)
    ```
    
    ![2024-12-17_15-22-04.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/324153f7-7cb2-4abc-9a70-d47fbccce0d5/2024-12-17_15-22-04.jpg)
    

## 2. Locating the Defect

- 잠재적 결함 위치 찾기
    - 자동 코드 수리를 위해서는 결함이 있을 가능성이 높은 코드 위치를 식별하는 것이 중요
    - 통계적 디버깅(statistical debugging) 기법을 활용

- ex.
    
    ```python
    from StatisticalDebugger import OchiaiDebugger, RankingDebugger
    
    middle_debugger = OchiaiDebugger()
    
    for x, y, z in MIDDLE_PASSING_TESTCASES + MIDDLE_FAILING_TESTCASES:
        with middle_debugger:
            middle_test(x, y, z)
    
    middle_debugger
    ```
    
    ![2024-12-17_15-23-59.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/01fe2e7f-dc0b-4bf5-a160-7bc3b054d044/2024-12-17_15-23-59.jpg)
    
    ```python
    # 가장 의심스러운 라인?
    location = middle_debugger.rank()[0]
    (func_name, lineno) = location
    lines, first_lineno = inspect.getsourcelines(middle)
    print(lineno, end="")
    print_content(lines[lineno - first_lineno], '.py')
    ```
    
    ![2024-12-17_15-24-34.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/bec7d7a0-21cf-4907-a150-b5515e4764f2/2024-12-17_15-24-34.jpg)
    
    ```python
    # 의심 수준?
    middle_debugger.suspiciousness(location)
    ```
    
    ![2024-12-17_15-24-55.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/11aa250a-273c-48a4-b58b-66860fb4101b/2024-12-17_15-24-55.jpg)
    

## 3. Random Code Mutations

- 코드를 처음부터 생성하는 것은 현실적으로 비효율적 - 조합의 수가 너무 많음
- 코드를 완전히 새로 생성하는 대신, 기존 코드를 바탕으로 일부를 수정(변이)하는 것이 더 효율적

1. 코드 재사용 원칙
    - Plastic Surgery Hypothesis : 한 프로그램의 특정 부분에 오류가 있다면, 같은 프로그램 내의 다른 부분은 올바른 동작을 구현하고 있을 가능성이 높다
2. 구조 기반 접근
    - 코드 변이를 수행할 때 텍스트(문자열) 기반 대신 구조적 표현인 추상 구문 트리(AST)를 사용
    - AST를 사용하면 구문 오류(lexical, syntactical errors)를 피할 수 있음

- ex.
    
    ```python
    import ast
    import inspect
    from bookutils import print_content, show_ast
    
    def middle_tree() -> ast.AST:
        return ast.parse(inspect.getsource(middle))
    
    show_ast(middle_tree())
    ```
    
    ![2024-12-17_15-30-01.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/88015961-acb2-4e3a-84f7-81b342e2b6fe/2024-12-17_15-30-01.jpg)
    
    ```python
    print(ast.dump(middle_tree()))
    ```
    
    >  Module(body=[FunctionDef(name='middle', args=arguments(posonlyargs=[], args=[arg(arg='x'), arg(arg='y'), arg(arg='z')], kwonlyargs=[], kw_defaults=[], defaults=[]), body=[If(test=Compare(left=Name(id='y', ctx=Load()), ops=[Lt()], comparators=[Name(id='z', ctx=Load())]), body=[If(test=Compare(left=Name(id='x', ctx=Load()), ops=[Lt()], comparators=[Name(id='y', ctx=Load())]), body=[Return(value=Name(id='y', ctx=Load()))], orelse=[If(test=Compare(left=Name(id='x', ctx=Load()), ops=[Lt()], comparators=[Name(id='z', ctx=Load())]), body=[Return(value=Name(id='y', ctx=Load()))], orelse=[])])], orelse=[If(test=Compare(left=Name(id='x', ctx=Load()), ops=[Gt()], comparators=[Name(id='y', ctx=Load())]), body=[Return(value=Name(id='y', ctx=Load()))], orelse=[If(test=Compare(left=Name(id='x', ctx=Load()), ops=[Gt()], comparators=[Name(id='z', ctx=Load())]), body=[Return(value=Name(id='x', ctx=Load()))], orelse=[])])]), Return(value=Name(id='z', ctx=Load()))], decorator_list=[])], type_ignores=[])
    
    - FunctionDef: 함수 정의 노드
    - arguments: 함수 인자 목록
    - If: test(조건식), body(참일때 코드블록), orelse(거짓일때 코드블록)
    - Return: 반환 문장

### (1) Statement Visitor

- AST의 문장(Statements)을 수집하기 위한 방법 - ast 모듈의 NodeVisitor를 활용하여 구현
    1. AST를 순회하며 함수 정의 (FunctionDef) 노드 탐색
    2. 함수 정의 내 모든 문장(statement)를 리스트에 추가

- StatementVisitor
    
    ```python
    from ast import NodeVisitor
    
    class StatementVisitor(NodeVisitor):
        """AST의 함수 정의 내 모든 문장을 방문하는 클래스"""
    
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
    ```
    

- 문장, 함수명 수집 방법
    
    ```python
    # tree에서 모든 문장과 해당 문장이 속한 함수명을 반환
    def all_statements_and_functions(tree: ast.AST, tp: Optional[Type] = None) -> List[Tuple[ast.AST, str]]:
        
        visitor = StatementVisitor()  # StatementVisitor 인스턴스 생성
        visitor.visit(tree)           # AST 방문 시작
        statements = visitor.statements  # 수집된 문장과 함수명
    
        if tp is not None:
            # 특정 클래스(tp)에 해당하는 문장만 필터링
            statements = [s for s in statements if isinstance(s[0], tp)]
    
        return statements  # 필터링된 문장과 함수명 반환
    ```
    
    ```python
    all_statements(middle_tree(), ast.Return)
    ```
    
    ![2024-12-17_16-40-04.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/c23a3d11-1372-4505-896e-3f1a8cce4802/2024-12-17_16-40-04.jpg)
    
- 문장만 수집
    
    ```python
    # tree에서 모든 문장만 반환
    def all_statements(tree: ast.AST, tp: Optional[Type] = None) -> List[ast.AST]:
        # all_statements_and_functions를 호출해 문장만 추출
        return [stmt for stmt, func_name in all_statements_and_functions(tree, tp)]
    ```
    
    ![2024-12-17_16-40-16.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/190a594e-1b8e-4b92-9b3c-c9c1bded0384/2024-12-17_16-40-16.jpg)
    

- 랜덤으로 문장 출력도 가능
    
    ```python
    import random
    
    random_node = random.choice(all_statements(middle_tree()))
    ast.unparse(random_node)
    ```
    
    ![2024-12-17_16-41-27.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/f56e34e9-1f3f-4bab-8560-48f9d47f8b60/2024-12-17_16-41-27.jpg)
    

### (2) Statement Mutator

- 코드 내 문장을 **변이**시켜 수정안 후보를 생성하는 작업 - ast 모듈의 Node Transformer 클래스를 활용하여 구현
- 특정 문장(statement)을 찾아 **삭제**, **대체**, **변이**하는 연산을 수행
- AST 기반으로 수행되므로, 문법적 오류를 최소화하고 안전하게 코드 구조를 수정

- Statement Mutator
    
    ```python
    from ast import NodeTransformer
    
    class StatementMutator(NodeTransformer):
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
    ```
    

- AST 노드의 의심수준 확인
    
    ```python
    import warnings
    import re
    
    RE_SPACE = re.compile(r'\s+')
    NODE_MAX_LENGTH = 20
    
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
    ```
    

- 변이할 AST 노드(문장)를 선택
    - 노드의 의심도(suspiciousness)를 기반으로 가중 랜덤 선택을 수행
    - 각 노드의 의심도는 변이 우선순위를 결정하는 가중치로 사용
    
    ```python
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
    ```
    

- visit() 메서드의 역할과 변이 방법을 선택 및 적용
    
    ```python
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
    ```
    

1. 교체 변이 연산
    - 랜덤한 문장을 코드에서 가져와 기존 노드를 교체하며, 일부 조정을 통해 문법적으로 올바른 형태를 유지
        
        ```python
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
        ```
        

1. 추가 변이 연산
    - 랜덤한 문장을 선택해 현재 노드의 앞 또는 뒤에 삽입
    - return 문일 경우에는 문법적 의미를 유지하기 위해 삽입 위치를 조정
        
        ```python
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
        ```
        

1. 삭제 변이 연산
    - 노드를 삭제하되 문법적 오류를 방지하기 위해, 특정 상황에서 pass 문으로 대체하거나 하위 블록을 유지하는 방식을 사용
        
        ```python
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
        ```
        

- 변이 전체 흐름 실행 메서드
    
    ```python
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
    ```
    

- ex.
    
    ```python
    mutator = StatementMutator(log=True)
    
    # 10줄에 대한 변이
    for i in range(10):
        new_tree = mutator.mutate(middle_tree())
    ```
    
    ![2024-12-17_17-28-50.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/2cdb3434-89f7-44c0-8fbf-51cb048177ca/2024-12-17_17-28-50.jpg)
    
    ```python
    print_content(ast.unparse(new_tree), '.py')
    ```
    
    ![2024-12-17_17-29-09.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/665d8b00-d027-4cd2-8868-cedf629b4e74/2024-12-17_17-29-09.jpg)
    

## 4. Fitness

### (1) Fitness Calculation

- 적합도 (Fitness)
    - 변이된 코드 후보가 테스트 스위트에서 얼마나 많은 테스트 케이스를 통과했는지를 평가하는 값
    - 이전에 통과한 테스트 케이스 & 실패한 테스트 케이스 모두 사용
    
- ex. middle() 함수의 **변이된 코드 후보**의 적합도(fitness)를 계산
    - 기존 통과 테스트와 실패 테스트의 중요도 설정
        
        ```python
        WEIGHT_PASSING = 0.99
        WEIGHT_FAILING = 0.01
        ```
        
    - 적합도 평가
        
        ```python
        # 변이된 함수의 적합도 평가
        def middle_fitness(tree: ast.AST) -> float:
            original_middle = middle  # 원래 middle 함수 백업
        
            # AST를 컴파일하고 실행
            try:
                code = compile(cast(ast.Module, tree), '<fitness>', 'exec')
            except ValueError:
                return 0  # 컴파일 오류 시 적합도 0 반환
        
            exec(code, globals())  # 변이된 코드 실행
        
            passing_passed = 0
            failing_passed = 0
        
            # 기존 통과 테스트 실행
            for x, y, z in MIDDLE_PASSING_TESTCASES:
                try:
                    middle_test(x, y, z)  # 테스트 실행
                    passing_passed += 1  # 통과한 경우 카운트 증가
                except AssertionError:
                    pass
        
            passing_ratio = passing_passed / len(MIDDLE_PASSING_TESTCASES)
        
            # 기존 실패 테스트 실행
            for x, y, z in MIDDLE_FAILING_TESTCASES:
                try:
                    middle_test(x, y, z)  # 테스트 실행
                    failing_passed += 1  # 통과한 경우 카운트 증가
                except AssertionError:
                    pass
        
            failing_ratio = failing_passed / len(MIDDLE_FAILING_TESTCASES)
        
            # 적합도 계산: 가중치를 적용한 통과 및 실패 비율 합산
            fitness = (WEIGHT_PASSING * passing_ratio + WEIGHT_FAILING * failing_ratio)
        
            # 원래 middle 함수로 복원
            globals()['middle'] = original_middle
            return fitness
        ```
        
    - 적용
        
        ```python
        middle_fitness(middle_tree())
        ```
        
        ![2024-12-17_17-39-57.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/33351fcc-af44-4f35-92e4-8319d67fc803/2024-12-17_17-39-57.jpg)
        

### (2) Population

- 개체군 (Population)
    - 코드의 수정안 후보(fix candidates)들의 집합
    - 개체군을 세대 단위로 관리하며, 각 세대에서 최적의 수정안을 찾기 위해 선택(selection), 변이(mutation), 교차(crossover) 연산을 반복적으로 수행
- 개체군 크기
    - 한 세대에서 유지할 **수정안 후보의 수**
    - Le Goues et al. (2012)의 연구를 참고해 **40개**를 개체군 크기로 선택

- **개체군의 정렬**과 **적합도 평가**를 통해 수정안 후보들의 품질을 비교
    1. 개체군 초기화
        
        ```python
        POPULATION_SIZE = 40
        middle_mutator = StatementMutator()
        
        # 40개 후보 리트스 생성 (원본 + 39개의 변이된 코드)
        MIDDLE_POPULATION = [middle_tree()] + [middle_mutator.mutate(middle_tree()) for i in range(POPULATION_SIZE - 1)]
        ```
        
    2. 적합도 정렬
        
        ```python
        MIDDLE_POPULATION.sort(key=middle_fitness, reverse=True)
        ```
        
    3. 결과 비교
        
        ```python
        # 가장 높은 적합도 (낮은건 -1)
        print(ast.unparse(MIDDLE_POPULATION[0]), middle_fitness(MIDDLE_POPULATION[0]))
        ```
        
        ![2024-12-17_17-55-12.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/02a13d2d-fb11-45c7-b7c8-572a677f1550/2024-12-17_17-55-12.jpg)
        

## 5. Evolve

### (1) Evolution

- 새로운 변이된 후보를 생성하고, 적합도를 기준으로 상위 후보를 유지하여 개체군을 진화
- ex.
    
    ```python
    def evolve_middle() -> None:
    		global MIDDLE_POPULATION
    
        # 소스 문장 수집 (변이에 사용할 코드 조각들)
        source = all_statements(middle_tree())
    
        # StatementMutator 초기화
        mutator = StatementMutator(source=source)
    
        # 개체군 크기 설정
        n = len(MIDDLE_POPULATION)
    
        # 새로운 후보(offspring)를 생성
        offspring: List[ast.AST] = []
        while len(offspring) < n:
            parent = random.choice(MIDDLE_POPULATION)  # 기존 개체군에서 부모 선택
            offspring.append(mutator.mutate(parent))  # 변이를 적용해 새로운 후보 생성
    
        # 기존 개체군에 새로운 후보 추가
        MIDDLE_POPULATION += offspring
    
        # 적합도(fitness)를 기준으로 내림차순 정렬
        MIDDLE_POPULATION.sort(key=middle_fitness, reverse=True)
    
        # 상위 n개의 후보만 유지 (원래 개체군 크기로 줄이기)
        MIDDLE_POPULATION = MIDDLE_POPULATION[:n]
    ```
    
    ```python
    evolve_middle()
    tree = MIDDLE_POPULATION[0]
    print(ast.unparse(tree), middle_fitness(tree))
    ```
    
    ![2024-12-17_18-05-35.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ee4a19f9-aec7-4828-9fba-6223e5f0a75a/2024-12-17_18-05-35.jpg)
    

- 반복적 실행
    - 50번의 진화 동안 실행되며, 수정안이 완벽한 적합도(fitness = 1.0)에 도달하면 조기 종료
    
    ```python
    for i in range(50):  # 최대 50번의 진화 반복
        evolve_middle()  # 개체군을 진화시킴
        best_middle_tree = MIDDLE_POPULATION[0]  # 적합도가 가장 높은 수정안 선택
        fitness = middle_fitness(best_middle_tree)  # 해당 수정안의 적합도 평가
    
        # 현재 반복의 상태 출력
        print(f"\rIteration {i:2}: fitness = {fitness}  ", end="")
    
        # 적합도가 1.0(모든 테스트를 통과)인 경우 조기 종료
        if fitness >= 1.0:
            break
    ```
    
    ![2024-12-17_18-07-05.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/fde99c7a-96c1-4941-a893-2354b95e795b/2024-12-17_18-07-05.jpg)
    
    ```python
    print_content(ast.unparse(best_middle_tree), '.py', start_line_number=1)
    ```
    
    ![2024-12-17_18-08-35.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/73674fdc-920c-4348-a705-04da31860c4a/2024-12-17_18-08-35.jpg)
    

### (2) Simplifying

- 변이된 코드의 불필요한 문장을 제거하여 단순화(simplification)하는 과정
- ~~Delta Debugging을 사용~~
    - 결함을 유발하는 입력을 단순화하는 알고리즘
    - 불필요한 문장을 제거하면서도 여전히 최대 적합도(fitness = 1.0)를 유지하는 가장 단순한 형태의 수정안을 탐색
    - 적합도가 1.0인 경우를 실패로 간주 & 실패 조건이 지속되는 한 계속해서 불필요한 부분 제거
    - 구현
        
        ```python
        from DeltaDebugger import DeltaDebugger
        
        def test_middle_lines(lines: List[str]) -> None:
            source = "\n".join(lines)
            tree = ast.parse(source)
            assert middle_fitness(tree) < 1.0  # "Fail" only while fitness is 1.0
            
        middle_lines = ast.unparse(best_middle_tree).strip().split('\n')
        
        with DeltaDebugger() as dd:
            test_middle_lines(middle_lines)
        ```
        
        ```python
        reduced_lines = dd.min_args()['lines']
        reduced_source = "\n".join(reduced_lines)
        repaired_source = ast.unparse(ast.parse(reduced_source))
        print_content(repaired_source, '.py')
        ```
        
        ![2024-12-17_18-18-00.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/460ade58-ad0b-4c1d-849e-f8b550b4f189/2024-12-17_18-18-00.jpg)
        
- ~~ChangeDebugger을 사용~~
    - 단순화된 코드를 원본 코드와 비교하여 패치(patch)를 생성하고 출력
        
        ```python
        from ChangeDebugger import diff, print_patch 
        
        original_source = ast.unparse(ast.parse(middle_source)) 
        for patch in diff(original_source, repaired_source):
            print_patch(patch)
        ```
        
        ![2024-12-17_18-19-57.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/2dcf2b5b-7701-467d-883f-d7a4c705b525/2024-12-17_18-19-57.jpg)
        

### (3) Crossover Operator

- Crossover
    - 두 개의 부모 개체(코드 수정안)에서 일부를 교환하여 새로운 자식 개체를 생성하는 과정
    - 중간 지점을 기준으로 문장을 나누어 앞부분과 뒷부분을 교환
    - 코드 다양성을 높이고 더 나은 수정안을 탐색할 가능성을 제공
        
        ![2024-12-17_18-27-25.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/7a4500c5-0e5f-4f01-b410-135b34eae2e3/2024-12-17_18-27-25.jpg)
        

- Crossover Operator
    
    ```python
    import ast
    
    class CrossoverOperator:
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
    ```
    
- ex.
    
    ```python
    tree_p1: ast.Module = ast.parse(inspect.getsource(p1))
    tree_p2: ast.Module = ast.parse(inspect.getsource(p2))
    body_p1 = tree_p1.body[0].body  
    body_p2 = tree_p2.body[0].body 
    
    crosser = CrossoverOperator()
    tree_p1.body[0].body, tree_p2.body[0].body = crosser.cross_bodies(body_p1, body_p2) 
    
    print_content(ast.unparse(tree_p1), '.py')
    ```
    
    ![2024-12-17_18-33-52.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/2b73de70-db23-4b49-88e4-de69cd0c908d/2024-12-17_18-33-52.jpg)
    

- Crossover 연산을 프로그램의 임의의 부분에 적용하기 위해 필요한 조건을 확인
    
    ```python
    # 모듈과 클래스 정의는 교차 대상에서 제외
    SKIP_LIST = {ast.Module, ast.ClassDef}
    
    # 주어진 AST 노드가 교차 가능한 문장 리스트를 포함하는지 확인
    def can_cross(self, tree: ast.AST, body_attr: str = 'body') -> bool:
        
        # SKIP_LIST에 포함된 노드인지 확인 (모듈이나 클래스는 제외)
        if any(isinstance(tree, cls) for cls in self.SKIP_LIST):
            return False  # 교차 불가능
    
        # body 속성이 존재하고, 문장 리스트의 길이가 2 이상인지 확인
        body = getattr(tree, body_attr, [])
        return body is not None and len(body) >= 2
    ```
    

- body_attr 속성에 대해 Crossover를 수행
    
    ```python
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
    ```
    

- if-else **노드**에서 **Crossover 연산**을 수행
    
    ```python
    # if-else **노드**에서 Crossover **연산**
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
    ```
    

- crossover 기능 진입
    
    ```python
    def crossover(self, t1: ast.AST, t2: ast.AST) -> Tuple[ast.AST, ast.AST]:
        assert isinstance(t1, ast.AST)
        assert isinstance(t2, ast.AST)
    
        for body_attr in ['body', 'orelse', 'finalbody']:
            if self.crossover_attr(t1, t2, body_attr):
                return t1, t2
    
        raise CrossoverError("No crossover found")
    
    class CrossoverError(ValueError):
        pass
    ```
    

- ex.
    
    ```python
    crossover = CrossoverOperator()
    tree_p1 = ast.parse(inspect.getsource(p1))
    tree_p2 = ast.parse(inspect.getsource(p2))
    crossover.crossover(tree_p1, tree_p2)
    
    print_content(ast.unparse(tree_p1), '.py')
    ```
    
    ![2024-12-17_18-44-11.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d67481c1-e33d-4a03-87ee-24d61bd5a6a3/2024-12-17_18-44-11.jpg)
    

## 6. Repairer

### (1) Repairer Class

- Repairer 클래스를 구현해 자동 프로그램 수리를 임의의 Python 프로그램에 적용
- 입력
    - 통계적 디버거: 통계적 디버깅 도구(ex. OchiaiDebugger)를 통해 결함 위치 탐색
    - 테스트 케이스: 통과한 테스트와 실패한 테스트를 통해 코드 수리의 기준을 제공
- 동작
    - Mutation: 결함이 의심되는 위치를 변이
    - Crossover: 두 코드 수정안을 결합해 새로운 후보를 생성
    - 적합도 평가: 생성된 후보가 테스트 케이스를 얼마나 잘 통과하는지 평가
- 결과
    - 적합도가 가장 높은 수정안(best fix candidate)을 반환

- RankingDebugger, StatementMutator, CrossoverOperator, DeltaDebugger 활용
    
    ```python
    import ast
    
    class Repairer(StackInspector):
        def __init__(self, 
    							   debugger: RankingDebugger, *,
                     targets: Optional[List[Any]] = None, # 수리할 함수/모듈 목록
                     sources: Optional[List[Any]] = None, # 수리에서 사용할 함수/모듈 목록
                     log: Union[bool, int] = False,
                     mutator_class: Type = StatementMutator, # 변이를 수행할 클래스
                     crossover_class: Type = CrossoverOperator, # 교차를 수행할 클래스
                     reducer_class: Type = DeltaDebugger, # 축소를 수행할 클래스
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
                self.log_tree("Source code to take repairs from:", 
                              self.source_tree)
    
            # 적합도 캐시: 수리 과정에서 계산된 적합도를 저장
            self.fitness_cache: Dict[str, float] = {}
    
            # 변이, 교차, 축소 도구 설정
            self.mutator: StatementMutator = mutator_class(
                source=all_statements(self.source_tree),  # 소스 코드의 모든 문장 목록
                suspiciousness_func=self.debugger.suspiciousness,  # 결함 위치 의심 점수
                log=(self.log >= 3))  # 로깅 수준
            self.crossover: CrossoverOperator = crossover_class(log=(self.log >= 3))
            self.reducer: DeltaDebugger = reducer_class(log=(self.log >= 3))
    
            # globals 설정: 코드 실행 시 사용할 전역 변수
            if globals is None:
                globals = self.caller_globals()  # 호출자의 globals 값 가져오기
            self.globals = globals
    ```
    

- 환경 설정 메서드 추가
    
    ```python
    # 주어진 함수의 소스 코드를 반환
    def getsource(self, item: Union[str, Any]) -> str:
        if isinstance(item, str):  # 문자열이면
            item = self.globals[item]  # globals에서 객체 가져오기
        return inspect.getsource(item)  # 객체의 소스 코드 반환
    ```
    
    ```python
    #  수리 대상 함수 목록을 반환 (test 포함 제외)
    def default_functions(self) -> List[Callable]:
    		# 이름이 'test'로 시작하거나 끝나는지 확인
        def is_test(name: str) -> bool:
            return name.startswith('test') or name.endswith('test')
    
        # 커버된 함수 중 테스트 함수가 아닌 함수만 반환
        return [func for func in self.debugger.covered_functions()
                if not is_test(func.__name__)]
    ```
    
    ```python
    # tree를 소스 코드 형태로 출력
    def log_tree(self, description: str, tree: Any) -> None:
        if self.log:  # 로깅 활성화된 경우
            print(description)
            print_content(ast.unparse(tree), '.py')  # AST를 소스 코드로 변환하여 출력
            print()
            print()
    ```
    
    ```python
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
    ```
    

- 테스트 실행
    
    ```python
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
        
    class FailureNotReproducedError(ValueError):
        pass
    ```
    
    ```python
    repairer = Repairer(middle_debugger)
    assert repairer.run_test_set(middle_debugger.PASS) == len(MIDDLE_PASSING_TESTCASES)
    assert repairer.run_test_set(middle_debugger.FAIL) == 0
    ```
    
    ✓
    

- 테스트 검증
    
    ```python
    # 주어진 테스트 집합의 가중치(Weight)를 반환
    def weight(self, test_set: str) -> float:
        return {
            self.debugger.PASS: WEIGHT_PASSING,  # PASS 테스트에 대한 가중치
            self.debugger.FAIL: WEIGHT_FAILING   # FAIL 테스트에 대한 가중치
        }[test_set]
    ```
    
    ```python
    # 테스트를 실행하고, 가중치를 적용한 적합도(fitness)를 반환
    def run_tests(self, validate: bool = False) -> float:
        fitness = 0.0  # 초기 적합도 점수
    
    		# PASS 및 FAIL 테스트 실행
        for test_set in [self.debugger.PASS, self.debugger.FAIL]:
            passed = self.run_test_set(test_set, validate=validate)  # 통과한 테스트 수
            ratio = passed / len(self.debugger.collectors[test_set])  # 통과 비율 계산
            fitness += self.weight(test_set) * ratio  # 가중치를 곱해 적합도 점수 계산
    
        return fitness  # 최종 적합도 점수 반환
    ```
    
    ```python
    # 테스트 결과를 검증
    def validate(self) -> None:
        fitness = self.run_tests(validate=True)  # 검증 모드에서 테스트 실행
        assert fitness == self.weight(self.debugger.PASS)  # PASS의 가중치와 적합도가 일치하는지 확인
    ```
    
    ```python
    repairer = Repairer(middle_debugger)
    repairer.validate()
    ```
    
    ✓
    

- 수정 후보 평가
    
    ```python
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
    ```
    

### (2) Definition Visitor

- DefinitionVisitor 클래스를 사용해 AST)에서 **최상위 함수 및 클래스 정의의 이름**을 추출
- 이를 Repairer 클래스의 toplevel_defs() 메서드에서 활용

- Repairer
    
    ```python
    # tree에서 최상위 함수 및 클래스 정의의 이름 목록을 반환
    def toplevel_defs(self, tree: ast.AST) -> List[str]:
        visitor = DefinitionVisitor()  # DefinitionVisitor 인스턴스 생성
        visitor.visit(tree)  # AST를 방문하여 정의된 이름 수집
        assert hasattr(visitor, 'definitions')  # 'definitions' 속성이 존재하는지 확인
        return visitor.definitions  # 수집된 정의 목록 반환
    ```
    
- Definition Visitor
    
    ```python
    # AST 트리에서 함수 및 클래스 정의의 이름을 수집하는 방문자 클래스
    class DefinitionVisitor(NodeVisitor):
        def __init__(self) -> None:
            self.definitions: List[str] = []
    
    		# 주어진 노드에서 이름을 추출해 `definitions`에 추가
        def add_definition(self, node: Union[ast.ClassDef, 
                                             ast.FunctionDef, 
                                             ast.AsyncFunctionDef]) -> None:
            self.definitions.append(node.name)
    
    		# 함수 정의(FunctionDef) 노드를 방문하여 이름을 추가
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.add_definition(node)
    
    		# 비동기 함수 정의(AsyncFunctionDef) 노드를 방문하여 이름을 추가
        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.add_definition(node)
    
    		# 클래스 정의(ClassDef) 노드를 방문하여 이름을 추가
        def visit_ClassDef(self, node: ast.ClassDef) -> None:\
            self.add_definition(node)
    ```
    

### (3) Evolve Repairer

- 초기 population 설정
    
    ```python
    # 초기 개체군을 생성
    def initial_population(self, size: int) -> List[ast.AST]:
        # AST(추상 구문 트리)로 이루어진 개체군 목록 반환
        return [self.target_tree] + [self.mutator.mutate(copy.deepcopy(self.target_tree)) for i in range(size - 1)]
    ```
    
- repair 진행
    
    ```python
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
    
        # 코드 축소 (최적화)
        best_tree = self.reduce(best_tree)
        fitness = self.fitness(best_tree)
    
        # 축소된 코드 출력
        self.log_tree(f"Reduced code (fitness = {fitness}):", best_tree)
    
        return best_tree, fitness  # 수리된 코드와 적합도 반환
    ```
    

- evolving
    
    ```python
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
    ```
    

- simplifying
    
    ```python
    # 수리된 프로그램을 델타 디버깅을 통해 간소화
    def reduce(self, tree: ast.AST) -> ast.AST:
        # 원본 프로그램의 적합도 계산
        original_fitness = self.fitness(tree)
    
        # 프로그램을 소스 코드 라인 단위로 나눔
        source_lines = ast.unparse(tree).split('\n')
    
        # 델타 디버깅 실행
        with self.reducer:  # DeltaDebugger 컨텍스트
            self.test_reduce(source_lines, original_fitness)
    
        # 델타 디버깅 결과 가져오기
        reduced_lines = self.reducer.min_args()['source_lines']
        reduced_source = "\n".join(reduced_lines)  # 간소화된 소스 코드 생성
    
        # 간소화된 소스 코드를 AST로 변환하여 반환
        return ast.parse(reduced_source)
        
    # 델타 디버깅 과정에서 간소화된 코드의 적합도를 평가
    def test_reduce(self, source_lines: List[str], original_fitness: float) -> None:
        try:
            # 소스 코드 라인을 문자열로 병합
            source = "\n".join(source_lines)
    
            # 소스 코드를 AST로 변환
            tree = ast.parse(source)
    
            # 간소화된 코드의 적합도 평가
            fitness = self.fitness(tree)
    
            # 간소화된 코드의 적합도가 원본보다 낮아야 함
            assert fitness < original_fitness
    
        except AssertionError:
            # 적합도가 낮아지지 않은 경우
            raise
        except SyntaxError:
            # 구문 오류가 발생한 경우
            raise
        except IndentationError:
            # 들여쓰기 오류가 발생한 경우
            raise
        except Exception:
            # 기타 예외 발생 시 무시
            # traceback.print_exc()  # 내부 오류 확인 시 주석 해제
            raise
    ```
    

- 실제 적용
    
    ```python
    repairer = Repairer(middle_debugger, log=True)
    ```
    
    ![2024-12-17_23-28-06.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/1421409a-8cfc-4739-8daf-c5abebcf36c9/2024-12-17_23-28-06.jpg)
    
    ```python
    best_tree, fitness = repairer.repair()
    ```
    
    ![2024-12-17_23-28-20.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/47c1ff1e-adfa-471d-bcb6-f7e62b4a225a/2024-12-17_23-28-20.jpg)
    
    ```python
    print_content(ast.unparse(best_tree), '.py')
    ```
    
    ![2024-12-17_23-28-55.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/a3081199-53a7-443e-aaed-49727ac47f60/2024-12-17_23-28-55.jpg)
    

## 7. Mutating Conditions

- html 문제의 경우,
    
    ```python
    best_tree, fitness = html_repairer.repair(iterations=20)
    ```
    
    ![2024-12-17_23-33-15.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/9e3c6154-826c-4605-858d-7d881172f04b/2024-12-17_23-33-15.jpg)
    
    → fitness가 1.0이 되지 못함
    
    → 소스 코드의 statement에서 condition이 잘못되었기 때문
    

### (1) Condition Visitor

- 조건식 탐색
    
    ```python
    import ast
    
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
    ```
    

- Condition Visitor 클래스
    - 제어 흐름의 조건식과 논리 연산자(and, or, not)가 포함된 표현식들을 탐색하고 수집
    
    ```python
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
    ```
    

- ex.
    
    ```python
    [ast.unparse(cond).strip() for cond in all_conditions(remove_html_markup_tree())]
    ```
    
    ![2024-12-17_23-54-28.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/81100bef-d6fa-493f-aca9-259086ae77da/2024-12-17_23-54-28.jpg)
    

### (2) Condition Mutator

- Condition Mutator
    - AST에서 제어 흐름 조건식을 변환하는 클래스
    
    ```python
    class ConditionMutator(StatementMutator):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)  # 부모 클래스의 생성자 호출
    
            # 소스 코드에서 조건식 수집
            self.conditions = all_conditions(self.source)
    
            if self.log:  # 로깅이 활성화된 경우
                print("Found conditions",
                      [ast.unparse(cond).strip()  # 조건식을 문자열로 변환하여 출력
                       for cond in self.conditions])
    
    		# 소스 코드에서 조건식 중 하나를 랜덤하게 선택하여 반환
        def choose_condition(self) -> ast.expr:
            return copy.deepcopy(random.choice(self.conditions))
    ```
    

- 변환 진행
    
    ```python
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
    ```
    

- ex.
    
    ```python
    for i in range(10):
        new_tree = mutator.mutate(remove_html_markup_tree())
    ```
    
    ![2024-12-18_00-02-30.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/778e7a87-b553-4451-80be-4000422205a6/2024-12-18_00-02-30.jpg)
    
    ```python
    condition_repairer = Repairer(html_debugger,
                                  mutator_class=ConditionMutator,
                                  log=2)
                                  
    best_tree, fitness = condition_repairer.repair(iterations=200)
    ```
    
    ![2024-12-18_00-04-36.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/1a5892e8-bfc7-4344-9e6d-c0475777cade/2024-12-18_00-04-36.jpg)
    
    ![2024-12-18_00-04-46.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/9f484c42-a0dd-4741-a70c-90f1214470e7/2024-12-18_00-04-46.jpg)