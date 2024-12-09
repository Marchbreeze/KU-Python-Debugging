<aside>
➡️

목표 1. 자동화된 추적
- 값의 기원을 자동으로 수집하고 추적
- 데이터를 생성하거나 변경한 위치, 제어 흐름(조건문, 반복문 등)에서 영향을 미친 요소까지 포함

목표 2. 디버깅 효율성 향상
- 여러 위치나 모듈에 퍼져 있는 기원을 쉽게 찾을 수 있도록 정보를 시각화하거나 기록

</aside>

![2024-12-09_02-00-10.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d7b25261-2745-419b-a7be-108b3beeb539/2024-12-09_02-00-10.jpg)

![2024-12-09_01-59-49.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/17cd04ca-a5af-4fda-8777-2de6661a70e8/2024-12-09_01-59-49.jpg)

## 1. 프로그램 상태 & 의존성

- 상태 (state)
    - 프로그램 실행 중의 모든 정보(구성 설정, 데이터베이스 콘텐츠, 장치의 상태 등) → 프로그램 결과에 영향
    - 대부분의 경우, 개별 변수를 통해 표현됨
    - 변수 : 임의의 값을 가지지 않음 & 특정 **시점**에서 설정되거나 접근됨
        
        → 프로그램 코드를 읽음으로써 변수의 기원(origins)을 파악할 수 있음
        

- ex. 중간값 반환 잘못된 예시
    
    ```python
    def middle(x, y, z):
        if y < z:
            if x < y:
                return y
            elif x < z:
                return y
        else:
            if x > y:
                return y
            elif x > z:
                return x
        return z
    ```
    
    ```python
    m = middle(2, 1, 3)
    m
    ```
    
    >  1 (elif x < z의 조건문에서 x가 중간값일 가능성이 고려되지 않음)
    

- 예시의 디버깅 진행
    1. 값의 변경 여부 확인
        - x, y, z는 함수 내부에서 변경되지 않음
    2. 잘못된 값의 반환 위치 확인
        - 반환된 값 m이 y인 경우, return y를 실행한 위치를 찾아야 함
        
        ```python
        with Debugger.Debugger():
            middle(2, 1, 3)
        ```
        
        ![2024-11-24_22-53-49.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/98312ad5-aa29-4c37-90c0-d7b183f75138/2024-11-24_22-53-49.jpg)
        

- 의존성 (dependency)
    - 변수 x가 변수 y에 의존하는 경우, `x ← y` 로 표현
    - 상태가 의존하는 기원의 종류
        1. 데이터 (Data dependency)
            - ex. 반환값이었던 y값
        2. 제어 조건 (Control dependency)
            - ex. 리턴문을 제어한 if 조건들 (y < z, x > y, x < z)

## 2. Dependencies 클래스

- Dependencies 클래스
    - **변수 간 의존성**을 특정 위치에서 캡처하고 시각화하는 도구
    - 변수와 위치 정보를 활용하여 **데이터 및 제어 의존성**을 기록하고 이를 분석 및 시각화할 수 있도록 설계

- **두 가지 의존성 그래프**를 관리
    1. data : 데이터 의존성을 기록 (한 변수의 값이 다른 변수의 값에 의존할 때 기록)
    2. control : 제어 의존성을 기록 (조건문이나 실행 흐름에 의해 변수의 상태나 실행 여부가 결정될 때 기록)

- 그래프 구조 : Dictionary로 관리
    1. **키 (Key)**: 노드(Node) – 특정 변수와 그 위치
    2. **값 (Value)**: 노드 집합(Set of Nodes) – 의존 관계에 있는 다른 변수와 위치

- 노드 : 튜플 (variable_name, location)로 표현
    - variable_name: 변수 이름
    - location: 변수의 위치를 나타내는 튜플 : func(실행 코드 블록), lineno(코드의 줄 번호)
    - ex.
        
        ```python
        Location = Tuple[Callable, int]
        Node = Tuple[str, Location]
        Dependency = Dict[Node, Set[Node]]
        ```
        

- 클래스 초기화
    
    ```python
    class Dependencies(StackInspector):
    
    		# init에서 data, control의 두 의존성 그래프를 보유
        def __init__(self, 
                     data: Optional[Dependency] = None,
                     control: Optional[Dependency] = None) -> None:
    
    				# 기본값 처리
            if data is None:
                data = {}
            if control is None:
                control = {}
    
    				# 속성 초기화
            self.data = data
            self.control = control
    
    				# 모든 변수가 데이터 및 제어 그래프에 존재하도록 동기화
    				# setdefault() : 키가 없을 경우 기본값 (빈 집합)을 설정
            for var in self.data:
                self.control.setdefault(var, set())
            for var in self.control:
                self.data.setdefault(var, set())
    
            self.validate()
    ```
    

- 의존성 그래프의 구조적 일관성 검증
    
    ```python
    def validate(self) -> None:
    		# 데이터 타입 검증 (딕셔너리 타입인지)
        assert isinstance(self.data, dict)
        assert isinstance(self.control, dict)
    
    		# 그래프 노드 구조 검증
        for node in (self.data.keys()) | set(self.control.keys()):
            var_name, location = node
            assert isinstance(var_name, str)
            func, lineno = location
            assert callable(func)
            assert isinstance(lineno, int)
    ```
    
    - (11번 단락에 override 있음)

- 주어진 노드의 소스 코드 반환
    1. 주어진 노드의 소스 코드 줄 추출
        
        ```python
        def _source(self, node: Node) -> str:
            # func 변수 찾을 수 없는 경우 빈 문자열 반환
            (name, location) = node
            func, lineno = location
            if not func:
                return ''
        
        		# 소스 코드
            try:
                source_lines, first_lineno = inspect.getsourcelines(func)
            except OSError:
                warnings.warn(f"Couldn't find source " f"for {func} ({func.__name__})")
                return ''
        
        		# 소스 코드의 해당 줄 추출
            try:
                line = source_lines[lineno - first_lineno].strip()
            except IndexError:
                return ''
        
            return line
        ```
        
    2. _source()의 결과를 기반으로 더 사용자 친화적인 포맷으로 반환
        
        ```python
        def source(self, node: Node) -> str:
        		# 유효한 결과 있으면 반환
            line = self._source(node)
            if line:
                return line
        
        		# 없으면 함수명 반환
            (name, location) = node
            func, lineno = location
            code_name = func.__name__
            if code_name.startswith('<'):
                return code_name
            else:
                return f'<{code_name}()>'
        ```
        
    - ex.
        
        ```python
        test_deps = Dependencies()
        test_deps.source(('z', (middle, 1)))
        ```
        
        ![2024-11-25_00-31-00.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/a6d933f7-a037-4b93-954d-36b4f396c611/2024-11-25_00-31-00.jpg)
        

## 3. 의존성 시각화

- 그래프 객체 세팅
    - graphviz 패키지를 사용하여 방향성 그래프(Digraph)를 정의
    - 시각적으로 표현할 때 필요한 스타일과 속성을 설정
        
        ```python
        from graphviz import Digraph
        import html
        
        NODE_COLOR = 'peachpuff'
        FONT_NAME = 'Courier'
        
        def make_graph(self,
                       name: str = "dependencies",
                       comment: str = "Dependencies") -> Digraph:
            return Digraph(name=name, comment=comment,
                graph_attr={
                },
                node_attr={
                    'style': 'filled',
                    'shape': 'box',
                    'fillcolor': self.NODE_COLOR,
                    'fontname': self.FONT_NAME
                },
                edge_attr={
                    'fontname': self.FONT_NAME
                })
        ```
        

