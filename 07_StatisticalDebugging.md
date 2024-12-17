## 1. 통계적 디버깅 개요

![2024-12-06_16-31-24.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/22614304-2e6d-4b63-9445-632b1f2ccd27/2024-12-06_16-31-24.jpg)

![2024-12-06_16-31-44.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ae85204a-b960-467a-9995-4118c723a416/2024-12-06_16-31-44.jpg)

![2024-12-06_16-32-02.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/945e9fbd-302f-4b72-be7e-4ebf7bc9478e/2024-12-06_16-32-02.jpg)

![2024-12-06_16-32-18.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/0def6671-56e5-46e9-9d51-dbbaefdd9c06/2024-12-06_16-32-18.jpg)

![2024-12-06_16-32-40.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/b4f012c7-0baa-49c4-902c-25140ed4db4e/2024-12-06_16-32-40.jpg)

- Statistical Debugger
    - 프로그램의 실행 중 발생하는 특정 이벤트(ex. 코드 라인의 실행 여부)와 테스트 결과(성공 또는 실패)를 연관시켜 결함이 있는 코드의 위치를 식별하는 데 사용
    - 다양한 서브클래스가 있으며, 대표적으로 TarantulaDebugger와 OchiaiDebugger가 있음
        - 두 디버거는 코드 커버리지 데이터를 수집해 라인별로 “의심 수준”을 계산
        - 의심 수준은 실패 테스트에서 얼마나 자주 실행되는지를 나타냄
    - 상관관계를 찾는 디버깅 기법
        - 상관관계가 반드시 인과관계를 의미하는 것은 아님, 상관관계가 높은 이벤트는 중요한 단서를 제공

- 이벤트 수집 방법
    1. 수동 호출 수집
        - 특정 함수 호출을 성공 또는 실패로 분류하여 이벤트를 수집
        - with 블록 안에서 첫 번째 함수 호출만 추적됨
            
            ```python
            debugger = TarantulaDebugger()
            with debugger.collect_pass():
                remove_html_markup("abc")  # 성공
            with debugger.collect_fail():
                remove_html_markup('"abc"')  # 실패
            ```
            
    2. 테스트 기반 수집
        - 테스트에서 발생한 예외 여부를 기준으로 이벤트를 성공 또는 실패로 분류
            
            ```python
            debugger = TarantulaDebugger()
            with debugger:  # 성공
                remove_html_markup("abc")
            with debugger:  # 실패 (예외 발생)
                remove_html_markup('"abc"')
                assert False
            ```
            

## 2. 이벤트 수집

### (1) Collector 추상 클래스

- 추상 클래스 Collector는 다음 두 가지 메서드를 제공
    - collect(): 이벤트를 수집하기 위한 메서드로, traceit() 추적기에서 호출
    - events(): 수집된 이벤트를 가져오기 위한 메서드
    - 두 메서드는 서브클래스에서 구현됨
    
    ```python
    from Tracer import Tracer
    from typing import Any, Callable, Optional, Type, Tuple
    from typing import Dict, Set, List, TypeVar, Union
    from types import FrameType, TracebackType
    
    class Collector(Tracer):
    
        def collect(self, frame: FrameType, event: str, arg: Any) -> None:
            pass
    
        def events(self) -> Set:
            return set()
    
        def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
            self.collect(frame, event, arg)
    ```
    
- 적용 방법
    
    ```python
    with Collector() as c:
        out = remove_html_markup('"abc"')
    out
    ```
    
    >  ‘abc’
    

### (2) Collector의 고유 식별자

- id() 메서드
    - 이벤트를 기록하는 과정에서 Collector의 고유 식별자 역할
        
        → 어떤 Collector가 어떤 이벤트를 추적하고 있는지를 명확히 알 수 있음
        
    - 프로그램 실행 중 첫 번째 함수 호출을 기반으로 생성
        - 첫 번째 함수 호출은 Collector가 추적을 시작한 시점을 나타내는 기준점이 됨
        - 디버깅 시 Collector의 컨텍스트를 식별하거나 디버깅 데이터를 그룹화할 때 유용

- 구현
    - 초기화
        
        ```python
        def __init__(self) -> None:
        		# 첫 번째로 호출된 함수 객체
            self._function: Optional[Callable] = None
            # 첫 호출 시 함수의 지역 변수 딕셔너리
            self._args: Optional[Dict[str, Any]] = None
            # 함수 호출 시의 인자
            self._argstring: Optional[str] = None
            # 첫 호출에서 발생한 예외
            self._exception: Optional[Type] = None
            # 추적에서 제외할 클래스와 함수 목록
            self.items_to_ignore: List[Union[Type, Callable]] = [self.__class__]
        ```
        
    - 추적
        
        ```python
        # 실행 흐름을 추적하고 첫 번째 함수 호출을 기록 & collect() 호출
        def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
        
        		# 추적 제외 처리
            for item in self.items_to_ignore:
                if (isinstance(item, type) and 'self' in frame.f_locals and
                    isinstance(frame.f_locals['self'], item)):
                    return
                if item.__name__ == frame.f_code.co_name:
                    return
                    
        		# 첫 함수 호출 기록
            if self._function is None and event == 'call':
                self._function = self.create_function(frame)
                self._args = frame.f_locals.copy()
                self._argstring = ", ".join([f"{var}={repr(self._args[var])}" for var in self._args])
                                           
            self.collect(frame, event, arg)
        ```
        

