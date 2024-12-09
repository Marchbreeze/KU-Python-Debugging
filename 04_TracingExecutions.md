## 1. 추적 함수

- 파이썬 : Interpreted 언어이므로 프로그램 실행 중 상태에 접근하는 것이 비교적 쉬움
    - 일반적으로 실행을 제어하고 상태를 검사하는 작업을 interperter가 이미 수행 중

- `sys.settrace()`
    - Debugger : 실행을 중단하고 상태에 접근하는 `Hook` 위에 구현됨
    - 파이썬은 sys.settrace() 함수에서 이러한 후크를 제공
    - sys.settrace(traceit) → 각 줄이 실행될 때마다 추적 함수(traceit)가 호출
    - 실행 기록을 남기기 위해 유용
    - interactive debugger와 달리, 특정 부분을 선택할 필요 없이 모든 것을 추적

- `추적 함수`
    
    ```python
    from types import FrameType, TracebackType
    from typing import Any, Optional, Callable, Dict, List, Type, TextIO, cast
    
    def traceit(frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        print(event, frame.f_lineno, frame.f_code.co_name, frame.f_locals)
        return traceit
    ```
    
    - `frame` 매개변수
        - 현재의 실행 프레임을 나타내며, 현재 함수와 지역 변수를 포함
        - frame.f_lineno : 현재 실행 중인 줄 번호
        - frame.f_locals : 현재 함수의 지역 변수(딕셔너리 형태)
        - frame.f_code : 현재 코드 객체, co_name 속성을 통해 함수 이름에 접근
    - `event` 매개변수
        - 프로그램에서 발생한 일을 나타내는 문자열
        - 'line' – 새로운 줄이 실행되었음을 나타냄
        - 'call' – 함수가 호출되었음을 나타냄
        - 'return' – 함수가 반환되었음을 나타냄

- 이전 디버깅 과정에 적용
    
    ```python
    from Intro_Debugging import remove_html_markup
    import sys
    
    def remove_html_markup_traced(s):
        sys.settrace(traceit)
        ret = remove_html_markup(s)
        sys.settrace(None)
        return ret
    
    remove_html_markup_traced('xyz')
    ```
    
    ![2024-11-04_00-11-15.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/54a0d35a-439f-4053-8eac-4194e8d6fd84/2024-11-04_00-11-15.jpg)
    
    ![2024-11-04_00-11-35.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ec2668ca-e46d-48d7-9564-be853fe18aaf/2024-11-04_00-11-35.jpg)
    

- 실행 중에 함수의 지역 변수(c)에 대해서도 객체로 조회할 수 있음
    
    ```python
    # for c in s 에서의 c 조회
    def traceit(frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        if 'c' in frame.f_locals:
            value_of_c = frame.f_locals['c']
            print(f"{frame.f_lineno:} c = {repr(value_of_c)}")
        else:
            print(f"{frame.f_lineno:} c is undefined")
    
        return traceit
    ```
    
    ![2024-11-04_01-36-02.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/8ed308fb-2d62-4cd6-8ea4-2913e4c60220/2024-11-04_01-36-02.jpg)
    
    ![2024-11-04_01-36-16.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d39f4013-413c-4ddb-bedd-de7c9f84b753/2024-11-04_01-36-16.jpg)
    

- 추적함수가 None을 반환하는 경우
    - traceit 함수가 None을 반환하면, 함수 f()에 대한 추적이 중지됨
    - 그러나 f()가 완전히 반환되면, 추적 함수는 다시 호출되어 함수의 반환 이벤트가 기록
    - 특정 함수의 자세한 실행 흐름 추적이 필요하지 않을 때, 추적을 일시적으로 중지하는 데 유용한 방식

## 2. Tracer Class

- Tracer 클래스
    - 추적 기능을 커스터마이즈할 수 있도록 조정
    - 추적 출력을 형식화하고, 서브클래싱을 통해 다양한 출력 형식을 제공
    - traceit() : 기존 추적 함수와 동일 (print() 대신 `log()`)
    - 일반적인 사용 방식
        
        ```python
        with Tracer():
            # 추적할 코드
            ...
        
        # 더 이상 추적되지 않는 코드
        ...
        ```
        