- 데이터 및 제어 의존성 그래프 형태로 시각화
    - 의존성을 기반으로 graphviz **방향성 그래프**를 생성하고 반환
    - mode에 따라 그래프의 화살표 방향을 결정
        - 'flow': 정보 흐름을 나타냄 (A → B는 A가 B에 영향을 미친다는 의미)
        - 'depend': 의존성을 나타냄 (A → B는 B가 A에 의존한다는 의미)
        
        ```python
        def graph(self, *, mode: str = 'flow') -> Digraph:
        
            self.validate()
        
            g = self.make_graph()
            self.draw_dependencies(g, mode)
            self.add_hierarchy(g)
            return g
        ```
        
    - Jupyter Notebook 환경에서 객체를 출력할 때, 의존성 그래프를 **SVG 형식**으로 렌더링
        
        ```python
        def _repr_mimebundle_(self, include: Any = None, exclude: Any = None) -> Any:
            return self.graph()._repr_mimebundle_(include, exclude)
        ```
        
    1. draw_dependencies : 의존성 추가
        1. 모든 변수를 집합 형태로 반환
            
            ```python
            def all_vars(self) -> Set[Node]:
            		# 빈 집합으로 초기화
                all_vars = set()
                
                # 데이터 의존성에서 변수 수집
                for var in self.data:
                    all_vars.add(var)
                    for source in self.data[var]:
                        all_vars.add(source)
            
            		# 제어 의존성에서 변수 수집
                for var in self.control:
                    all_vars.add(var)
                    for source in self.control[var]:
                        all_vars.add(source)
            
                return all_vars
            ```
            
        2. 그래프에 직선 추가
            
            ```python
            def draw_edge(self, g: Digraph, mode: str,
                          node_from: str, node_to: str, **kwargs: Any) -> None:
                # 그래프의 종류에 따라 방향 설정한 edge 추가
                if mode == 'flow':
                    g.edge(node_from, node_to, **kwargs)
                elif mode == 'depend':
                    g.edge(node_from, node_to, dir="back", **kwargs)
                else:
                    raise ValueError("`mode` must be 'flow' or 'depend'")
            ```
            
        3. 그래프에 의존성 추가
            
            ```python
            def draw_dependencies(self, g: Digraph, mode: str) -> None:
                for var in self.all_vars():
                    g.node(self.id(var),
                           label=self.label(var),
                           tooltip=self.tooltip(var))
            
                    if var in self.data:
                        for source in self.data[var]:
                            self.draw_edge(g, mode, self.id(source), self.id(var))
            
                    if var in self.control:
                        for source in self.control[var]:
                            self.draw_edge(g, mode, self.id(source), self.id(var), style='dashed', color='grey')
            ```
            
            1. 변수(var)에 대해 **고유 식별자** 생성
                
                ```python
                def id(self, var: Node) -> str:
                    id = ""
                    for c in repr(var):
                        if c.isalnum() or c == '_':
                            id += c
                        if c == ':' or c == ',':
                            id += '_'
                    return id
                ```
                
            2. HTML 스타일의 라벨 생성
                
                ```python
                def label(self, var: Node) -> str:
                    (name, location) = var
                    source = self.source(var)
                
                    title = html.escape(name)
                    if name.startswith('<'):
                        title = f'<I>{title}</I>'
                
                    label = f'<B>{title}</B>'
                    if source:
                        label += (f'<FONT POINT-SIZE="9.0"><BR/><BR/>'
                                  f'{html.escape(source)}'
                                  f'</FONT>')
                    label = f'<{label}>'
                    return label
                ```
                
            3. 툴팁 생성
                
                ```python
                def tooltip(self, var: Node) -> str:
                    (name, location) = var
                    func, lineno = location
                    return f"{func.__name__}:{lineno}"
                ```
                
    2. add_hierarchy : 계층 구조 생성
        1. 모든 변수 정보를 함수별로 그룹화하여 반환
            - {`function`: [(`lineno`, `var`), (`lineno`, `var`), ...], ...} 형식으로 반환
            
            ```python
            def all_functions(self) -> Dict[Callable, List[Tuple[int, Node]]]:
            		# 함수별 변수 정보 저장
                functions: Dict[Callable, List[Tuple[int, Node]]] = {}
                
                # 모든 변수에 대해 함수에 정보 추가
                for var in self.all_vars():
                    (name, location) = var
                    func, lineno = location
                    if func not in functions:
                        functions[func] = []
                    functions[func].append((lineno, var))
            
            		# 각 함수의 변수 리스트를 줄 번호(lineno) 기준으로 오름차순 정렬
                for func in functions:
                    functions[func].sort()
            
                return functions
            ```
            
        2. 그래프에 계층 구조를 나타내기 위해 보이지 않는 엣지 추가
            
            → 노드 배치 순서를 함수 내 코드의 실행 순서와 일치하도록 보정하여, 시각적 일관성을 높이는 데 사용
            
            ```python
            def add_hierarchy(self, g: Digraph) -> Digraph:
                functions = self.all_functions()
                
                for func in functions:
            		    # 이전 변수 노드를 추적 - 현재 변수 노드와 엣지를 연결
                    last_var = None
                    # 이전 줄 번호를 추적 - 실행 순서가 바뀌지 않도록 보정
                    last_lineno = 0
                    for (lineno, var) in functions[func]:
                        if last_var is not None and lineno > last_lineno:
                            g.edge(self.id(last_var), self.id(var), style='invis')
                        last_var = var
                        last_lineno = lineno
            
                return g
            ```
            
    
    1. ex.
        
        ```python
        def middle_deps() -> Dependencies:
            return Dependencies({('z', (middle, 1)): set(), ('y', (middle, 1)): set(), ('x', (middle, 1)): set(), ('<test>', (middle, 2)): {('y', (middle, 1)), ('z', (middle, 1))}, ('<test>', (middle, 3)): {('y', (middle, 1)), ('x', (middle, 1))}, ('<test>', (middle, 5)): {('z', (middle, 1)), ('x', (middle, 1))}, ('<middle() return value>', (middle, 6)): {('y', (middle, 1))}}, {('z', (middle, 1)): set(), ('y', (middle, 1)): set(), ('x', (middle, 1)): set(), ('<test>', (middle, 2)): set(), ('<test>', (middle, 3)): {('<test>', (middle, 2))}, ('<test>', (middle, 5)): {('<test>', (middle, 3))}, ('<middle() return value>', (middle, 6)): {('<test>', (middle, 5))}})
        ```
        
        ```python
        middle_deps().graph(mode='depend')
        ```
        
        ![2024-11-25_01-22-49.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/b516f650-e73f-42b6-91e1-c111ef6e9daa/2024-11-25_01-22-49.jpg)
        
    

## 4. 의존성 추적

- backward_slice()
    - 주어진 슬라이싱 기준(criteria)으로부터 **의존성을 거꾸로 추적**하여 의존성의 부분 집합을 반환

- 슬라이싱 기준
    - 사용 가능한 입력
        1. 변수 이름 : ex. <test>
        2. (function, lineno) 형식의 튜플 : ex. (middle, 3)
        3. (var_name, (function, lineno)) 형식의 위치 정보 : ex. ('x', (middle, 1))
    - 모드
        - 어떤 종류의 의존성 추적할지 결정 (d: 데이터, c: 제어)
    
1. 슬라이싱 기준에 맞는 변수 탐색
    
    ```python
    def expand_criteria(self, criteria: List[Criterion]) -> List[Node]:
        all_vars = []
        for criterion in criteria:
            criterion_var = None
            criterion_func = None
            criterion_lineno = Non
    
    				# 슬라이싱 기준을 유형 별로 분류
            if isinstance(criterion, str):
                criterion_var = criterion
            elif len(criterion) == 2 and callable(criterion[0]):
                criterion_func, criterion_lineno = criterion
            elif len(criterion) == 2 and isinstance(criterion[0], str):
                criterion_var = criterion[0]
                criterion_func, criterion_lineno = criterion[1]
            else:
                raise ValueError("Invalid argument")
    				
    				# 의존성 그래프 변수와 비교
            for var in self.all_vars():
                (var_name, location) = var
                func, lineno = location
    
    						# 조건 비교 및 매칭
                name_matches = (criterion_func is None or
                                criterion_func == func or
                                criterion_func.__name__ == func.__name__)
                location_matches = (criterion_lineno is None or
                                    criterion_lineno == lineno)
                var_matches = (criterion_var is None or
                               criterion_var == var_name)
                if name_matches and location_matches and var_matches:
                    all_vars.append(var)
    
        return all_vars
    
    ```
    

1. 의존성 추적
    
    ```python
    def backward_slice(self, *criteria: Criterion, 
                       mode: str = 'cd', depth: int = -1) -> Dependencies:
        data = {}
        control = {}
        queue = self.expand_criteria(criteria)
        seen = set()
    
    		# 반복 추적 (대기열이 비어있지 않고, 남은 깊이가 0이 아니면 추적을 계속)
        while len(queue) > 0 and depth != 0:
            var = queue[0]
            queue = queue[1:]
            seen.add(var)
    
    				# 현재 변수의 데이터 의존성을 추가
            if 'd' in mode:
                data[var] = self.data[var]
                for next_var in data[var]:
                    if next_var not in seen:
                        queue.append(next_var)
            else:
                data[var] = set()
    
    				# 현재 변수의 제어 의존성을 추가
            if 'c' in mode:
                control[var] = self.control[var]
                for next_var in control[var]:
                    if next_var not in seen:
                        queue.append(next_var)
            else:
                control[var] = set()
    
            depth -= 1
    
        return Dependencies(data, control)
    ```
    

- 예제
    1. 데이터 의존성
        
        ```python
        middle_deps().backward_slice('<middle() return value>', mode='d') 
        ```
        
        ![2024-11-25_01-50-46.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/51497846-a590-4cf1-879f-d094b5f1a970/2024-11-25_01-50-46.jpg)
        
        - middle() 함수의 반환문에 있는 y 값이 middle()로 전달된 y 값에 데이터 의존성을 가지고 있음
            
            → 상단 노드의 y 값이 하단 노드의 y 값으로 Flow 존재
            
            → return 문은 상단 노드에서의 y 초기화에 데이터 의존성을 가지고 있음
            
    2. 제어 의존성
        
        ```python
        middle_deps().backward_slice('<middle() return value>', mode='c', depth=1) 
        ```
        
        ![2024-11-25_01-53-55.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/8fe2cc65-ff48-41ca-a384-ab04f6f49e26/2024-11-25_01-53-55.jpg)
        
        - 제어 의존성 : 회색 점선으로 표시됨
        
        ```python
        middle_deps().backward_slice('<middle() return value>', mode='c')
        ```
        
        ![2024-11-25_01-54-17.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/3ce73dab-148d-4a44-bf8e-db9bf1fa0ff6/2024-11-25_01-54-17.jpg)
        
        - 이 조건문(x < z)은 다시 이전의 조건문들에 의해 제어됨 → 전체 제어 의존성 체인 확인 필요

## 5. 의존성 코드 시각화