- 고유 ID 반환
    
    ```python
    # 첫 호출된 함수 이름과 인자 문자열로 구성된 고유 ID 반환
    def id(self) -> str:
    		return f"{self.function().__name__}({self.argstring()})"
    	
    # print 실행시 id 반환
    def __repr__(self) -> str:
        return self.id()
    ```
    
    ```python
    c.id()
    ```
    
    > "remove_html_markup(s='abc')”
    
- 저장된 값 반환
    
    ```python
    def function(self) -> Callable:
        if not self._function:
            raise ValueError("No call collected")
        return self._function
    ```
    
    ```python
    c.function()
    ```
    
    >  <function __main__.remove_html_markup(s)>
    
    ```python
    def argstring(self) -> str:
        if not self._argstring:
            raise ValueError("No call collected")
        return self._argstring
    ```
    
    ```python
    c.argstring()
    ```
    
    >  "s='abc'”
    
    ```python
    def args(self) -> Dict[str, Any]:
        if not self._args:
            raise ValueError("No call collected")
        return self._args
    ```
    
    ```python
    c.args()
    ```
    
    >  {'s': 'abc'}
    
    ```python
    def exception(self) -> Optional[Type]:
        return self._exception
    ```
    
- 수집 인프라 자체의 이벤트 수집 제외
    
    ```python
    def add_items_to_ignore(self, items_to_ignore: List[Union[Type, Callable]]) -> None:
        self.items_to_ignore += items_to_ignore
    ```
    

- 블록 종료 중 오류 방지 (아무것도 수집되지 않은 경우)
    
    ```python
    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        ret = super().__exit__(exc_tp, exc_value, exc_traceback)
        if not self._function:
            if exc_tp:
                return False  # re-raise exception
            else:
                raise ValueError("No call collected")
        return ret
    ```
    

- 추후 구현될 함수
    
    ```python
    Coverage = Set[Tuple[Callable, int]]
    
    def covered_functions(self) -> Set[Callable]:
        return set()
    
    def coverage(self) -> Coverage:
        return set()
    ```
    

### (3) Coverage Collector

- CoverageCollector 클래스 : 프로그램 실행 중 실행된 위치(함수와 라인 번호)를 수집
    - coverage informantion : 실행된 함수와 라인 번호로 구성된 정보
- 구현
    
    ```python
    from types import FrameType
    from StackInspector import StackInspector
    
    class CoverageCollector(Collector, StackInspector):
        def __init__(self) -> None:
            super().__init__()
    	      # 실행된 위치를 저장하는 집합 : (함수 객체, 라인 번호) 형태의 튜플로 Set 구성
            self._coverage: Coverage = set()
    ```
    
- 커버리지에 추가
    
    ```python
    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        # 현재 실행 중인 함수를 호출 스택에서 검색
        name = frame.f_code.co_name
        function = self.search_func(name, frame)
    		# 함수가 없으면 호출 스택에 추가
        if function is None:
            function = self.create_function(frame)
    		# 커버리지에 위치 추가
        location = (function, frame.f_lineno)
        self._coverage.add(location)
    ```
    
- 커버리지 정보 (함수명, 라인 번호) 반환
    
    ```python
    def events(self) -> Set[Tuple[str, int]]:
        return {(func.__name__, lineno) for func, lineno in self._coverage}
    ```
    
    ```python
    c.events()
    ```
    
    ![2024-12-06_05-50-22.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/f777ee3d-9080-434e-bb7a-b06f4e774fc1/2024-12-06_05-50-22.jpg)
    
- 함수 객체 집합 반환
    
    ```python
    def covered_functions(self) -> Set[Callable]:
        return {func for func, lineno in self._coverage}
    ```
    
- 함수 객체 포함 커버리지 정보 반환
    
    ```python
    def coverage(self) -> Coverage:
        return self._coverage
    ```
    

- 함수 소스코드 포함 반환
    
    ```python
    def code_with_coverage(function: Callable, coverage: Coverage) -> None:
        # 함수의 소스 코드와 시작 라인 번호 설정
        source_lines, starting_line_number = getsourcelines(function)
        # 첫 번째 라인의 번호 설정
        line_number = starting_line_number
        # 각 라인 앞에 실행 여부를 나타내는 별표 표시
        for line in source_lines:
            marker = '*' if (function, line_number) in coverage else ' '
            print(f"{line_number:4} {marker} {line}", end='')
            line_number += 1
    ```
    
    ```python
    code_with_coverage(remove_html_markup, c.coverage())
    ```
    
    ![2024-12-06_05-53-24.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/1028d765-3198-40df-8102-961875165577/2024-12-06_05-53-24.jpg)
    

## 3. 차이 계산

### (1) Statistical Debugger

- 차이 계산
    - 실패와 성공의 결과를 분석하기 위해서, 성공/실패의 이벤트를 비교하고 차이점을 찾아야 함
    - 성공과 실패에서 발생한 이벤트가 동일하다면, 해당 이벤트는 문제의 원인이 아님