- 오류 발생 시 더 나은 진단을 제공하는 `StackInspector` 클래스 위에 Tracer를 구축
    - with 구문이 시작되면 `__enter__()` 메서드가 호출되어 추적이 시작
    - with 블록이 끝나면 `__exit__()` 메서드가 호출되어 추적이 중지
    - StackInspector
        
        ```python
        from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
        import inspect
        import traceback
        
        class StackInspector:
            def caller_frame(self) -> FrameType:
                frame = cast(FrameType, inspect.currentframe())
                while self.our_frame(frame):
                    frame = cast(FrameType, frame.f_back)
                return frame
        
            def our_frame(self, frame: FrameType) -> bool:
                return isinstance(frame.f_locals.get('self'), self.__class__)
            
            def is_internal_error(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> bool:
                if not exc_tp:
                    return False
                for frame, lineno in traceback.walk_tb(exc_traceback):
                    if self.our_frame(frame):
                        return True
                return False
        ```
        
    - 구현 코드
        
        ```python
        from StackInspector import StackInspector
        
        """ StackInspector 클래스를 상속, `with Tracer(): block()`으로 사용 """
        class Tracer(StackInspector):
        
        		""" 코드 블록을 추적하고 로그를 file로 보냄 (기본값은 콘솔 출력) """
            def __init__(self, *, file: TextIO = sys.stdout) -> None:
                self.original_trace_function: Optional[Callable] = None
                self.file = file
        
        		""" 추적함수 (서브클래스에서 재정의 가능) """
            def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
                self.log(event, frame.f_lineno, frame.f_code.co_name, frame.f_locals)
        
        		""" 내부 추적함수 (클래스 내부 메서드를 추적에서 제외) """
            def _traceit(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
                if self.our_frame(frame):
                    pass
                else:
                    self.traceit(frame, event, arg)
                return self._traceit
        
        		""" 디버깅 로그 즉각 출력 : file에 데이터를 즉시 반영하도록 자동 플러시 기능을 제공 """
            def log(self, *objects: Any, sep: str = ' ', end: str = '\n', flush: bool = True) -> None:
                print(*objects, sep=sep, end=end, file=self.file, flush=flush)
        
        		""" with 블록의 시작 시 호출 """
            def __enter__(self) -> Any:
                self.original_trace_function = sys.gettrace()
                sys.settrace(self._traceit)
                # 하단 줄은 현재 블록에 대한 추적을 활성화하는 데도 사용
                # inspect.currentframe().f_back.f_trace = self._traceit
                return self
        
        		""" with 블록의 종료 시 호출, 문제가 없으면 None을 반환, 오류 시 아닌 값을 반환 """
            def __exit__(self, exc_tp: Type, exc_value: BaseException, 
                         exc_traceback: TracebackType) -> Optional[bool]:
                sys.settrace(self.original_trace_function)
        
                # True가 아닌 값을 반환해야 with 구문 내부에서 발생한 예외가 프로그램 흐름에 맞게 처리됨
                if self.is_internal_error(exc_tp, exc_value, exc_traceback):
                    return False  # internal error
                else:
                    return None  # all ok
        ```
        
    - 실행
        
        ```python
        with Tracer():
            remove_html_markup("abc")
        ```
        
        ![2024-11-04_02-26-37.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/8a5c0265-0bda-4473-8132-8284aaa32469/2024-11-04_02-26-37.jpg)
        
        ![2024-11-04_02-26-46.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/11944ada-93e9-48d4-b412-1790522c33d0/2024-11-04_02-26-46.jpg)
        

## 3. 소스 코드 접근

- 현재 실행 중인 함수의 소스 코드를 가져오고, 이를 추적 기능에 추가
    - Tracer 클래스에 새로운 기능을 추가하여 추적 중인 함수의 소스 코드를 보여줄 수 있도록 함
    - 소스 코드를 표시하면 현재 코드가 어디에서 실행되고 있는지를 더 명확히 파악할 수 있음