1. print 활용
    1. format_var : 특정 노드(변수)를 텍스트로 표시
        - 표시 방법 : NAME (FUNCTION:LINENO) → NAME (LINENO) (함수 내부에서 명시 불필요)
            
            ```python
            def format_var(self, var: Node, current_func: Optional[Callable] = None) -> str:
                name, location = var
                func, lineno = location
                if current_func and (func == current_func or func.__name__ == current_func.__name__):
                    return f"{name} ({lineno})"
                else:
                    return f"{name} ({func.__name__}:{lineno})"
            ```
            
            >  x (10)
            
            >  x (example_func:10)
            
    2. __str__ : 모든 노드와 그 **데이터 의존성(**<=**)** 및 제어 의존성(<-)을 텍스트로 표시
        
        ```python
        def __str__(self) -> str:
            self.validate()
        
            out = ""
            
            # 함수 별 의존성 출력
            for func in self.all_functions():
                code_name = func.__name__
        
                if out != "":
                    out += "\n"
                out += f"{code_name}():\n"
        
        				# 의존성의 키를 모두 수집하고 정렬
                all_vars = list(set(self.data.keys()) | set(self.control.keys()))
                all_vars.sort(key=lambda var: var[1][1])
        
        				# 현재 함수와 연관된 노드 필터링
                for var in all_vars:
                    (name, location) = var
                    var_func, var_lineno = location
                    var_code_name = var_func.__name__
        
                    if var_code_name != code_name:
                        continue
        
        						# 노드 의존성 문자열 생성
                    all_deps = ""
                    for (source, arrow) in [(self.data, "<="), (self.control, "<-")]:
                        deps = ""
                        for data_dep in source[var]:
                            if deps == "":
                                deps = f" {arrow} "
                            else:
                                deps += ", "
                            deps += self.format_var(data_dep, func)
                        if deps != "":
                            if all_deps != "":
                                all_deps += ";"
                            all_deps += deps
        
                    if all_deps == "":
                        continue
                    out += ("    " + self.format_var(var, func) + all_deps + "\n")
        
            return out
        ```
        
    - ex.
        
        ```python
        print(middle_deps())
        ```
        
        ![2024-11-25_02-18-44.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/858ab7b0-6170-4407-9fff-1eb86e33cc05/2024-11-25_02-18-44.jpg)
        

1. print(repr) 활용
    - __repr__ : 의존성 각자 텍스트로 표시
        
        ```python
        def repr_var(self, var: Node) -> str:
            name, location = var
            func, lineno = location
            return f"({repr(name)}, ({func.__name__}, {lineno}))"
        
        def repr_deps(self, var_set: Set[Node]) -> str:
            if len(var_set) == 0:
                return "set()"
        
            return ("{" +
                    ", ".join(f"{self.repr_var(var)}"
                              for var in var_set) +
                    "}")
        
        def repr_dependencies(self, vars: Dependency) -> str:
            return ("{\n        " +
                    ",\n        ".join(
                        f"{self.repr_var(var)}: {self.repr_deps(vars[var])}"
                        for var in vars) +
                    "}")
        
        def __repr__(self) -> str:
            return (f"Dependencies(\n" +
                    f"    data={self.repr_dependencies(self.data)},\n" +
                    f" control={self.repr_dependencies(self.control)})")
        ```
        
    - ex.
        
        ```python
        print(repr(middle_deps()))
        ```
        
        ![2024-11-25_02-20-51.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/7c39cb34-2a4a-4d05-8119-d9ce007ce322/2024-11-25_02-20-51.jpg)
        
    
2. 코드 상에서의 의존성 출력
    1. 단일 함수에 대한 의존성을 포함한 코드를 주석과 함께 출력
        
        ```python
        def _code(self, item: Callable, mode: str) -> None:=
        		# 출력 대상 함수 결정
            func = item
            for fn in self.all_functions():
                if fn == item or fn.__name__ == item.__name__:
                    func = fn
                    break
        		
        		# 의존성 노드 추출
            all_vars = self.all_vars()
            slice_locations = set(location for (name, location) in all_vars)
        
        		# 코드 줄 분석 및 주석 추가
            source_lines, first_lineno = inspect.getsourcelines(func)
            n = first_lineno
            for line in source_lines:
                line_location = (func, n)
                if line_location in slice_locations:
                    prefix = "* "
                else:
                    prefix = "  "
                print(f"{prefix}{n:4} ", end="")
        
        				# 의존성 주석 생성
                comment = ""
                for (mode_control, source, arrow) in [
                    ('d', self.data, '<='),
                    ('c', self.control, '<-')
                ]:
                    if mode_control not in mode:
                continue
                    deps = ""
                    for var in source:
                        name, location = var
                        if location == line_location:
                            for dep_var in source[var]:
                                if deps == "":
                                    deps = arrow + " "
                                else:
                                    deps += ", "
                                deps += self.format_var(dep_var, item)
                    if deps != "":
                        if comment != "":
                            comment += "; "
                        comment += deps
        
        				# 주석 추가 및 출력
                if comment != "":
                    line = line.rstrip() + "  # " + comment
                print_content(line.rstrip(), '.py')
                print()
              n += 1
        ```
        
    2. 지정된 함수(items) 목록 또는 의존성에 포함된 모든 함수의 코드를 출력
        
        ```python
        def code(self, *items: Callable, mode: str = 'cd') -> None:
        		# 출력 대상 결정
            if len(items) == 0:
                items = cast(Tuple[Callable], self.all_functions().keys())
                
            # 대상 함수별 출력
            for i, item in enumerate(items):
                if i > 0:
                    print()
                self._code(item, mode)
        ```
        
    - ex.
        
        ```python
        middle_deps().code()
        ```
        
        ![2024-11-25_02-27-28.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/69989237-b21b-4579-9362-e8cfcf10fcc8/2024-11-25_02-27-28.jpg)
        
        - 6번 줄이 마지막으로 실행된 줄이므로, 조사 시작 지점으로 삼을 수 있음
        - 데이터 의존성을 통해, 함수 호출 이후 반환될 때까지 y 값이 다른 문장에 의해 변경되지 않았음을 알 수 있음
            
            → 조건문 또는 최종 return 문에 오류가 있음을 알 수 있음
            

## 6. 슬라이스

- 특정 변수에 대한 의존성 그래프가 주어지면, 이 변수에 영향을 미칠 수 있는 프로그램의 하위 집합 (슬라이스)를 식별할 수 있음
    - 위 예시 : * 표시된 위치들만 슬라이스의 일부

- 슬라이스의 중요성
    1. 영향을 미치지 않는 코드 위치를 배제
        - 프로그램에서 실패에 영향을 미칠 가능성이 없는 위치를 배제
        - 변경해도 실패에 영향을 미치지 않음
    2. 코드의 흩어진 원인들을 통합
        - 프로그램 코드의 많은 의존성은 비지역적 → 하나의 단일 맥락으로 묶어줌

- remove_html_markup의 예시
    - 기존 코드
        
        ```python
        def remove_html_markup(s):  # type: ignore
            tag = False
            quote = False
            out = ""
        
            for c in s:
                assert tag or not quote
        
                if c == '<' and not quote:
                    tag = True
                elif c == '>' and not quote:
                    tag = False
                elif (c == '"' or c == "'") and tag:
                    quote = not quote
                elif not tag:
                    out = out + c
        
            return out
        ```
        
    
    ```python
    def remove_html_markup_deps() -> Dependencies:
        return Dependencies({('s', (remove_html_markup, 136)): set(), ('tag', (remove_html_markup, 137)): set(), ('quote', (remove_html_markup, 138)): set(), ('out', (remove_html_markup, 139)): set(), ('c', (remove_html_markup, 141)): {('s', (remove_html_markup, 136))}, ('<test>', (remove_html_markup, 144)): {('quote', (remove_html_markup, 138)), ('c', (remove_html_markup, 141))}, ('tag', (remove_html_markup, 145)): set(), ('<test>', (remove_html_markup, 146)): {('quote', (remove_html_markup, 138)), ('c', (remove_html_markup, 141))}, ('<test>', (remove_html_markup, 148)): {('c', (remove_html_markup, 141))}, ('<test>', (remove_html_markup, 150)): {('tag', (remove_html_markup, 147)), ('tag', (remove_html_markup, 145))}, ('tag', (remove_html_markup, 147)): set(), ('out', (remove_html_markup, 151)): {('out', (remove_html_markup, 151)), ('c', (remove_html_markup, 141)), ('out', (remove_html_markup, 139))}, ('<remove_html_markup() return value>', (remove_html_markup, 153)): {('<test>', (remove_html_markup, 146)), ('out', (remove_html_markup, 151))}}, {('s', (remove_html_markup, 136)): set(), ('tag', (remove_html_markup, 137)): set(), ('quote', (remove_html_markup, 138)): set(), ('out', (remove_html_markup, 139)): set(), ('c', (remove_html_markup, 141)): set(), ('<test>', (remove_html_markup, 144)): set(), ('tag', (remove_html_markup, 145)): {('<test>', (remove_html_markup, 144))}, ('<test>', (remove_html_markup, 146)): {('<test>', (remove_html_markup, 144))}, ('<test>', (remove_html_markup, 148)): {('<test>', (remove_html_markup, 146))}, ('<test>', (remove_html_markup, 150)): {('<test>', (remove_html_markup, 148))}, ('tag', (remove_html_markup, 147)): {('<test>', (remove_html_markup, 146))}, ('out', (remove_html_markup, 151)): {('<test>', (remove_html_markup, 150))}, ('<remove_html_markup() return value>', (remove_html_markup, 153)): set()})
        
    remove_html_markup_deps().graph()
    ```
    
    ![2024-11-25_03-04-14.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/9546c406-f972-4cb0-890a-5c084ed84d18/2024-11-25_03-04-14.jpg)
    
    - 첫번째 (tag = False) 가 아무런 의존성을 주지 못하는 이유?
        
        → tag가 False인 상태는 첫 번째 문자가 처리되기 전까지 (루프가 시작되자마자 조건에 따라 tag의 값이 변경되기 때문)
        

⇒ 동적 슬라이스 (dynamic slices) : 단일 실행 내에서 발생한 의존성을 반영

⇒ 실행이 변경됨에 따라 의존성도 함께 변경됨

## 8. 추적 기법