- Statistical Debugger 설정
    
    ```python
    class StatisticalDebugger:
        """A class to collect events for multiple outcomes."""
    
        def __init__(self, collector_class: Type = CoverageCollector, log: bool = False):
            # 사용할 Collector 클래스 지정 (기본: CoverageCollector)
            self.collector_class = collector_class
            # 결과별 Collector 저장
            self.collectors: Dict[str, List[Collector]] = {}
            # 로그 출력 여부 설정
            self.log = log 
    ```
    

- 새 Collector 생성
    
    ```python
    def collect(self, outcome: str, *args: Any, **kwargs: Any) -> Collector:
    		# Collector 생성
        collector = self.collector_class(*args, **kwargs)
        # 디버깅 클래스 무시 설정
        collector.add_items_to_ignore([self.__class__])
        # 목록에 Collector 저장
        return self.add_collector(outcome, collector)
    ```
    
    ```python
    s = StatisticalDebugger()
    with s.collect('PASS'):
        remove_html_markup("abc")
    with s.collect('PASS'):
        remove_html_markup('<b>abc</b>')
    with s.collect('FAIL'):
        remove_html_markup('"abc"')
    ```
    
- 실행 결과에 따라 Collector 저장
    
    ```python
    def add_collector(self, outcome: str, collector: Collector) -> Collector:
    		# 결과에 대한 리스트 초기화
        if outcome not in self.collectors:
            self.collectors[outcome] = []
        # 목록에 추가 후 저장된 Collector 반환
        self.collectors[outcome].append(collector)
        return collector
    ```
    
    ```python
    s.collectors
    ```
    
    ![2024-12-06_06-46-16.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/0c8e9e25-2e96-4378-aef9-7eddd8232062/2024-12-06_06-46-16.jpg)
    
    ```python
    s.collectors['PASS'][0].id()
    ```
    
    ![2024-12-06_06-47-03.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/5d1e8d0d-42c9-407c-87da-938f3de061d9/2024-12-06_06-47-03.jpg)
    
    ```python
    s.collectors['PASS'][0].events()
    ```
    
    ![2024-12-06_06-47-18.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/65ee0450-a862-4409-93f8-7111529cff72/2024-12-06_06-47-18.jpg)
    

- 관찰된 모든 이벤트의 집합 반환
    - outcome 지정된 경우: 해당 결과에 대해 관찰된 이벤트만 통합
    - outcome 지정 안된 경우: 모든 실행 결과('PASS', 'FAIL' 등)에 대해 관찰된 이벤트를 통합
    
    ```python
    def all_events(self, outcome: Optional[str] = None) -> Set[Any]:
        all_events = set()
        # 특정 실행 결과에 대해
        if outcome:
            if outcome in self.collectors:
                for collector in self.collectors[outcome]:
                    all_events.update(collector.events())
        # 모든 실행 결과에 대해
        else:
            for outcome in self.collectors:
                for collector in self.collectors[outcome]:
                    all_events.update(collector.events())
    
        return all_events
    ```
    
    ```python
    s.all_events()
    ```
    
    ![2024-12-06_06-41-49.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d9b79da0-0295-45c0-886c-d63ffed8f7d0/2024-12-06_06-41-49.jpg)
    
    ```python
    s.all_events('FAIL')
    ```
    
    ![2024-12-06_06-42-13.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/44a91cab-fee5-42be-945c-6f52099c5ee0/2024-12-06_06-42-13.jpg)
    

### (2) Event Table