- inspect 모듈 활용
    
    ```python
    # 현재 모듈을 frame.f_code를 통해 가져옴
    module = inspect.getmodule(frame.f_code)
    # 해당 모듈의 소스 코드를 inspect.getsource()를 사용해 가져옴
    inspect.getsource(module)
    ```
    

- 서브클래스로 덮어쓰는 방식 활용
    - C 클래스를 이전의 C 클래스의 서브클래스처럼 정의하여 new_method()를 추가하는 방법
    - 기존 C 클래스의 정의에 새로운 메서드가 추가된 새로운 C 클래스가 생성되며, 이전 정의는 덮어쓰게 됨
    - 단, 이미 생성된 C 객체들은 여전히 이전 정의를 사용하므로, 이 객체들을 새로 만들어야 새로운 정의를 반영할 수 있움
        
        ```python
        class C(C):
            def new_method(self, args):
                pass
        ```
        

- 기존 Tracer 클래스 덮어쓰기
    
    ```python
    class Tracer(Tracer):
        def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
    			if event == 'call':
                self.log(f"Calling {frame.f_code.co_name}()")
    
            if event == 'line':
                module = inspect.getmodule(frame.f_code)
                if module:
                    source = inspect.getsource(module)
                if source:
                    current_line = source.split('\n')[frame.f_lineno - 1]
                    self.log(frame.f_lineno, current_line)
    
            if event == 'return':
                self.log(f"{frame.f_code.co_name}() returns {repr(arg)}")
    ```
    
    ```python
    with Tracer():
        remove_html_markup("abc")
    ```
    
    ![2024-11-04_02-34-29.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/ccea611a-b21a-4a37-9b8c-d157d08594a3/2024-11-04_02-34-29.jpg)
    

## 4. 변수의 변화 감지

- Tracer 클래스에 마지막으로 보고된 변수들의 복사본을 저장하고, 새로운 값과 비교하여 변경된 값만 보고
    
    ```python
    class Tracer(Tracer):
    		""" 새 Tracer 객체 생성 """
        def __init__(self, file: TextIO = sys.stdout) -> None:
    		    # 마지막에 보고된 변수들을 저장하는 딕셔너리 설정 -> 이전 상태와 비교하여 변경된 변수만 식별
            self.last_vars: Dict[str, Any] = {}
            super().__init__(file=file)
    
    		""" new_vars에 있는 변수들 중 변경된 변수들만 추적하여 반환 """
        def changed_vars(self, new_vars: Dict[str, Any]) -> Dict[str, Any]:
            changed = {}
            # new_vars에 있는 각 변수 이름(var_name)과 값을 가져와
            # last_vars에 해당 변수가 없거나, last_vars에 저장된 값과 현재 new_vars 값이 다르면
            # 변경된 변수로 간주하고 changed에 추가
            for var_name, var_value in new_vars.items():
                if (var_name not in self.last_vars or self.last_vars[var_name] != var_value):
                    changed[var_name] = var_value
            # self.last_vars를 현재의 new_vars로 복사하여 업데이트
            self.last_vars = new_vars.copy()
            return changed
    ```
    
- 예시
    
    ```python
    tracer = Tracer()
    tracer.changed_vars({'a': 10})
    ```
    
    >  {'a': 10}
    
    ```python
    tracer.changed_vars({'a': 10, 'b': 25})
    ```
    
    >  {'b': 25}
    
    ```python
    tracer.changed_vars({'a': 10, 'b': 25})
    ```
    
    >  {}
    
    ```python
    changes = tracer.changed_vars({'c': 10, 'd': 25})
    changes
    ```
    
    >  {'c': 10, 'd': 25}
    