- 프로그램 실행 중에 의존성을 자동으로 수집하여 이를 분석하는 방법
- 단일 호출로 어떤 계산에 대한 의존성을 수집하고, 이를 그래프나 코드 주석 형태로 프로그래머에게 제공
- 의존성 추적 방법
    1. 데이터 객체 래핑 (Wrapping Data Objects)
        - 변수 자체를 래핑하여 해당 변수와 관련된 데이터 및 의존성을 추적
    2. 데이터 접근 래핑 (Wrapping Data Accesses)
        - 데이터가 읽히거나 쓰이는 순간에 해당 접근을 감지하여 의존성을 추적

### (1) 데이터 객체 래핑

- 각 값을 클래스에 래핑해서 origin을 추적 - 변수의 값과 origin을 함께 저장
    - 프로그램 코드를 변경하지 않고 원래 값 대신 “래핑된” 객체를 전달할 수 있음
- ex.
    
    ```python
    # 변수 x가 3번 줄에서 0으로 초기화
    x = (value=0, origin=<Line 3>)
    # 5번 줄에서 x의 값을 변수 y에 복사
    y = (value=0, origin=<Line 3, Line 5>)
    ```
    
- 구현
    
    ```python
    class MyInt(int):
        def __new__(cls: Type, value: Any, *args: Any, **kwargs: Any) -> Any:
            return super(cls, cls).__new__(cls, value)
    
        def __repr__(self) -> str:
            return f"{int(self)}"
    ```
    
    - 사용할 때는 기본 int처럼 사용 가능
        
        ```python
        n: MyInt = MyInt(5)
        n, n + 1
        ```
        
        >  (5, 6)
        
    - 함수를 통해 origin 접근 가능
        
        ```python
        n.origin = "Line 5"
        n.origin
        ```
        
        >  ‘Line 5’
        

- 단점
    - 호환성 문제 : 래핑된 객체가 원래 값과 호환 가능해야 함
    - 연산 중 기원 손실 방지 필요 :  연산자를 오버로딩하여, 계산 후에도 원래 값과 기원을 유지하도록 처리
    - 값 할당 시 추적 문제 : 값이 다른 변수에 할당되는 순간을 추적 필요, but 파이썬에서 기본 제공 X
    - 모든 데이터 타입에 적용 필요

### (2) 데이터 접근 래핑

- 소스 코드에 변경을 가하여 모든 데이터 읽기, 쓰기 작업을 추적
    - 원래 데이터는 그대로 유지되지만, 코드를 수정하여 데이터 접근을 감시
    - 정수, 실수, 문자열, 리스트 등 어떤 타입이든 상관없이 작동
- ex.
    
    ```python
    # 읽기
    _data.get('x', x)  # returns x
    # 쓰기
    _data.set('x', value)  # returns value
    ```
    
    ```python
    # a = b + c
    a = _data.set('a', _data.get('b', b) + _data.get('c', c))
    ```
    
    → _data : 현재 코드 위치 & 각 변수의 사용 여부 추적
    
    → b&c는 읽기, a는 쓰기 ⇒ a가 b와 c의 데이터 의존성을 가진다는 결론 도출
    
- 단점
    - 읽기와 **쓰기** 작업을 정확히 구분해야 하므로 추가적인 노력이 필요
    - Python의 여러 언어 기능(ex. 속성, 메서드 호출, 클래스, 전역 변수)을 별도로 처리해야 함

### (3) DataTracker

- DataTracker 클래스로 _data 접근 구현
- 데이터 읽기와 쓰기 작업을 추적하며, 해당 작업이 이루어진 코드 위치를 확인할 수 있도록 함

- 클래스 초기화
    
    ```python
    class DataTracker(StackInspector):
    
        def __init__(self, log: bool = False) -> None:
            self.log = log
    ```
    
    - log: 추적 작업에 대한 로그를 활성화할지 결정하는 Boolean 값 (True일 때 추적 기록)

- 읽기
    
    ```python
    def set(self, name: str, value: Any, loads: Optional[Set[str]] = None) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: setting {name}")
        return value
    ```
    
    - 특정 변수(name)에 값(value)을 할당할 때, 해당 작업을 추적
- 쓰기
    
    ```python
    def get(self, name: str, value: Any) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: getting {name}")
        return value
    ```
    
    - 특정 변수(name)의 값을 읽는 작업을 추적
- ex.
    
    ```python
    _test_data = DataTracker(log=True)
    x = _test_data.set('x', 1)
    ```
    
    >  <module>:2: setting x
    
    ```python
    _test_data.get('x', x)
    ```
    
    >  <module>:1: getting x
    
    >  1
    

## 9. 변수 접근 추적

### (1) 소스 코드 계측 (AST)

- 소스 코드를 변환하여 변수에 대한 읽기 및 쓰기 접근이 자동으로 재작성되도록 하는 방법
    
    → 소스 코드의 내부 표현인 추상 구문 트리(Abstract Syntax Tree, AST)를 검사
    

- 추상 구문 트리 (AST)
    - 코드의 구조를 트리 형태로 표현한 것
    - 각 **구문 요소**(예: 변수, 연산자, 함수 호출 등)에 대해 **특정 노드 타입**이 존재
        
        ```python
        import ast
        from bookutils import show_ast
        
        middle_tree = ast.parse(inspect.getsource(middle))
        show_ast(middle_tree)
        ```
        
        ![2024-11-25_04-29-47.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/82264a2b-4d40-40aa-a059-6b8ff4c7a6e4/2024-11-25_04-29-47.jpg)
        
        → 가장 말단의 Name 노드에 대해서 변환이 필요
        

### (2) TrackGetTransformer

- 코드의 추상 구문 트리를 탐색하여, 모든 Name 노드를 식별하고 이를 _data **접근 코드**로 변환
- ast.NodeTransformer를 상속하여 AST의 특정 노드를 변환
    
    ```python
    from ast import NodeTransformer, NodeVisitor, Name, AST, \
    		Module, Load, Store, \
        Attribute, With, withitem, keyword, Call, Expr, \
        Assign, AugAssign, AnnAssign, Assert
    import typing
    
    DATA_TRACKER = '_data'
    
    class TrackGetTransformer(NodeTransformer):
    		# 모든 Name 노드를 탐색하여 조건에 따라 변환
        def visit_Name(self, node: Name) -> AST:
    		    # 현재 노드의 모든 자식 노드를 탐색
            self.generic_visit(node)
    
    				# Python의 내장 함수나 타입인지 확인
            if is_internal(node.id):
                return node
    
    				# _data 변수 자체는 변환하지 않음
            if node.id == DATA_TRACKER:
                return node
    
    				# 변수의 읽기 작업(load)에만 변환 적용
            if not isinstance(node.ctx, Load):
                return node
    
    				# 현재 변수 id를 _data.get() 호출로 변환하는 새로운 AST 노드 생성
            new_node = make_get_data(node.id)
            
            # 소스 코드 위치 정보를 새 노드에 복사하여 디버깅 및 오류 메시지에 원래 위치를 유지
            ast.copy_location(new_node, node)
            return new_node
    
    		def is_internal(id: str) -> bool:
    		    return (id in dir(__builtins__) or id in dir(typing))
    ```
    

- 현재 변수 id를 _data.get() 호출로 변환하는 새로운 AST 노드 생성
    
    ```python
    def make_get_data(id: str, method: str = 'get') -> Call:
        return Call(func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()), 
                                   attr=method, ctx=Load()),
                    args=[ast.Str(id), Name(id=id, ctx=Load())],
                    keywords=[])
    ```
    
- ex.
    
    ```python
    make_get_data("x")
    ```
    
    >  _data.get('x', x)
    
- 결과물
    
    ```python
    show_ast(Module(body=[make_get_data("x")], type_ignores=[])) 
    ```
    
    ![2024-11-25_04-40-44.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d85b1604-919c-4139-ab27-96246a2b8421/2024-11-25_04-40-44.jpg)
    

- 서브트리가 올바르게 생성되었는지 확인하는 방법
    
    → 이를 파싱하고 ast.dump()를 사용해 해당 코드의 AST 구조를 출력
    
    ```python
    print(ast.dump(ast.parse("_data.get('x', x)")))
    ```
    
    >  Module(body=[Expr(value=Call(func=Attribute(value=Name(id='_data', ctx=Load()), attr='get', ctx=Load()), args=[Constant(value='x'), Name(id='x', ctx=Load())], keywords=[]))], type_ignores=[])
    
    - 함수화하면
        
        ```python
        def dump_tree(tree: AST) -> None:
            print_content(ast.unparse(tree), '.py')
            ast.fix_missing_locations(tree)
            _ = compile(cast(ast.Module, tree), '<dump_tree>', 'exec')
        ```
        
- ex.
    
    ```python
    TrackGetTransformer().visit(middle_tree)
    ```
    
    ```python
    dump_tree(middle_tree)
    ```
    
    ![2024-11-25_04-44-00.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/c41420c0-c12d-4093-bd31-d573199a05c6/2024-11-25_04-44-00.jpg)
    

### (3) DataTrackerTester

- DataTrackerTester() 클래스
    - 특정 함수를 계측하기 위해, 추상 구문 트리를 기반으로 코드를 실행하고 함수의 데이터를 추적
    - 컨텍스트 매니저로 구현되어, with 문을 통해 안전하게 함수 계측을 수행하고 실행 후 원래 상태로 복원
    
    ```python
    from types import TracebackType
    
    class DataTrackerTester:
        def __init__(self, tree: AST, func: Callable, log: bool = True) -> None:
            # 계측할 함수의 소스 파일 경로 가져옴 - 나중에 컴파일된 코드의 위치 정보를 추적하는 데 사용
            source = cast(str, inspect.getsourcefile(func))
            # 주어진 AST(tree)를 실행 가능한 코드 객체로 컴파일
            self.code = compile(cast(ast.Module, tree), source, 'exec')
            self.func = func
            self.log = log
    
    		# DataTracker 생성
        def make_data_tracker(self) -> Any:
            return DataTracker(log=self.log)
    
    		# 컨텍스트 진입 시, 함수를 계측 버전으로 변환
        def __enter__(self) -> Any:
            tracker = self.make_data_tracker()
            globals()[DATA_TRACKER] = tracker
            exec(self.code, globals())
            return tracker
    
    		# with 블록이 종료되면, 함수와 전역 네임스페이스를 원래 상태로 복원
        def __exit__(self, exc_type: Type, exc_value: BaseException,
                     traceback: TracebackType) -> Optional[bool]:
            globals()[self.func.__name__] = self.func
            del globals()[DATA_TRACKER]
            return None
    ```
    