- 코드
    
    ```python
    from IPython.display import Markdown
    import html
    
    class StatisticalDebugger(StatisticalDebugger):
        def function(self) -> Optional[Callable]:
            """
            Return the entry function from the events observed,
            or None if ambiguous.
            """
            names_seen = set()
            functions = []
            for outcome in self.collectors:
                for collector in self.collectors[outcome]:
                    # We may have multiple copies of the function,
                    # but sharing the same name
                    func = collector.function()
                    if func.__name__ not in names_seen:
                        functions.append(func)
                        names_seen.add(func.__name__)
    
            if len(functions) != 1:
                return None  # ambiguous
            return functions[0]
    
        def covered_functions(self) -> Set[Callable]:
            """Return a set of all functions observed."""
            functions = set()
            for outcome in self.collectors:
                for collector in self.collectors[outcome]:
                    functions |= collector.covered_functions()
            return functions
    
        def coverage(self) -> Coverage:
            """Return a set of all (functions, line_numbers) observed"""
            coverage = set()
            for outcome in self.collectors:
                for collector in self.collectors[outcome]:
                    coverage |= collector.coverage()
            return coverage
    
        def color(self, event: Any) -> Optional[str]:
            """
            Return a color for the given event, or None.
            To be overloaded in subclasses.
            """
            return None
    
        def tooltip(self, event: Any) -> Optional[str]:
            """
            Return a tooltip string for the given event, or None.
            To be overloaded in subclasses.
            """
            return None
    
        def event_str(self, event: Any) -> str:
            """Format the given event. To be overloaded in subclasses."""
            if isinstance(event, str):
                return event
            if isinstance(event, tuple):
                return ":".join(self.event_str(elem) for elem in event)
            return str(event)
    
        def event_table_text(self, *, args: bool = False, color: bool = False) -> str:
            """
            Print out a table of events observed.
            If `args` is True, use arguments as headers.
            If `color` is True, use colors.
            """
            sep = ' | '
            all_events = self.all_events()
            longest_event = max(len(f"{self.event_str(event)}") 
                                for event in all_events)
            out = ""
    
            # Header
            if args:
                out += '| '
                func = self.function()
                if func:
                    out += '`' + func.__name__ + '`'
                out += sep
                for name in self.collectors:
                    for collector in self.collectors[name]:
                        out += '`' + collector.argstring() + '`' + sep
                out += '\n'
            else:
                out += '| ' + ' ' * longest_event + sep
                for name in self.collectors:
                    for i in range(len(self.collectors[name])):
                        out += name + sep
                out += '\n'
    
            out += '| ' + '-' * longest_event + sep
            for name in self.collectors:
                for i in range(len(self.collectors[name])):
                    out += '-' * len(name) + sep
            out += '\n'
    
            # Data
            for event in sorted(all_events):
                event_name = self.event_str(event).rjust(longest_event)
    
                tooltip = self.tooltip(event)
                if tooltip:
                    title = f' title="{tooltip}"'
                else:
                    title = ''
    
                if color:
                    color_name = self.color(event)
                    if color_name:
                        event_name = \
                            f'<samp style="background-color: {color_name}"{title}>' \
                            f'{html.escape(event_name)}' \
                            f'</samp>'
    
                out += f"| {event_name}" + sep
                for name in self.collectors:
                    for collector in self.collectors[name]:
                        out += ' ' * (len(name) - 1)
                        if event in collector.events():
                            out += "X"
                        else:
                            out += "-"
                        out += sep
                out += '\n'
    
            return out
    
        def event_table(self, **_args: Any) -> Any:
            """Print out event table in Markdown format."""
            return Markdown(self.event_table_text(**_args))
    
        def __repr__(self) -> str:
            return self.event_table_text()
    
        def _repr_markdown_(self) -> str:
            return self.event_table_text(args=True, color=True)
    ```
    
- ex.
    
    ```python
    s = StatisticalDebugger()
    with s.collect('PASS'):
        remove_html_markup("abc")
    with s.collect('PASS'):
        remove_html_markup('<b>abc</b>')
    with s.collect('FAIL'):
        remove_html_markup('"abc"')
    
    s.event_table(args=True)
    ```
    
    ![2024-12-06_06-52-30.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/3bae4098-f327-4095-929a-95a02d316cd2/2024-12-06_06-52-30.jpg)
    

### (3) Difference Debugger

- DifferenceDebugger 클래스
    - StatisticalDebugger를 확장하여 성공 실행(Passing Runs)과 실패 실행(Failing Runs)을 보다 쉽게 수집하고 분석할 수 있도록 설계된 특화 클래스

1. 테스트의 결과가 미리 결정되는 경우
    - 코드
        - 구현
            
            ```python
            class DifferenceDebugger(StatisticalDebugger):
            
                PASS = 'PASS'
                FAIL = 'FAIL'
            
                def collect_pass(self, *args: Any, **kwargs: Any) -> Collector:
                    return self.collect(self.PASS, *args, **kwargs)
            
                def collect_fail(self, *args: Any, **kwargs: Any) -> Collector:
                    return self.collect(self.FAIL, *args, **kwargs)
            ```
            
        - Collector 조회
            
            ```python
            def pass_collectors(self) -> List[Collector]:
                return self.collectors[self.PASS]
            
            def fail_collectors(self) -> List[Collector]:
                return self.collectors[self.FAIL]
            ```
            
        - 모든 이벤트 조회
            
            ```python
            def all_fail_events(self) -> Set[Any]:
                return self.all_events(self.FAIL)
            
            def all_pass_events(self) -> Set[Any]:
                return self.all_events(self.PASS)
            ```
            
        - 실행 간 차이 분석
            
            ```python
            # 실패 실행에서만 관찰된 이벤트를 반환
            def only_fail_events(self) -> Set[Any]:
                return self.all_fail_events() - self.all_pass_events()
            
            # 성공 실행에서만 관찰된 이벤트를 반환
            def only_pass_events(self) -> Set[Any]:
                return self.all_pass_events() - self.all_fail_events()
            ```
            
        

1. 확장된 인터페이스
    
    ```python
    class DifferenceDebugger(DifferenceDebugger):
        def __enter__(self) -> Any:
    		    # Collector 생성
    		    self.collector = self.collector_class()
    		    # 디버거 클래스 무시
            self.collector.add_items_to_ignore([self.__class__])
            self.collector.__enter__()
            return self
    
        def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
     
            status = self.collector.__exit__(exc_tp, exc_value, exc_traceback)
            if status is None:
                pass
            else:
                return False  # Internal error; re-raise exception
    
    				# 실행 결과를 PASS 또는 FAIL로 분류
            if exc_tp is None:
                outcome = self.PASS
            else:
                outcome = self.FAIL
    
    				# Collector를 실행 결과에 따라 저장
            self.add_collector(outcome, self.collector)
            return True  # Ignore exception, if any
    ```
    