- 기존 Tracer에 적용
    
    ```python
    class Tracer(Tracer):
    		""" 현재 소스 코드와 변경된 변수를 출력하는 메서드 """
        def print_debugger_status(self, frame: FrameType, event: str, arg: Any) -> None:
            
            # 현재 상태에서 변경된 변수만 필터링 후 "변수명 = 값" 형식으로 변환
            changes = self.changed_vars(frame.f_locals)
            changes_s = ", ".join([var + " = " + repr(changes[var]) for var in changes])
    
            if event == 'call':
                self.log("Calling " + frame.f_code.co_name + '(' + changes_s + ')')
            elif changes:
                self.log(' ' * 40, '#', changes_s)
    
            if event == 'line':
                try:
                    module = inspect.getmodule(frame.f_code)
                    if module is None:
                        source = inspect.getsource(frame.f_code)
                    else:
                        source = inspect.getsource(module)
                    current_line = source.split('\n')[frame.f_lineno - 1]
    
                except OSError as err:
                    self.log(f"{err.__class__.__name__}: {err}")
                    current_line = ""
    
                self.log(repr(frame.f_lineno) + ' ' + current_line)
    
            if event == 'return':
                self.log(frame.f_code.co_name + '()' + " returns " + repr(arg))
                self.last_vars = {}  # Delete 'last' variables
    
        def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
            self.print_debugger_status(frame, event, arg)
    ```
    
- 실행
    
    ```python
    with Tracer():
        remove_html_markup('<b>x</b>')
    ```
    
    ![2024-11-04_03-18-04.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/294419f6-86d7-4d69-9a2c-a125207ffe38/2024-11-04_03-18-04.jpg)
    
    ![2024-11-04_03-18-16.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d0b17986-f3f5-4f39-8006-24bae6437707/2024-11-04_03-18-16.jpg)
    

## 5. ConditionalTracer

- 다음 로그는 오랜 시간이 걸리거나 데이터 구조가 매우 복잡해지는 경우 파악이 어려워짐
    
    → 특정 조건이 유지되는 동안에만 추적기에 로그를 기록
    

- `ConditionalTracer` 클래스
    - 특정 조건식이 만족될 때에만 로그를 기록하도록 설계된 클래스
        
        ```python
        with ConditionalTracer(condition='c == "z"'):
            remove_html_markup(...)
        ```
        

- 구현
    
    ```python
    class ConditionalTracer(Tracer):
    		""" condition 매개변수는 추적을 수행할 조건 나타내는 표현식 -> 조건이 참일때만 로그 기록 """
        def __init__(self, *, condition: Optional[str] = None, file: TextIO = sys.stdout) -> None:
    
            if condition is None:
                condition = 'False'
    
            self.condition: str = condition
            self.last_report: Optional[bool] = None
            super().__init__(file=file)
            
        """ eval() 함수를 사용해 주어진 expr(조건)을 현재 프레임의 로컬 변수 환경에서 평가 """
        def eval_in_context(self, expr: str, frame: FrameType) -> Optional[bool]:
            try:
                cond = eval(expr, None, frame.f_locals)
            except NameError:  # (yet) undefined variable
                cond = None
            return cond
    
    		""" 현재 프레임에서 조건을 평가하고, 참일 때만 True를 반환하여 로그를 기록할지 여부를 결정 """
        def do_report(self, frame: FrameType, event: str, arg: Any) -> Optional[bool]:
            return self.eval_in_context(self.condition, frame)
            
        """ 프로그램 실행 중 매 줄마다 호출, 조건이 참일때만 print 메서드 호출해서 기록 """
        def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
            report = self.do_report(frame, event, arg)
            if report != self.last_report:
                if report:
                    self.log("...")
                self.last_report = report
    
            if report:
                self.print_debugger_status(frame, event, arg)
    ```
    
- 실행
    
    ```python
    with ConditionalTracer(condition='quote'):
        remove_html_markup('<b title="bar">"foo"</b>')
    ```
    
    ![2024-11-04_03-35-59.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d191afbc-0407-4245-b947-2ece0daa0dd6/2024-11-04_03-35-59.jpg)
    

- 매개변수로 입력된 condition
    - syntax 오류를 가질 때 → 오류 발생
        
        ```python
        with ExpectError(SyntaxError):
            with ConditionalTracer(condition='2 +'):
                remove_html_markup('<b title="bar">"foo"</b>')
        ```
        
        >  SyntaxError: unexpected EOF while parsing (expected)
        
    - 정의되지 않은 변수가 포함된 경우 → 조건 평가가 False로 항상 처리
        
        ```python
        with ExpectError():
            with ConditionalTracer(condition='undefined_variable'):
                remove_html_markup('<b title="bar">"foo"</b>')
        ```
        
        > 
        