- ex.
    
    ```python
    # 생성해둔 추상 구문 트리와 함수 입력
    with DataTrackerTester(middle_tree, middle):
        middle(2, 1, 3)
    ```
    
    ![2024-11-25_04-49-20.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/a44e8dd4-cc9b-4ac5-8045-d46a37ca5e8a/2024-11-25_04-49-20.jpg)
    
    ```python
    # 추적 끝나면 원상복구
    middle(2, 1, 3)
    ```
    
    >  1
    

### (4) Visitor Class

- 쓰기 과정의 추적
    - 단순 :      x = value → _data.set('x', value)
    - 복잡 : x[y] = value → _data.set('x', value, loads=(x, y))   ⇒   x, y의 읽기 작업도 추가 기록
1. 구현
    
    ```python
    def make_set_data(id: str, value: Any, 
                      loads: Optional[Set[str]] = None, method: str = 'set') -> Call:
        keywords=[]
        
    		# loads가 주어진 경우 키워드 인자 loads를 생성 : 읽기 작업을 추적할 변수들을 포함
        if loads:
            keywords = [
                keyword(arg='loads',
                        value=ast.Tuple(
                            elts=[Name(id=load, ctx=Load()) for load in loads],
                            ctx=Load()
                        ))
            ]
    
    		# 호출 노드 생성
        new_node = Call(func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()),
                                       attr=method, ctx=Load()),
                        args=[ast.Str(id), value],
                        keywords=keywords)
    
        ast.copy_location(new_node, value)
        return new_node
    ```
    
2. 할당문의 왼쪽(LHS)이 단순한 변수 이름이 아니라, x[i]와 같은 복잡한 표현식인 경우
    
    ```python
    class LeftmostNameVisitor(NodeVisitor):
        def __init__(self) -> None:
            super().__init__()
            self.leftmost_name: Optional[str] = None
    
        def visit_Name(self, node: Name) -> None:
            if self.leftmost_name is None:
                self.leftmost_name = node.id
            self.generic_visit(node)
    ```
    
    ```python
    def leftmost_name(tree: AST) -> Optional[str]:
        visitor = LeftmostNameVisitor()
        visitor.visit(tree)
        return visitor.leftmost_name
    ```
    
    ```python
    leftmost_name(ast.parse('a[x] = 25'))
    ```
    
    >  ‘a’
    
3. 튜플이 할당된 경우
    
    ```python
    class StoreVisitor(NodeVisitor):
        def __init__(self) -> None:
            super().__init__()
            self.names: Set[str] = set()
    
        def visit(self, node: AST) -> None:
            if hasattr(node, 'ctx') and isinstance(node.ctx, Store):
                name = leftmost_name(node)
                if name:
                    self.names.add(name)
            self.generic_visit(node)
    ```
    
    ```python
    def store_names(tree: AST) -> Set[str]:
        visitor = StoreVisitor()
        visitor.visit(tree)
        return visitor.names
    ```
    
    ```python
    store_names(ast.parse('a[x], b[y], c = 1, 2, 3'))
    ```
    
    >  {’a’, ‘b’, ‘c’}
    
4. 왼쪽 표현식에 읽기 작업이 포함된 경우
    
    ```python
    class LoadVisitor(NodeVisitor):
        def __init__(self) -> None:
            super().__init__()
            self.names: Set[str] = set()
    
        def visit(self, node: AST) -> None:
            if hasattr(node, 'ctx') and isinstance(node.ctx, Load):
                name = leftmost_name(node)
                if name is not None:
                    self.names.add(name)
            self.generic_visit(node)
    ```
    
    ```python
    def load_names(tree: AST) -> Set[str]:
        visitor = LoadVisitor()
        visitor.visit(tree)
        return visitor.names
    ```
    
    ```python
    load_names(ast.parse('a[x], b[y], c = 1, 2, 3'))
    ```
    
    >  {’a’, ‘b’, ‘x’, ‘y’}
    

### (5) TrackSetTransformer

- 모든 할당에 대해서 수행
    
    ```python
    class TrackSetTransformer(NodeTransformer):
    		# 일반 할당(a = b)을 계측
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
    
    		# 확장된 할당(a += b)을 계측
        def visit_AugAssign(self, node: AugAssign) -> AugAssign:
            value = ast.unparse(node.value)
            if value.startswith(DATA_TRACKER):
                return node
            id = cast(str, leftmost_name(node.target))
            node.value = make_set_data(id, node.value, method='augment')
            return node
    
    		# 주석이 포함된 할당(a: int = b)을 계측
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
       
    	  # assert 구문을 계측     
        def visit_Assert(self, node: Assert) -> Assert:
            value = ast.unparse(node.test)
            if value.startswith(DATA_TRACKER + '.set'):
                return node 
            loads = load_names(node.test)
            node.test = make_set_data("<assertion>", node.test, loads=loads)
            return node
    ```
    
- ex.
    
    ```python
    TrackSetTransformer().visit(assign_tree)
    dump_tree(assign_tree)
    ```
    
    ![2024-11-25_05-45-57.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/86cc2258-b3ab-4d18-b16d-517cb20bac28/2024-11-25_05-45-57.jpg)
    
    ```python
    # TrackSetTransformer 실행 이후
    TrackGetTransformer().visit(assign_tree)
    dump_tree(assign_tree)
    ```
    
    ![2024-11-25_05-46-13.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/c72a88b9-5a6f-4ba1-9725-43e4ba5ec9c8/2024-11-25_05-46-13.jpg)
    

### (6) 나머지 TrackTransformer

1. 리턴
    - 코드
        
        ```python
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
        ```
        
    - ex.
        
        ```python
        TrackReturnTransformer().visit(middle_tree)
        dump_tree(middle_tree)
        ```
        
        ![2024-11-25_05-48-26.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/fb2f5727-f5a1-4e3a-92ee-eab1a88eeffa/2024-11-25_05-48-26.jpg)
        

1. 제어흐름
    - 코드
        
        ```python
        class TrackControlTransformer(NodeTransformer):
        		# if 문 계측
            def visit_If(self, node: ast.If) -> ast.If:
                self.generic_visit(node)
                node.test = self.make_test(node.test)
                node.body = self.make_with(node.body)
                node.orelse = self.make_with(node.orelse)
                return node
                
            # 블록(코드의 리스트)을 with _data:로 감싸는 AST 서브트리 생성
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
               
            # 조건식을 _data.test() 호출로 변환 
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
                
            # while 문 계측
            def visit_While(self, node: ast.While) -> ast.While:
                self.generic_visit(node)
                node.test = self.make_test(node.test)
                node.body = self.make_with(node.body)
                node.orelse = self.make_with(node.orelse)
                return node
                
            # for 문 계측
            def visit_For(self, node: Union[ast.For, ast.AsyncFor]) -> AST:
                self.generic_visit(node)
                id = ast.unparse(node.target).strip()
                node.iter = make_set_data(id, node.iter)
                # Uncomment if you want iterators to control their bodies
                # node.body = self.make_with(node.body)
                # node.orelse = self.make_with(node.orelse)
                return node
        
            # 비동기 for 문 계측
            def visit_AsyncFor(self, node: ast.AsyncFor) -> AST:
                return self.visit_For(node)
        
            # 컴프리헨션(list, dict, set, generator) 내의 for 구문 계측
            def visit_comprehension(self, node: ast.comprehension) -> AST:
                self.generic_visit(node)
                id = ast.unparse(node.target).strip()
                node.iter = make_set_data(id, node.iter)
                return node
        ```
        
    - ex.
        
        ```python
        TrackControlTransformer().visit(middle_tree)
        dump_tree(middle_tree)
        ```
        
        ![2024-11-25_05-50-33.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ba628f72-26e6-4ddf-a493-e644f43d99c3/2024-11-25_05-50-33.jpg)
        
    - DataTracker의 확장 필요 (추후 오버라이드될 함수들)
        
        ```python
        def test(self, cond: AST) -> AST:
            if self.log:
                caller_func, lineno = self.caller_location()
                print(f"{caller_func.__name__}:{lineno}: testing condition")
            return cond
        
        def __enter__(self) -> Any:
            if self.log:
                caller_func, lineno = self.caller_location()
                print(f"{caller_func.__name__}:{lineno}: entering block")
            return self
        
        def __exit__(self, exc_type: Type, exc_value: BaseException, traceback: TracebackType) -> Optional[bool]:
            if self.log:
                caller_func, lineno = self.caller_location()
                print(f"{caller_func.__name__}:{lineno}: exiting block")
            return None
        ```
        