- 실행
    
    ```python
    T2 = TypeVar('T2', bound='DifferenceDebugger')
    
    def test_debugger_html(debugger: T2) -> T2:
        with debugger:
            remove_html_markup('abc')
        with debugger:
            remove_html_markup('<b>abc</b>')
        with debugger:
            remove_html_markup('"abc"')
            assert False  # Mark test as failing
        return debugger
        
    test_debugger_html(DifferenceDebugger())
    ```
    
    ![2024-12-06_07-14-00.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/45da3af0-37b1-424c-af88-8c3e933a5972/2024-12-06_07-14-00.jpg)
    

## 4. 차이 시각화

### (1) Discrete Spectrum Debugger

- 실행 결과 간의 차이를 시각화하기 위해 코드의 커버리지 정보를 색상으로 강조하는 기술

- 불연속 스펙트럼
    - 빨강 : 실패 실행에서만 실행된 코드
    - 초록 : 성공 실행에서만 실행된 코드
    - 노랑 : 성공과 실패 실행 모두에서 실행된 코드
    - 하이라이트되지 않음 : 실행되지 않은 코드

- SpectrumDebugger
    - 이벤트의 의심 수준(suspiciousness)을 계산하는 기능을 제공하는 추상 클래스
    - suspiciousness: 이벤트가 실패와 얼마나 관련이 있는지를 나타내는 값으로, 0에서 1 사이의 범위
        - 0 : 실패와 전혀 관련이 없는 이벤트
        - 1 : 실패와 매우 관련이 있는 이벤트
        - None : 이벤트의 의심 수준을 계산할 수 없는 경우

- 추상 함수 설정
    
    ```python
    class SpectrumDebugger(DifferenceDebugger):
    		# 특정 이벤트의 suspiciousness 반환
        def suspiciousness(self, event: Any) -> Optional[float]:
            return None
    
    		# 특정 이벤트의 툴팁 반환 (기본적으로는 퍼센트 반환)
    		def tooltip(self, event: Any) -> str:
    		    return self.percentage(event)
    		    
    		# 특정 이벤트의 suspiciousness의 퍼센트 수치 반환
    		def percentage(self, event: Any) -> str:
    		    suspiciousness = self.suspiciousness(event)
    		    if suspiciousness is not None:
    		        return str(int(suspiciousness * 100)).rjust(3) + '%'
    		    else:
    		        return ' ' * len('100%')
    ```
    
- 소스코드 출력
    
    ```python
        def code(self, functions: Optional[Set[Callable]] = None, *, 
                 color: bool = False, # True : HTML 렌더링으로 suspiciousness 색상 표시
                 suspiciousness: bool = False, # True : suspiciousness 값 추가
                 line_numbers: bool = True) -> str: # True : 라인 번호 추가
    
    				# 함수 목록 미지정시 기존적으로 지정된 함수 목록 사용
            if not functions:
                functions = self.covered_functions()
    
            out = ""
            
            # 각 함수의 소스 코드 추출
            seen = set()
            for function in functions:
                source_lines, starting_line_number = inspect.getsourcelines(function)
                if (function.__name__, starting_line_number) in seen:
                    continue
                seen.add((function.__name__, starting_line_number))
                if out:
                    out += '\n'
                    if color:
                        out += '<p/>'
    						# 함수의 각 줄에 대해 의심 수준 & 툴팁 추출
                line_number = starting_line_number
                for line in source_lines:
                    if color:
                        line = html.escape(line)
                        if line.strip() == '':
                            line = '&nbsp;'
                    location = (function.__name__, line_number)
                    location_suspiciousness = self.suspiciousness(location)
                    if location_suspiciousness is not None:
                        tooltip = f"Line {line_number}: {self.tooltip(location)}"
                    else:
                        tooltip = f"Line {line_number}: not executed"
                    if suspiciousness:
                        line = self.percentage(location) + ' ' + line
                    if line_numbers:
                        line = str(line_number).rjust(4) + ' ' + line
                    line_color = self.color(location)
                    if color and line_color:
                        line = f'''<pre style="background-color:{line_color}"
                        title="{tooltip}">{line.rstrip()}</pre>'''
                    elif color:
                        line = f'<pre title="{tooltip}">{line}</pre>'
                    else:
                        line = line.rstrip()
                    out += line + '\n'
                    line_number += 1
    
            return out
    ```
    
- 출력 방식 조정
    
    ```python
    # Jupyter Notebook 환경에서 객체를 출력할 때 HTML 형식으로 렌더링
    def _repr_html_(self) -> str:
        return self.code(color=True)
    
    # 객체를 문자열로 출력할 때 호출
    def __str__(self) -> str:
        return self.code(color=False, suspiciousness=True)
    
    # 객체를 출력할 때 호출
    def __repr__(self) -> str:
        """Show code as string"""
        return self.code(color=False, suspiciousness=True)
    ```
    