- 특정 코드 위치에서만 로그 집중
    - function과 line이라는 가상 변수(pseudo-variable)를 도입
        
        ```python
        class ConditionalTracer(ConditionalTracer):
            def eval_in_context(self, expr: str, frame: FrameType) -> Any:
                frame.f_locals['function'] = frame.f_code.co_name
                frame.f_locals['line'] = frame.f_lineno
        
                return super().eval_in_context(expr, frame)
        ```
        
        - 현재 함수 이름(frame.f_code.co_name)을 function 변수로 저장
        - 현재 줄 번호(frame.f_lineno)를 line 변수로 저장
    - 실행
        
        ```python
        with ConditionalTracer(condition="function == 'remove_html_markup' and line >= 237"):
            remove_html_markup('xyz')
        ```
        
        ![2024-11-04_03-41-22.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/b4fc75a0-a3b7-4851-b070-39baa8992e51/2024-11-04_03-41-22.jpg)
        
    - interactive 디버거에서 사용하는 일반적인 중단점(breakpoint)과 유사

## 6. EventTracer

- 변수가 특정 값을 가질 때뿐만 아니라 값이 변경되는 시점도 정확히 추적 필요

- `EventTracer` 클래스
    - 사용자가 지정한 표현식 목록을 매줄마다 평가하고, 이 중 하나라도 값이 변하면 로그를 기록
    - 변수의 값이 바뀌는 줄 추적
        
        ```python
        with EventTracer(events=['tag', 'quote']):
            remove_html_markup(...)
        ```
        
    - 현재 함수가 바뀌는 줄 추적 (함수가 호출되거나 반환될 때)
        
        ```python
        with EventTracer(events=['function']):
            remove_html_markup(...)
        ```
        
    
- 구현
    
    ```python
    class EventTracer(ConditionalTracer):
    
    		""" 추적할 표현식 리스트인 event 입력 """
        def __init__(self, *, condition: Optional[str] = None, events: List[str] = [], file: TextIO = sys.stdout) -> None:
            self.events = events
            self.last_event_values: Dict[str, Any] = {}
            super().__init__(file=file, condition=condition)
    
    		""" 주어진 events 리스트의 각 표현식을 평가하고, 값이 이전과 다르면 True를 반환 """
    		def events_changed(self, events: List[str], frame: FrameType) -> bool:
            change = False
            for event in events:
                value = self.eval_in_context(event, frame)
                if (event not in self.last_event_values or value != self.last_event_values[event]):
                    self.last_event_values[event] = value
                    change = True
            return change
    
    		""" 로그 기록 여부 결정 - 조건이 만족되거나 이벤트 값이 변경될 때 True를 반환 """      
        def do_report(self, frame: FrameType, event: str, arg: Any) -> bool:
            return (self.eval_in_context(self.condition, frame) or self.events_changed(self.events, frame))
    ```
    
- 실행
    
    ```python
    with EventTracer(events=['quote', 'tag']):
        remove_html_markup('<b title="bar">"foo"</b>')
    ```
    
    ![2024-11-04_03-56-48.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/75d2e006-3278-49f4-9bdb-1cdfca609a06/2024-11-04_03-56-48.jpg)
    
    - interactive 디버거에서 사용하는 일반적인 감시점(watchpoint)과 유사

## 7. 정적 코드 삽입

- EventTracer와 같은 추적 방식은 유연하지만, 모든 줄에서 조건과 이벤트를 평가하기 때문에 매우 느려짐
    
    ```python
    from Timer import Timer
    
    with Timer() as t:
        for i in range(runs):
            remove_html_markup('<b title="bar">"foo"</b>')
    untraced_execution_time = t.elapsed_time()
    untraced_execution_time
    ```
    
    > 0.00286945
    
    ```python
    with Timer() as t:
        for i in range(runs):
            with EventTracer():
                remove_html_markup('<b title="bar">"foo"</b>')
    traced_execution_time = t.elapsed_time()
    traced_execution_time
    ```
    
    > 0.790874917 (275배 차이)
    

- remove_html_markup() 과 EventTracer() 의 모든 줄과 반환을 추적 → 비용이 큼