1. 함수 호출
    - 코드
        
        ```python
        class TrackCallTransformer(NodeTransformer):
        		# 주어진 노드를 _data.call() 계측 호출로 변환
            def make_call(self, node: AST, func: str, pos: Optional[int] = None, kw: Optional[str] = None) -> Call:
                keywords = []
                if pos:
                    keywords.append(keyword(arg='pos', value=ast.Num(pos)))
                if kw:
                    keywords.append(keyword(arg='kw', value=ast.Str(kw)))
                return Call(func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()),
                                           attr=func,
                                           ctx=Load()),
                             args=[node], 
                             keywords=keywords)
                             
        		# AST의 함수 호출 노드(Call)를 변환하여 계측
            def visit_Call(self, node: Call) -> Call:
                self.generic_visit(node)
                call_as_text = ast.unparse(node)
                if call_as_text.startswith(DATA_TRACKER + '.ret'):
                    return node  
                func_as_text = ast.unparse(node)
                if func_as_text.startswith(DATA_TRACKER + '.'):
                    return node
                new_args = []
                for n, arg in enumerate(node.args):
                    new_args.append(self.make_call(arg, 'arg', pos=n + 1))
                node.args = cast(List[ast.expr], new_args)
                for kw in node.keywords:
                    id = kw.arg if hasattr(kw, 'arg') else None
                    kw.value = self.make_call(kw.value, 'arg', kw=id)
                node.func = self.make_call(node.func, 'call')
                return self.make_call(node, 'ret')
        ```
        
    - ex.
        
        ```python
        TrackCallTransformer().visit(f_tree)
        dump_tree(f_tree)
        ```
        
        ![2024-11-25_05-57-09.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/b2ee1af6-10a4-4d03-8b4a-92dd8a6dcc99/2024-11-25_05-57-09.jpg)
        
    - DataTracker의 확장 필요
        
        ```python
        class DataTracker(DataTracker):
        		# 함수에 전달된 인자 추적 (pos: 인자 순서, kw: 키워드 인수의 이름)
            def arg(self, value: Any, pos: Optional[int] = None, kw: Optional[str] = None) -> Any:
                if self.log:
                    caller_func, lineno = self.caller_location()
                    info = ""
                    if pos:
                        info += f" #{pos}"
                    if kw:
                        info += f" {repr(kw)}"
                    print(f"{caller_func.__name__}:{lineno}: pushing arg{info}")
        
                return value
                
            # 함수에서 반환된 값 추적
            def ret(self, value: Any) -> Any:
                if self.log:
                    caller_func, lineno = self.caller_location()
                    print(f"{caller_func.__name__}:{lineno}: returned from call")
        
                return value
            
            # 함수 호출 계측 (추후 오버라이딩)
            def instrument_call(self, func: Callable) -> Callable:
                return func
        
        		# 함수 호출 자체를 추적
            def call(self, func: Callable) -> Callable:
                if self.log:
                    caller_func, lineno = self.caller_location()
                    print(f"{caller_func.__name__}:{lineno}: calling {func}")
                return self.instrument_call(func)
        ```
        

1. 파라미터
    - 코드
        
        ```python
        class TrackParamsTransformer(NodeTransformer):
        		# 함수 정의를 변환하여 파라미터 추적 코드를 삽입
            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
                self.generic_visit(node)
                
                # 파라미터 탐색
                named_args = []
                for child in ast.iter_child_nodes(node.args):
                    if isinstance(child, ast.arg):
                        named_args.append(child)
                create_stmts = []
                
                # 추적 코드 생성
                for n, child in enumerate(named_args):
                    keywords=[keyword(arg='pos', value=ast.Num(n + 1))]
                    if child is node.args.vararg:
                        keywords.append(keyword(arg='vararg', value=ast.Str('*')))
                    if child is node.args.kwarg:
                        keywords.append(keyword(arg='vararg', value=ast.Str('**')))
                    if n == len(named_args) - 1:
                        keywords.append(keyword(arg='last',
                                                value=ast.NameConstant(value=True)))
                    create_stmt = Expr(
                        value=Call(
                            func=Attribute(value=Name(id=DATA_TRACKER, ctx=Load()),
                                           attr='param', ctx=Load()),
                            args=[ast.Str(child.arg),
                                  Name(id=child.arg, ctx=Load())
                                 ],
                            keywords=keywords
                        )
                    )
                    ast.copy_location(create_stmt, node)
                    create_stmts.append(create_stmt)
                    
                # 본문 수정
                node.body = cast(List[ast.stmt], create_stmts) + node.body
                return node
        ```
        
    - ex.
        
        ```python
        TrackParamsTransformer().visit(middle_tree)
        dump_tree(middle_tree)
        ```
        
        ![2024-11-25_06-03-14.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ef0f8062-2d6a-443f-a0f3-3afa77cdc51d/2024-11-25_06-03-14.jpg)
        
    - DataTracker의 확장 필요
        
        ```python
        class DataTracker(DataTracker):
        			# 함수 호출 시 매개변수의 이름, 값, 위치, 그리고 가변 인수 여부를 로깅하고 기록
        	    def param(self, name: str, value: Any, 
                      pos: Optional[int] = None, vararg: str = '', last: bool = False) -> Any:
                if self.log:
                    caller_func, lineno = self.caller_location()
                    info = ""
                    if pos is not None:
                        info += f" #{pos}"
                    print(f"{caller_func.__name__}:{lineno}: initializing {vararg}{name}{info}")
                return self.set(name, value)
        ```
        

- Transformer Stress Test
    
    ```python
    # 변환하고 계측한 후, 변환된 AST을 컴파일하여 트랜스포머의 안정성과 정확성을 스트레스 테스트
    for module in [Assertions, Debugger, inspect, ast]:
        module_tree = ast.parse(inspect.getsource(module))
        assert isinstance(module_tree, ast.Module)
    
        TrackCallTransformer().visit(module_tree)
        TrackSetTransformer().visit(module_tree)
        TrackGetTransformer().visit(module_tree)
        TrackControlTransformer().visit(module_tree)
        TrackReturnTransformer().visit(module_tree)
        TrackParamsTransformer().visit(module_tree)
        ast.fix_missing_locations(module_tree) 
    
        module_code = compile(module_tree, '<stress_test>', 'exec')
        print(f"{repr(module.__name__)} instrumented successfully.")
    ```
    

## 10. DependencyTracker

- 변수 접근을 추적하고, 이를 기반으로 의존성을 구성하는 클래스
    
    ```python
    class DependencyTracker(DataTracker):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
    
            self.origins: Dict[str, Location] = {}  # 현재 변수가 마지막으로 설정된 위치
            self.data_dependencies: Dependency = {} 
            self.control_dependencies: Dependency = {}
    
            self.last_read: List[str] = []  # 최근에 읽힌 변수 리스트
            self.last_checked_location = (StackInspector.unknown, 1) # 마지막으로 확인된 코드 위치
            self._ignore_location_change = False # 코드 실행 중 위치 변경을 무시할지 여부
            
            self.data: List[List[str]] = [[]]  # Data stack
            self.control: List[List[str]] = [[]]  # Control stack
    
            self.frames: List[Dict[Union[int, str], Any]] = [{}]  # Argument stack
            self.args: Dict[Union[int, str], Any] = {}  # Current args
    ```
    

- 읽기
    
    ```python
    def get(self, name: str, value: Any) -> Any:
        self.check_location()
        self.last_read.append(name)
        return super().get(name, value)
    ```
    
    - ex.
        
        ```python
        _test_data = DependencyTracker(log=True)
        _test_data.get('x', x) + _test_data.get('y', y)
        ```
        
        ![2024-11-25_06-09-30.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/975148e5-7012-4dc8-97da-ac088059b305/2024-11-25_06-09-30.jpg)
        
    - 읽기 작업을 수행하기 전 현재 실행 위치를 확인하고 특정 조건에 따라 last_read 리스트를 초기화 필요
        
        ```python
        # self.last_read 리스트를 초기화하여, 이전에 읽은 변수 기록을 제거
        def clear_read(self) -> None:
            if self.log:
                direct_caller = inspect.currentframe().f_back.f_code.co_name  # type: ignore
                caller_func, lineno = self.caller_location()
                print(f"{caller_func.__name__}:{lineno}: "
                      f"clearing read variables {self.last_read} "
                      f"(from {direct_caller})")
            self.last_read = []
        
        # 현재 실행 위치(함수 이름과 줄 번호)를 확인하고, 이전 위치와 다르다면 clear_read를 호출
        def check_location(self) -> None:
        		# 현재 실행 위치 확인
            location = self.caller_location()
            func, lineno = location
            last_func, last_lineno = self.last_checked_location
        		# 이전 위치와 비교
            if self.last_checked_location != location:
                if self._ignore_location_change:
                    self._ignore_location_change = False
                elif func.__name__.startswith('<'):
                    pass
                elif last_func.__name__.startswith('<'):
                    pass
                else:
                    #	위치가 변경되었다면 읽기 변수 초기화
                    self.clear_read()
            self.last_checked_location = location
        
        # 다음 줄 실행 시 발생하는 위치 변경에 의한 last_read 리스트 초기화를 방지
        def ignore_next_location_change(self) -> None:
            self._ignore_location_change = True
        
        # 현재 줄 실행 시 발생하는 위치 변경에 의한 last_read 리스트 초기화를 방지
        def ignore_location_change(self) -> None:
            self.last_checked_location = self.caller_location()
        ```
        