- DiscreteSpectrumDebugger 클래스
    - 의심 수준(suspiciousness)과 색상(color) 계산 방식을 구체적으로 구현
    - 의심 수준
        
        ```python
        class DiscreteSpectrumDebugger(SpectrumDebugger):
            
            def suspiciousness(self, event: Any) -> Optional[float]:
                passing = self.all_pass_events()
                failing = self.all_fail_events()
                # 실패만 발생 1.0, 성공만 발생 0.0, 실패 성공 모두 발생 0.5
                if event in passing and event in failing:
                    return 0.5
                elif event in failing:
                    return 1.0
                elif event in passing:
                    return 0.0
                else:
                    return None
        ```
        
    - 색상
        
        ```python
        def color(self, event: Any) -> Optional[str]:
            suspiciousness = self.suspiciousness(event)
            if suspiciousness is None:
                return None  # 실행되지 않은 코드
            if suspiciousness > 0.8:
                return 'mistyrose'  # 실패 실행에서만 발생
            if suspiciousness >= 0.5:
                return 'lightyellow'  # 성공과 실패 모두에서 발생
        
            return 'honeydew'  # 성공 실행에서만 발생
        ```
        
    - 툴팁
        
        ```python
        def tooltip(self, event: Any) -> str:
            passing = self.all_pass_events()
            failing = self.all_fail_events()
            if event in passing and event in failing:
                return "in passing and failing runs"
            elif event in failing:
                return "only in failing runs"
            elif event in passing:
                return "only in passing runs"
            else:
                return "never"
        ```
        
    - 예시
        
        ```python
        def test_debugger_html(debugger: T2) -> T2:
            with debugger:
                remove_html_markup('abc')
            with debugger:
                remove_html_markup('<b>abc</b>')
            with debugger:
                remove_html_markup('"abc"')
                assert False
                
        debugger = test_debugger_html(DiscreteSpectrumDebugger())
        debugger
        ```
        
        ![2024-12-06_17-15-27.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/fcfb365d-f22b-4a88-9687-0c8f2d0cb295/2024-12-06_17-15-27.jpg)
        
        ```python
        print(debugger)
        ```
        
        ![2024-12-06_17-17-30.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ce57e318-d370-44f8-bbf5-6a68d64e31e1/2024-12-06_17-17-30.jpg)
        
    - 분석
        - Line 12: 프로그램의 실패 원인 중 하나로 관찰된 증상(symptom)
        - 이 줄을 주석 처리하거나 제거하면 현재 실패는 해결될 수 있지만, 이는 부작용으로 인해 다른 실패를 초래할 가능성이 큼
        - 진짜 defect = Line 12가 실행되도록 한 이전 조건문(Line 11)

### (2) Continuous Spectrum Debugger

- 이벤트가 오직 실패 실행에서만 발생해야 한다는 엄격한 기준의 한계를 보완하기 위해 도입
    - 실패를 초래하는 문제의 코드 줄(culprit line)이 성공 실행에서도 실행될 수 있음

- Tarantula 도구
    - 각 코드 줄의 색상(hue)을 실패 실행과 성공 실행 간의 상대적인 실행 비율에 따라 설정하여 코드의 의심 수준을 시각화
    - 실패 실행에서 더 많이 실행 → 색상이 빨간색에 가까움
    - 성공 실행에서 더 많이 실행 → 색상이 초록색에 가까움
        
        ![2024-12-06_17-25-07.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/8413c541-8fba-4760-9e2e-cc0fdb8d6fe5/2024-12-06_17-25-07.jpg)
        

- 구현
    
    ```python
    class ContinuousSpectrumDebugger(DiscreteSpectrumDebugger):
    
    		# 주어진 이벤트를 관찰한 Collector(실행 데이터)를 반환
        def collectors_with_event(self, event: Any, category: str) -> Set[Collector]:
            all_runs = self.collectors[category]
            collectors_with_event = set(collector for collector in all_runs 
                                        if event in collector.events())
            return collectors_with_event
    
    		# 주어진 이벤트를 실행하지 않은 Collector를 반환
        def collectors_without_event(self, event: Any, category: str) -> Set[Collector]:
            all_runs = self.collectors[category]
            collectors_without_event = set(collector for collector in all_runs 
                                           if event not in collector.events())
            return collectors_without_event
    ```
    
- Collector 비율 계산
    
    ```python
    def event_fraction(self, event: Any, category: str) -> float:
        if category not in self.collectors:
            return 0.0
        all_collectors = self.collectors[category]
        collectors_with_event = self.collectors_with_event(event, category)
        fraction = len(collectors_with_event) / len(all_collectors)
        return fraction
        
    # 특정 이벤트가 성공 실행에서 실행된 비율을 반환
    def passed_fraction(self, event: Any) -> float:
        return self.event_fraction(event, self.PASS)
        
    # 특정 이벤트가 실패 실행에서 실행된 비율을 반환
    def failed_fraction(self, event: Any) -> float:
        return self.event_fraction(event, self.FAIL)
    ```
    
- Hue 계산
    
    ```python
    def hue(self, event: Any) -> Optional[float]:
        passed = self.passed_fraction(event)
        failed = self.failed_fraction(event)
        if passed + failed > 0:
            return passed / (passed + failed)
        else:
            return None
    ```
    