- `정적 코드 삽입`을 통한 기능 개선 (Dynamically → Statically)
    - 프로그램을 실행할 때마다 평가하는 대신, 특정 위치에 디버깅 코드를 직접 삽입하여 조건을 미리 체크
        
        → 추적이 필요 없는 코드는 원래 속도로 실행 가능
        
    - 단점 : 추적 조건이 특정 위치에 한정
    - Binary Code (ex. C언어) : 정적 추적기와 유사하게 작동
    
- 구현
    
    ```python
    # 추적을 위해 삽입할 코드
    TRACER_CODE = "TRACER.print_debugger_status(inspect.currentframe(), 'line', None); "
    ```
    
    ```python
    TRACER = Tracer()
    ```
    
    ```python
    """ 각 breakpoint 줄에 TRACER_CODE를 삽입하여 새로운 버전의 함수를 반환 """
    def insert_tracer(function: Callable, breakpoints: List[int] = []) -> Callable:
    
        source_lines, starting_line_number = inspect.getsourcelines(function)
    
    		# 중단점 줄을 역순으로 정렬하여, 각 줄에 TRACER_CODE를 삽입
        breakpoints.sort(reverse=True)
        for given_line in breakpoints:
    		    # 중단점 줄의 상대 위치를 계산한 후, 들어쓰기를 계산해 TRACER_CODE 삽입
            relative_line = given_line - starting_line_number + 1
            inject_line = source_lines[relative_line - 1]
            indent = len(inject_line) - len(inject_line.lstrip())
            source_lines[relative_line - 1] = ' ' * indent + TRACER_CODE + inject_line.lstrip()
    
        # 새로운 함수명 설정
        new_function_name = function.__name__ + "_traced"
        source_lines[0] = source_lines[0].replace(function.__name__, new_function_name)
        new_def = "".join(source_lines)
    
        # 기존 소스와 파일명 유지
        prefix = '\n' * starting_line_number    # 함수가 원래 줄 번호 유지할 수 있도록
        new_function_code = compile(prefix + new_def, function.__code__.co_filename, 'exec')
        exec(new_function_code)
        new_function = eval(new_function_name)
        return new_function
    ```
    
- 실행
    
    ```python
    with Timer() as t:
        remove_html_markup_traced('<b title="bar">"foo"</b>')
    static_tracer_execution_time = t.elapsed_time()
    ```
    
    ![2024-11-04_04-16-27.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/4ed61f1c-610c-460a-bf4c-cba5ff86a830/2024-11-04_04-16-27.jpg)
    
    ```python
    static_tracer_execution_time
    ```
    
    > 0.01659020 (1.86배 빠름)
    

## 8. 예외 처리

- 예외가 발생할 경우 기본적으로 예외는 Tracer를 통과하며 추적이 중단됨
- 예외 발생 시점의 정보(예외 타입, 메시지 등)를 기록하여 디버깅에 도움을 줄 수 있음

- 예시
    
    ```python
    def fail() -> float:
        return 2 / 0
    
    with Tracer():
        try:
            fail()
        except Exception:
            pass
    ```
    
    ![2024-11-04_04-45-07.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/95d879a7-6d9f-41fe-af2e-0a1834c47328/2024-11-04_04-45-07.jpg)
    
- 해결책
    
    ```python
    class Tracer(Tracer):
        def print_debugger_status(self, frame: FrameType, event: str, arg: Any) -> None:
            if event == 'exception':
                exception, value, tb = arg
                self.log(f"{frame.f_code.co_name}() "
                         f"raises {exception.__name__}: {value}")
            else:
                super().print_debugger_status(frame, event, arg)
    ```
    
    ```python
    with Tracer():
        try:
            fail()
        except Exception:
            pass
    ```
    
    ![2024-11-04_04-46-07.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/87412ca9-8761-4817-8910-010173b2d1d1/2024-11-04_04-46-07.jpg)
    

---

Pytest 사용법

- 해당 작업디렉토리 안에 모든 테스트 파일 실행
    
    `> pytest`
    
- 특정 디렉토리 내 테스트 파일 실행
    
    `> pytest tests/`
    
- 특정 테스트 파일 실행
    
    `> pytest test_sample.py`