- 쓰기
    
    ```python
    import itertools
    
    TEST = '<test>'
    
    # 변수 name에 값 value를 설정하고 데이터 및 제어 의존성을 기록
    def set(self, name: str, value: Any, loads: Optional[Set[str]] = None) -> Any:
        # 읽은 변수(vars_read)의 출처를 dependencies에 추가
        def add_dependencies(dependencies: Set[Node], 
                             vars_read: List[str], tp: str) -> None:
            for var_read in vars_read:
                if var_read in self.origins:
                    if var_read == self.TEST and tp == "data":
                        continue
                    origin = self.origins[var_read]
                    dependencies.add((var_read, origin))
                    if self.log:
                        origin_func, origin_lineno = origin
                        caller_func, lineno = self.caller_location()
                        print(f"{caller_func.__name__}:{lineno}: "
                              f"new {tp} dependency: "
                              f"{name} <= {var_read} "
                              f"({origin_func.__name__}:{origin_lineno})")
    		# 위치 확인 및 초기화
        self.check_location()
        ret = super().set(name, value)
        location = self.caller_location()
    		
    		# 데이터, 제어 의존성 추가
        add_dependencies(self.data_dependencies.setdefault
                         ((name, location), set()),
                         self.last_read, tp="data")
        add_dependencies(self.control_dependencies.setdefault
                         ((name, location), set()),
                         cast(List[str], itertools.chain.from_iterable(self.control)),
                         tp="control")
    
    		# 기록 갱신 후 반환
        self.origins[name] = location
        self.last_read = [name]
        self._ignore_location_change = False
        return ret
    
    # 추적된 데이터 및 제어 의존성을 반환
    def dependencies(self) -> Dependencies:
        return Dependencies(self.data_dependencies, self.control_dependencies)
    ```
    
    - ex.
        
        ```python
        _test_data = DependencyTracker()
        x = _test_data.set('x', 1)
        y = _test_data.set('y', _test_data.get('x', x))
        z = _test_data.set('z', _test_data.get('x', x) + _test_data.get('y', y))
        ```
        
        ```python
        _test_data.origins
        ```
        
        ![2024-11-25_06-17-01.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/805c5a6c-81b4-4c0b-b2f9-6114470ef7bd/2024-11-25_06-17-01.jpg)
        
        ```python
        _test_data.data_dependencies
        ```
        
        ![2024-11-25_06-17-33.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/da0c031c-280d-4dc3-8bdc-fc37c66a6134/2024-11-25_06-17-33.jpg)
        
        ```python
        _test_data.dependencies().graph()
        ```
        
        ![2024-11-25_06-17-59.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/78036f85-2d83-4b7a-a235-54e0766d758f/2024-11-25_06-17-59.jpg)
        

<참조>

- 조건문에서의 제어 의존성 추적
    
    ```python
    # 테스트 조건의 값을 <test>라는 이름의 가상 변수에 설정 & 이후 last_read 리스트에 추
    def test(self, value: Any) -> Any:
        self.set(self.TEST, value)
        return super().test(value)
    
    # 조건문(if, while, for)의 블록에 진입할 때 제어 의존성을 추적
    def __enter__(self) -> Any:
        self.control.append(self.last_read)
        self.clear_read()
        return super().__enter__()
    
    # 조건문 블록을 빠져나올 때 읽기 변수 상태를 복원하고, 이후 실행을 준비
    def __exit__(self, exc_type: Type, exc_value: BaseException, traceback: TracebackType) -> Optional[bool]:
        self.clear_read()
        self.last_read = self.control.pop()
        self.ignore_next_location_change()
        return super().__exit__(exc_type, exc_value, traceback)
    ```
    
    - ex.
        
        ```python
        _test_data = DependencyTracker()
        x = _test_data.set('x', 1)
        y = _test_data.set('y', _test_data.get('x', x))
        
        if _test_data.test(_test_data.get('x', x) >= _test_data.get('y', y)):
            with _test_data:
                z = _test_data.set('z',  _test_data.get('x', x) + _test_data.get('y', y))
                
        _test_data.control_dependencies
        ```
        
        ![2024-11-25_06-22-12.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/039f0694-831e-4fdc-a915-22305a9569f2/2024-11-25_06-22-12.jpg)
        

<참조>

- 함수 호출 & 리턴을 처리하기 위한 데이터 스택 사용
    - 복잡한 표현식에서 함수 호출을 처리하면서 데이터 의존성을 추적
    - 함수 호출 시 인수의 평가로 인해 읽힌 변수들만 함수 호출에 영향을 미치는 변수로 기록
    
    ```python
    # 함수 호출을 추적하고, 호출 시점에서의 읽기 변수 상태와 매개변수를 저장
    def call(self, func: Callable) -> Callable:
    		# 기본 추적 작업 수행
        func = super().call(func)
    
    		# 호출 대상 함수가 generator면 별도 처리
        if inspect.isgeneratorfunction(func):
            return self.call_generator(func)
        
        # 읽기 변수 상태 저장
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: "
                  f"saving read variables {self.last_read}")
    		
    		# data stack 업데이트
        self.data.append(self.last_read)
        self.clear_read()
        self.ignore_next_location_change()
        self.frames.append(self.args)
        self.args = {}
        return func
    ```
    
    ```python
    # 함수가 반환될 때 발생하는 데이터 의존성과 매개변수 의존성을 추적하고, 호출 이전의 상태를 복원
    def ret(self, value: Any) -> Any:
    
        value = super().ret(value)
        if self.in_generator():
            return self.ret_generator(value)
    
        # 이전 읽기 변수 복원 및 반환값 추가
        ret_name = None
        for var in self.last_read:
            if var.startswith("<"):
                ret_name = var
        self.last_read = self.data.pop()
        if ret_name:
            self.last_read.append(ret_name)
    
    		# 비추적 함수에서 반환된 경우, 모든 매개변수를 last_read에 추가
        if self.args:
            for key, deps in self.args.items():
                self.last_read += deps
    
    		# 상태 복원
        self.ignore_location_change()
        self.args = self.frames.pop()
    
    		# 디버깅 로그 출력
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: "
                  f"restored read variables {self.last_read}")
        return value
    ```
    
    ```python
    import copy
    
    # self.data 스택의 마지막 값이 None이면 제너레이터 호출로 간주
    def in_generator(self) -> bool:
        return len(self.data) > 0 and self.data[-1] is None
    
    # 제너레이터 호출 시 초기화 작업 수행
    def call_generator(self, func: Callable) -> Callable:
        self.data.append(None) 
        self.frames.append(None)  
        assert self.in_generator()
        self.clear_read()
        return func
    
    # 제너레이터 반환 시 발생하는 의존성을 추적하고, 반환된 제너레이터 객체를 래핑
    def ret_generator(self, generator: Any) -> Any:
        self.data.pop()
        self.frames.pop()
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: "
                  f"wrapping generator {generator} (args={self.args})")
        for arg in self.args:
            self.last_read += self.args[arg]
        saved_args = copy.deepcopy(self.args)
    
    		# 제너레이터가 실행될 때 매개변수를 복원하고 호출을 추적
        def wrapper() -> Generator[Any, None, None]:
            self.args = saved_args
            if self.log:
                caller_func, lineno = self.caller_location()
                print(f"{caller_func.__name__}:{lineno}: "
                  f"calling generator (args={self.args})")
            self.ignore_next_location_change()
            yield from generator
    
        return wrapper()
    ```
    
- ex.
    
    ```python
    def my_gen():
        yield 1
        yield 2
    
    tracker = DependencyTracker(log=True)
    
    gen = tracker.call_generator(my_gen)
    wrapped_gen = tracker.ret_generator(gen)
    
    for value in wrapped_gen:
        print(value)
    ```
    
    ![2024-11-25_06-42-59.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/f6388946-655a-4930-875f-0b5acc3b4570/2024-11-25_06-42-59.jpg)
    
- 파라미터 & 아규먼트
    
    ```python
    # 함수 호출 시 위치 인수와 키워드 인수의 읽기 의존성을 추적
    def arg(self, value: Any, pos: Optional[int] = None, kw: Optional[str] = None) -> Any:
        # 로그 출력
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: " f"saving args read {self.last_read}")
        
        # 위치 인수 또는 키워드 인수 저장
        if pos:
            self.args[pos] = self.last_read
        if kw:
            self.args[kw] = self.last_read
            
    		# 읽기 변수 초기화
        self.clear_read()
        return super().arg(value, pos, kw)
    ```
    
    ```python
    # 함수 호출 시 전달된 파라미터와 해당 매개변수에 의존하는 읽기 변수 상태를 추적
    def param(self, name: str, value: Any,
              pos: Optional[int] = None, vararg: str = "", last: bool = False) -> Any:
        # 읽기 변수 초기화
        self.clear_read()
    
    		# 파라미터 분류 및 처리
        if vararg == '*':
            for index in self.args:
                if isinstance(index, int) and pos is not None and index >= pos:
                    self.last_read += self.args[index]
        elif vararg == '**':
            for index in self.args:
                if isinstance(index, str):
                    self.last_read += self.args[index]
        elif name in self.args:
            self.last_read = self.args[name]
        elif pos in self.args:
            self.last_read = self.args[pos]
    
    		# 로그 출력
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: "
                  f"restored params read {self.last_read}")
    
    		# 위치 변경 무시 후 상위 클래스 호출
        self.ignore_location_change()
        ret = super().param(name, value, pos)
    
    		# 마지막 파라미터 처리
        if last:
            self.clear_read()
            self.args = {}  
    
        return ret
    ```
    

- Dependencies 클래스에 검증 추가
    
    ```python
    class Dependencies(Dependencies):
        def validate(self) -> None:
            super().validate()
    
    				# 모든 변수 순회 후 소스 코드 존재 여부 확인
            for var in self.all_vars():
                source = self.source(var)
                if not source:
                    continue
                if source.startswith('<'):
                    continue   # no source
    
    						# 의존성 검증
                for dep_var in self.data[var] | self.control[var]:
                    dep_name, dep_location = dep_var
                    
                    # <test> 검증 제외
                    if dep_name == DependencyTracker.TEST:
                        continue
                        
                    # 반환값 의존성이 있는 경우, 소스 코드에 함수 호출이 포함되어 있는지 확인
                    if dep_name.endswith(' value>'):
                        if source.find('(') < 0:
                            warnings.warn(f"Warning: {self.format_var(var)} "
                                      f"depends on {self.format_var(dep_var)}, "
                                      f"but {repr(source)} does not "
                                      f"seem to have a call")
                        continue
                    
                    # 함수 정의 검증 제외
                    if source.startswith('def'):
                        continue
    
    								# 변수 이름이 소스 코드에 등장하는지 확인
                    rx = re.compile(r'\b' + dep_name + r'\b')
                    if rx.search(source) is None:
                        warnings.warn(f"{self.format_var(var)} "
                                  f"depends on {self.format_var(dep_var)}, "
                                  f"but {repr(dep_name)} does not occur "
                                  f"in {repr(source)}")
    ```
    