- 오버라이드
    
    ```python
    def suspiciousness(self, event: Any) -> Optional[float]:
        hue = self.hue(event)
        if hue is None:
            return None
        return 1 - hue
        
    def tooltip(self, event: Any) -> str:
        return self.percentage(event)
    ```
    
- ex.
    
    ```python
    for location in debugger.only_fail_events():
        print(location, debugger.hue(location))
    ```
    
    ![2024-12-06_17-32-28.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/f090c7db-b6d9-469d-9d34-2572c510bd2f/2024-12-06_17-32-28.jpg)
    
    ```python
    for location in debugger.only_pass_events():
        print(location, debugger.hue(location))
    ```
    
    ![2024-12-06_17-32-44.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ec2f463a-5ba1-47ae-91c0-46b7d0010152/2024-12-06_17-32-44.jpg)
    

- Brightness
    - 색상(Hue)뿐만 아니라 밝기(Brightness)를 사용하여 각 코드 줄의 실행 빈도(Support)를 시각화
    - 밝기는 해당 줄이 얼마나 자주 실행되었는지에 따라 달라지며, 실행 빈도가 높을수록 더 밝게 표시
        
        ![2024-12-06_17-33-40.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/9af415fe-9b80-408a-94a9-e7de3dca98b0/2024-12-06_17-33-40.jpg)
        
    - 구현
        
        ```python
        def brightness(self, event: Any) -> float:
            return max(self.passed_fraction(event), self.failed_fraction(event))
        ```
        

- Color
    - 각 이벤트(코드 줄)에 대해 Hue와 Brightness 값을 조합하여 HSL 색상을 반환
    - Hue는 실패/성공 실행 간의 상관성, Brightness는 실행 빈도를 반영
    - 구현
        
        ```python
        def color(self, event: Any) -> Optional[str]:
            hue = self.hue(event)
            if hue is None:
                return None
            saturation = self.brightness(event)
            return f"hsl({hue * 120}, {saturation * 100}%, 80%)"
        ```
        
    - ex.
        
        ```python
        for location in debugger.only_fail_events():
            print(location, debugger.color(location))
        ```
        
        ![2024-12-06_17-35-46.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/cb116273-7160-43a4-805e-246a9e4f8acc/2024-12-06_17-35-46.jpg)
        
        ```python
        debugger
        ```
        
        ![2024-12-06_17-36-00.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/fd1f42fc-7c92-41bd-974a-3d44ce10f20c/2024-12-06_17-36-00.jpg)
        

## 5. 의심 순위

### (1) Ranking Debugger

- Ranking
    - 코드가 큰 경우, 실패 실행에서 주로 실행된 의심스러운 코드 블록이 여러 줄일 수 있음
    - 우선순위 제공 : 실패와 강하게 상관관계가 있는 코드 줄을 상위에 표시
    - 코드 전체를 살펴보는 대신, 실패와 가장 관련이 있는 코드부터 조사 가능
- 구현
    
    ```python
    class RankingDebugger(DiscreteSpectrumDebugger):
    
    		# 이벤트의 의심 수준을 기준으로 내림차순 정렬된 이벤트 목록을 반환
        def rank(self) -> List[Any]:
    
    				# suspiciousness(event) 메서드를 호출하여 특정 이벤트의 의심 수준을 계산
            def susp(event: Any) -> float:
                suspiciousness = self.suspiciousness(event)
                assert suspiciousness is not None
                return suspiciousness
    
            events = list(self.all_events())
            events.sort(key=susp, reverse=True)
            return events
    
    		# 순위 목록을 문자열로 반환
        def __repr__(self) -> str:
            return repr(self.rank())
    ```
    

### (2) Tarantula Metric

- 프로그램 실행 중 특정 코드 줄이 실패와 얼마나 관련이 있는지를 계산하는 디버깅 기법
- 코드 줄의 “빨간색” 정도(redness)를 기반으로 의심 수준(suspiciousness)을 평가
    - 빨간색이 짙을수록 해당 코드가 실패와 강하게 연관
        
        ![2024-12-07_07-47-02.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/fd923b5e-903f-471c-9093-9cab57990b25/2024-12-07_07-47-02.jpg)
        

- 위의 ContinuousSpectrumDebugger에서 이미 구현됨
    
    ```python
    class TarantulaDebugger(ContinuousSpectrumDebugger, RankingDebugger):
        pass
    ```
    
    ```python
    tarantula_html = test_debugger_html(TarantulaDebugger())
    tarantula_html.rank()
    ```
    
    ![2024-12-07_07-49-08.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/c38c7a52-57b3-4b1b-bf50-04bb6d3ff0a2/2024-12-07_07-49-08.jpg)
    

### (3) Ochiai Metric

- 특정 이벤트(코드 줄 또는 실행)가 실패와 얼마나 강하게 관련되어 있는지를 정량적으로 평가
- 공식
    
    ![2024-12-07_07-49-42.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/30488f88-eeaa-4fbf-8427-15efb33c7ea2/2024-12-07_07-49-42.jpg)
    
    - failed(event): 실패 실행에서 이벤트가 발생한 횟수
    - passed(event): 성공 실행에서 이벤트가 발생한 횟수
    - total failed runs: 전체 실패 실행의 수