## 11. 최종적인 Slicer 제작

- Slicer Class : 모든 기능을 통합하는 도구
    1. 소스 코드 계측
        - 전달된 함수(func_1, func_2, …)를 계측하여 데이터 및 제어 의존성을 추적
    2. 의존성 수집
        - 계측된 함수가 호출되는 동안 의존성을 기록
    3. 정상 복원
        - with 블록 종료 후 계측된 함수의 원래 정의를 복원

### (1) Instrumenter Class

- 함수 계측 및 복원을 위한 기본 구조를 제공
- instrument() 메서드를 호출하여 계측 작업을 수행하며, 이를 서브클래스에서 오버로딩하여 구체적인 계측 방식을 구현해야 함
- 코드
    
    ```python
    class Instrumenter(StackInspector):
    
        def __init__(self, *items_to_instrument: Callable,
                     globals: Optional[Dict[str, Any]] = None,
                     log: Union[bool, int] = False) -> None:
            self.log = log
            # 계측 대상 함수 또는 객체의 리스트
            self.items_to_instrument: List[Callable] = list(items_to_instrument)
            self.instrumented_items: Set[Any] = set()
    
    				# 계측된 항목을 저장하거나 수정할 네임스페이스
            if globals is None:
                globals = self.caller_globals()
            self.globals = globals
    
    		# 계측 대상을 가져와 instrument() 메서드를 호출
        def __enter__(self) -> Any:
            items = self.items_to_instrument
            if not items:
                items = self.default_items_to_instrument()
    
            for item in items:
                self.instrument(item)
    
            return self
    
    		# 계측 대상이 명시되지 않은 경우, 기본적으로 빈 리스트를 반환
        def default_items_to_instrument(self) -> List[Callable]:
            return []
    
    		# 전달된 item(함수, 객체 등)을 계측 & 계측된 항목을 instrumented_items에 저장
        def instrument(self, item: Any) -> Any:
            if self.log:
                print("Instrumenting", item)
            self.instrumented_items.add(item)
            return item
            
        # with 블록 종료 시 호출되어 계측된 항목을 복원
        def __exit__(self, exc_type: Type, exc_value: BaseException, traceback: TracebackType) -> Optional[bool]:
            self.restore()
            return None
    
    		# 계측된 항목(instrumented_items)을 원래 상태로 복원
        def restore(self) -> None:
            for item in self.instrumented_items:
    		        # globals 네임스페이스에 저장된 계측된 정의를 원래 정의로 교체
                self.globals[item.__name__] = item
    ```
    

### (2) Slicer Class

- 자체적인 의존성 추적기를 구현 가능한 클래스
    
    ```python
    class Slicer(Instrumenter):
    		def __init__(self, 
    								 # 계측할 함수 또는 모듈 - 이를 통해 의존성을 추적할 코드 범위를 지정
    								 *items_to_instrument: Any,
    								 # 실행 중 의존성을 기록할 DependencyTracker 객체
                     dependency_tracker: Optional[DependencyTracker] = None,
                     # 계측된 항목을 저장할 네임스페이스
                     globals: Optional[Dict[str, Any]] = None,
                     # 디버깅 로그를 활성화
                     log: Union[bool, int] = False):
            super().__init__(*items_to_instrument, globals=globals, log=log)
    
            if dependency_tracker is None:
                dependency_tracker = DependencyTracker(log=(log > 1))
            self.dependency_tracker = dependency_tracker
    
            self.saved_dependencies = None
    
    		# 계측 대상이 명시되지 않았을 때 호출 (오류 출력)
        def default_items_to_instrument(self) -> List[Callable]:
            raise ValueError("Need one or more items to instrument")
    ```
    
    - `log=True` (or `log=1`): Show instrumented source code
    - `log=2`: Also log execution
    - `log=3`: Also log individual transformer steps
    - `log=4`: Also log source line numbers

- 기능 추가
    1. 함수나 객체를 받아, 이를 소스 코드에서 추출하고 AST로 변환
        
        ```python
        def parse(self, item: Any) -> AST:
        		# 소스 코드 추출
            source_lines, lineno = inspect.getsourcelines(item)
            source = "".join(source_lines)
        		
        		# 디버깅 로그
            if self.log >= 2:
                print_content(source, '.py', start_line_number=lineno)
                print()
                print()
        
        		# AST 변환
            tree = ast.parse(source)
            # 줄번호 조정 (추출된 소스 코드가 전체 코드 중 일부일 수 있으므로)
            ast.increment_lineno(tree, lineno - 1)
            return tree
        ```
        
    2. AST에 정의된 변환기를 적용하여 계측 및 추적 코드 삽입
        
        ```python
        # 수정하기 위해 적용할 변환기(transformer) 객체의 목록을 반환
        def transformers(self) -> List[NodeTransformer]:
            return [
                TrackCallTransformer(),
                TrackSetTransformer(),
                TrackGetTransformer(),
                TrackControlTransformer(),
                TrackReturnTransformer(),
                TrackParamsTransformer()
            ]
        
        # 계측 및 추적 코드 삽입 후 AST 반환
        def transform(self, tree: AST) -> AST:
            # 지정된 변환기 적용
            for transformer in self.transformers():
            
                if self.log >= 3:
                    print(transformer.__class__.__name__ + ':')
                    
        				# 각 변환기의 visit() 메서드를 호출하여 트리를 수정
                transformer.visit(tree)
                
                # 변환 중 추가된 AST 노드에 대해 줄 번호 및 위치 정보를 보완
                ast.fix_missing_locations(tree)
                
                if self.log >= 3:
                    print_content(ast.unparse(tree), '.py')
                    print()
                    print()
        
            if 0 < self.log < 3:
                print_content(ast.unparse(tree), '.py')
                print()
                print()
        
          return tree
        ```
        

1. 특정 함수 또는 객체의 소스 코드를 변환하여, 추적 및 의존성 분석을 위한 코드 삽입을 수행
    
    ```python
    def instrument(self, item: Any) -> Any:
    		# 내부 또는 내장 함수 확인
        if is_internal(item.__name__):
            return item  
        if inspect.isbuiltin(item):
            return item
    
    		# 기본적인 초기화 수행
        item = super().instrument(item)
        
    	  # AST 생성 및 변환
        tree = self.parse(item)
        tree = self.transform(tree)
        
        # 컴파일 및 실행
        self.execute(tree, item)
    
    		# 계측된 함수 반환
        new_item = self.globals[item.__name__]
        return new_item
    ```
    
2. 변환된 AST을 컴파일하고 실행하여, 계측된 코드가 실행 중 사용될 수 있도록 준비
    
    ```python
        def execute(self, tree: AST, item: Any) -> None:
            # 소스 파일 위치 가져오기
            source = cast(str, inspect.getsourcefile(item))
            
            # 변환된 AST를 실행 가능한 바이트코드로 변환
            code = compile(cast(ast.Module, tree), source, 'exec')
    
            # 의존성 추적기 활성화
            self.globals[DATA_TRACKER] = self.dependency_tracker
    
            # 코드 실행 - 계측된 코드로 기존 item(함수, 클래스 등)을 재정의
            exec(code, self.globals)
    ```
    

1. 코드 계측 전의 원래 상태로 복원
    
    ```python
        def restore(self) -> None:
    		    # DATA_TRACKER 제거
            if DATA_TRACKER in self.globals:
                self.saved_dependencies = self.globals[DATA_TRACKER]
                del self.globals[DATA_TRACKER]
            super().restore()
    ```
    

- 추가적인 코드들
    
    ```python
    # 수집된 의존성 정보를 반환
    def dependencies(self) -> Dependencies:
        if self.saved_dependencies is None:
            return Dependencies({}, {})
        return self.saved_dependencies.dependencies()
    
    # 계측된 코드와 함께 의존성을 주석 형태로 출력
    def code(self, *args: Any, **kwargs: Any) -> None:
        first = True
        for item in self.instrumented_items:
            if not first:
                print()
            self.dependencies().code(item, *args, **kwargs)
            first = False
    
    # 수집된 의존성을 그래프 형식으로 시각화
    def graph(self, *args: Any, **kwargs: Any) -> Digraph:
        return self.dependencies().graph(*args, **kwargs)
    
    def _repr_mimebundle_(self, include: Any = None, exclude: Any = None) -> Any:
        return self.graph()._repr_mimebundle_(include, exclude)
    ```
    

- 예시 실행
    
    ```python
    with Slicer(middle) as slicer:
        m = middle(2, 1, 3)
    m
    ```
    
    >  1
    
    ```python
    print(slicer.dependencies())
    ```
    
    ![2024-11-25_07-15-00.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/28dfa293-b549-4483-8ad6-084e42aa87f7/2024-11-25_07-15-00.jpg)
    
    ```python
    slicer.code()
    ```
    
    ![2024-11-25_07-15-24.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d6113f0e-6ab8-462d-b757-b0e742f3caa9/2024-11-25_07-15-24.jpg)
    
    ```python
    slicer
    ```
    
    ![2024-11-25_07-15-45.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/44092dac-a68a-4558-ad36-b6ee909326ef/2024-11-25_07-15-45.jpg)
    
    ```python
    print(repr(slicer.dependencies()))
    ```
    
    ![2024-11-25_07-16-08.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/21eb05b3-1c15-44f8-a33d-84ce018d0a08/2024-11-25_07-16-08.jpg)