- 구현
    
    ```python
    import math
    
    class OchiaiDebugger(ContinuousSpectrumDebugger, RankingDebugger):
    
        def suspiciousness(self, event: Any) -> Optional[float]:
            failed = len(self.collectors_with_event(event, self.FAIL))
            not_in_failed = len(self.collectors_without_event(event, self.FAIL))
            passed = len(self.collectors_with_event(event, self.PASS))
    
            try:
                return failed / math.sqrt((failed + not_in_failed) * (failed + passed))
            except ZeroDivisionError:
                return None
    
        def hue(self, event: Any) -> Optional[float]:
            suspiciousness = self.suspiciousness(event)
            if suspiciousness is None:
                return None
            return 1 - suspiciousness
    ```
    
- ex.
    
    ```python
    ochiai_html = test_debugger_html(OchiaiDebugger())
    ochiai_html.rank()
    ```
    
    ![2024-12-07_07-52-02.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/0932598a-9948-4097-a278-2d7b9e1265df/2024-12-07_07-52-02.jpg)
    

### (4) 랭킹 비교

- Metric의 성능
    - Ground Truth(정답)을 기준으로 평가
        - 결함이 존재했던 코드 줄이 순위 목록에서 얼마나 빨리 나타나는지
    1. Tarantula : 최초의 메트릭, 단순하지만 유효
    2. Ochiai : 가장 효과적인 메트릭, 실패와 성공 간의 상관성을 수학적으로 정밀하게 반영
    
- 한계
    - 개발자가 특정 코드 줄의 결함 여부를 단순히 해당 줄을 보기만 해서 판단할 수 없을 가능성이 높음
    - 결함 있는 줄의 순위를 인위적으로 바꾸어도 개발자에게 큰 영향을 미치지 않음

## 6. 추가적인 기능

### (1) Large Test Suites

- Test Suite
    - 결함 위치 추적(Fault Localization)에서 테스트의 수와 다양성은 결과의 정확도를 높이는 핵심 요소
    - 코드의 더 많은 경로를 실행하여 더 정밀한 결함 추적을 할 수 있음

- ex.
    
    ```python
    # 세 개의 난수(x, y, z)를 생성하여 테스트 케이스로 반환
    def middle_testcase() -> Tuple[int, int, int]:
        x = random.randrange(10)
        y = random.randrange(10)
        z = random.randrange(10)
        return x, y, z
    
    # 주어진 값 x, y, z를 middle() 함수에 전달하고, 결과가 올바른지 확인
    def middle_test(x: int, y: int, z: int) -> None:
        m = middle(x, y, z)
        assert m == sorted([x, y, z])[1]
    ```
    
    ```python
    # 무작위 테스트 케이스를 생성한 후 middle()이 성공적으로 작동하는 테스트 케이스를 반환
    def middle_passing_testcase() -> Tuple[int, int, int]:
        while True:
            try:
                x, y, z = middle_testcase()
                middle_test(x, y, z)
                return x, y, z
            except AssertionError:
                pass
                
    # 무작위 테스트 케이스를 생성한 후 middle()이 실패하는 테스트 케이스를 반환
    def middle_failing_testcase() -> Tuple[int, int, int]:
        while True:
            try:
                x, y, z = middle_testcase()
                middle_test(x, y, z)
            except AssertionError:
                return x, y, z
    ```
    
    ```python
    MIDDLE_TESTS = 100
    MIDDLE_PASSING_TESTCASES = [middle_passing_testcase() for i in range(MIDDLE_TESTS)]
    MIDDLE_FAILING_TESTCASES = [middle_failing_testcase() for i in range(MIDDLE_TESTS)]
    ```
    
    ```python
    ochiai_middle = OchiaiDebugger()
    
    for x, y, z in MIDDLE_PASSING_TESTCASES:
        with ochiai_middle.collect_pass():
            middle(x, y, z)
    
    for x, y, z in MIDDLE_FAILING_TESTCASES:
        with ochiai_middle.collect_fail():
            middle(x, y, z)
            
    ochiai_middle
    ```
    
    ![2024-12-09_01-30-27.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/e63340f3-79ba-4c52-8340-e4d0738cee25/2024-12-09_01-30-27.jpg)
    

### (2) Value Collector

- **커버리지**뿐만 아니라 실행 중 추출할 수 있는 **모든 데이터**를 이벤트로 처리하여 상관분석에 활용할 수 있음
- 구현
    
    ```python
    class ValueCollector(Collector):
    
    		# 수집한 변수와 값 저장
        def __init__(self) -> None:
            super().__init__()
            self.vars: Set[str] = set()
    
        def collect(self, frame: FrameType, event: str, arg: Any) -> None:
            local_vars = frame.f_locals  
            for var in local_vars:
                value = local_vars[var]
                self.vars.add(f"{var} = {repr(value)}") 
    
        def events(self) -> Set[str]:
            return self.vars
    ```
    
- ex.
    
    ```python
    for event in debugger.only_fail_events():
        print(event)
    ```
    
    ![2024-12-09_01-53-25.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/6b6291f9-6144-46c9-b538-73b6c61f09b4/2024-12-09_01-53-25.jpg)