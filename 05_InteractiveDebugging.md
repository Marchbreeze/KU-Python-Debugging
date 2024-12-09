## 1. Interactive Debugger

- Interactive Debugger (간단하게 Debugger)
    - 프로그램 실행을 관찰할 수 있도록 도와주는 도구

- 디버거의 기능
    1. 프로그램 실행
    2. 조건 정의 및 중단
        - 실행을 중단하고 디버거로 제어를 넘길 수 있는 조건을 정의할 수 있음
        - ex. 특정 위치 도달, 특정 변수의 특정 값 획득, 특정 변수 접근, …
    3. 현재 상태 관찰
        - 프로그램이 중단되었을 때, 현재 상태를 관찰할 수 있음
        - ex. 현재 위치, 변수와 그 값들, 현재 함수롸 그 호출자들, …
    4. 단계별 실행
        - 프로그램이 중단되었을 때, 다음 명령에서 다시 중단되도록 프로그램 실행을 단계별로 실행 가능
    5. 다시 실행
        - 다음 중단점까지 실행 재개

- 디버거의 종류
    - 독립 실행형 도구로 제공되거나, 선택한 프로그래밍 환경에 통합되어 제공
    1. 명령줄 인터페이스 (Command-Line Interface, CLI)
        - 사용자가 텍스트 기반의 터미널 창에서 명령어를 입력해 디버깅 작업을 수행하는 방식
    2. 그래픽 사용자 인터페이스 (Graphical User Interface, GUI)
        - 사용자가 시각적으로 명령을 선택할 수 있도록 제공되는 화면 기반 인터페이스

## 2. Debugger 구성

- 디버거의 상호작용 : 일반적으로 **루프 패턴**을 따름
    - 중단점 설정 → 실행 → 중단 → 상태 확인의 반복
    - 검사하고 싶은 위치를 식별하고, 디버거에게 해당 중단점(breakpoint)에 도달했을 때 실행을 멈추도록 지시

- 루프 패턴의 예시
    1. 디버거에서 239번째 줄에서 멈추도록 설정하는 명령
        
        ```python
        (debugger) break 239  
        (debugger) _
        ```
        
    2. 디버거에게 실행을 재개하거나 시작하도록 명령 (지정된 위치에서 멈춤)
        
        ```python
        (debugger) continue  
        Line 239: s = x  
        (debugger) _
        ```
        
    3. 멈춘 이후 디버거 명령을 사용해 상태를 확인하며, 상황이 예상대로인지 확인
        
        ```python
        (debugger) print s  
        s = 'abc'  
        (debugger) _
        ```
        
    4. 프로그램을 한 줄씩 실행하며 계속 진행
        
        ```python
        (debugger) step  
        Line 240: c = s[0]
        (debugger) _
        ```
        

- 구성 방법
    - 트레이싱 함수를 설정하여 사용자가 다음에 무엇을 할지 직접 명령을 입력하도록 요청(prompt) 하는 것
    - 간단히 설명하기 위해 Python의 input() 함수를 사용해 명령을 인터랙티브하게 명령줄에서 수집
    
- 디버거 초기 설정
    - 현재 상태를 나타내기 위해 몇 가지 변수를 유지함 :
        1. stepping: 사용자가 다음 줄로 이동하기를 원할 때 True로 설정
        2. breakpoints: 중단점(줄 번호)을 저장하는 집합(set)
        3. interact: 사용자가 특정 위치에서 머무르는 동안 True로 설정
    - 현재 트레이싱 정보를 3가지 속성에 저장 :
        1. frame: 현재 실행 중인 코드의 프레임 (현재 함수, 로컬 변수, 호출 스택 등의 정보)
        2. event: 발생한 이벤트의 종류 (line, call, return)
        3. arg: 이벤트와 관련된 추가 정보 (ex. return 이벤트의 반환값)
    - 로컬 변수 저장 : local_vars
        
        ```python
        from types import FrameType
        from typing import Any, Optional, Callable, Dict, List, Tuple, Set, TextIO
        
        class Debugger(Tracer):
        
            def __init__(self, *, file: TextIO = sys.stdout) -> None:
                self.stepping: bool = True
                self.breakpoints: Set[int] = set()
                self.interact: bool = True
        
                self.frame: FrameType
                self.event: Optional[str] = None
                self.arg: Any = None
        
                self.local_vars: Dict[str, Any] = {}
        
                super().__init__(file=file)
        ```
        
    
- 트레이싱 함수 설정
    - 코드 실행 중 이벤트(함수 호출, 줄 실행 등)가 발생할 때마다 호출
    - 디버거는 이 메서드를 통해 실행 흐름을 감지하고, 특정 조건에서 중단하여 사용자의 명령을 처리
        
        ```python
        class Debugger(Debugger):
            def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
                self.frame = frame
                self.local_vars = frame.f_locals
                self.event = event
                self.arg = arg
        
                if self.stop_here():
                    self.interaction_loop()
        ```
        
        - self.local_vars : 메모리 접근을 최소화하기 위해 frame.f_locals를 한 번만 참조
        - stop_here()가 true면 디버거의 상호작용 루프를 실행

- 디버거가 실행을 멈춰야 할지 결정하는 조건을 정의
    - 디버거가 한 줄씩 실행하거나, 중단점에 도달했을 때 True를 반환
        
        ```python
        def stop_here(self) -> bool:
            return self.stepping or self.frame.f_lineno in self.breakpoints
        ```
        

- 실행 흐름 제어
    1. step_command: 프로그램을 한 줄씩 실행하도록 설정
        
        ```python
        def step_command(self, arg: str = "") -> None:
            self.stepping = True
            self.interact = False
        ```
        
    2. continue_command: 중단점까지 실행을 재개하도록 설정
        
        ```python
        def continue_command(self, arg: str = "") -> None:
            self.stepping = False
            self.interact = False
        ```
        

- 상호작용 루프
    - 현재 디버거 상태를 출력하고, 사용자가 입력한 명령을 처리하여 디버깅을 제어
    - 사용자는 step, continue, print 등과 같은 명령을 입력하여 디버깅 작업을 진행
        
        ```python
        def interaction_loop(self) -> None:
            self.print_debugger_status(self.frame, self.event, self.arg)
        
            self.interact = True
            while self.interact:
                command = input("(debugger) ")
                self.execute(command)
        ```
        
        - input() 함수는 사용자의 명령을 문자열로 반환
        - self.execute(command)를 호출하여 입력된 명령을 처리

- 디버거 명령 처리
    - 입력한 명령 문자열(command)에 따라 적절한 동작(step_command, continue_command)을 실행
        
        ```python
        def execute(self, command: str) -> None:
            if command.startswith('s'):
                self.step_command()
            elif command.startswith('c'):
                self.continue_command()
        ```
        

- remove_html_markup() 으로 실습하기
    
    ```python
    def remove_html_markup(s):
        tag = False
        quote = False
        out = ""
    
        for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
            elif c == '"' or c == "'" and tag:
                quote = not quote
            elif not tag:
                out = out + c
    
        return out
    ```
    
    ```python
    from bookutils import input, next_inputs
    
    next_inputs(["step", "step", "continue"])
    
    with Debugger():
        remove_html_markup('abc')
    
    assert not next_inputs()
    ```
    
    - next_inputs() : 디버거가 호출하는 동안 순서대로 실행될 입력 명령 리스트를 설정 (자동 제공)
    - assert로 next_inputs()로 설정된 명령이 모두 처리되었는지 검사

## 3. 명령 처리 개선

- 새로운 execute() 메서드는 다음과 같은 기능을 제공
    1. 자동 명령 등록
        - 클래스에서 _command()로 끝나는 메서드를 자동으로 탐색하여 명령으로 등록
    2. 사용 가능한 명령 목록 제공 (help)
        - 사용 가능한 명령어를 사용자에게 동적으로 제공
        - help 명령을 통해 현재 클래스에 정의된 모든 명령을 나열
    3. 명령과 인자 분리
        - 명령어와 그에 전달된 인자를 자동으로 분리하여 적절히 처리

- 클래스에 정의된 명령어 목록을 반환
    - 디버거 클래스의 메서드 중 _command로 끝나는 메서드를 탐색하여, 사용 가능한 모든 명령을 문자열로 반환
        
        ```python
        def commands(self) -> List[str]:
            cmds = [method.replace('_command', '')
                    for method in dir(self.__class__)
                    if method.endswith('_command')]
            cmds.sort()
            return cmds
        ```
        
        ```python
        d = Debugger()
        d.commands()
        ```
        

- 명령어 사용법 안내
    - 명령어가 모호하거나 잘못된 경우, 또는 명령어 목록이 필요한 경우 호출
    - 각 명령어의 docstring에서 추가 정보를 제공하여 사용자가 명령을 이해하고 사용할 수 있도록 도움
        
        ```python
        def help_command(self, command: str = "") -> None:
        
            if command:
                possible_cmds = [possible_cmd for possible_cmd in self.commands()
                                 if possible_cmd.startswith(command)]
        
                if len(possible_cmds) == 0:
                    self.log(f"Unknown command {repr(command)}. Possible commands are:")
                    possible_cmds = self.commands()
                elif len(possible_cmds) > 1:
                    self.log(f"Ambiguous command {repr(command)}. Possible expansions are:")
            else:
                possible_cmds = self.commands()
        
            for cmd in possible_cmds:
                method = self.command_method(cmd)
                self.log(f"{cmd:10} -- {method.__doc__}")
        ```
        

- 사용자가 입력한 명령어를 해당하는 메서드로 변환
    - 입력된 명령을 클래스의 메서드 이름과 비교하여 일치하거나 고유하게 시작하는 명령을 찾아 실행할 준비
    - 명령이 모호하거나 존재하지 않으면 도움말을 표시하고 None을 반환
        
        ```python
        def command_method(self, command: str) -> Optional[Callable[[str], None]]:
        
            if command.startswith('#'):
                return None
        
            possible_cmds = [possible_cmd for possible_cmd in self.commands()
                             if possible_cmd.startswith(command)]
            if len(possible_cmds) != 1:
                self.help_command(command)
                return None
        
            cmd = possible_cmds[0]
            return getattr(self, cmd + '_command')
        ```
        
        ```python
        d = Debugger()
        d.command_method("step")
        ```
        

- 개선된 execute()
    - 사용자가 입력한 **명령어**를 처리하여 해당하는 메서드를 호출
    - 명령어와 인자를 분리하고, 이를 처리할 메서드를 찾아 실행하는 전체 흐름을 담당
        
        ```python
        def execute(self, command: str) -> None:
        
            sep = command.find(' ')
            if sep > 0:
                cmd = command[:sep].strip()
                arg = command[sep + 1:].strip()
            else:
                cmd = command.strip()
                arg = ""
        
            method = self.command_method(cmd)
            if method:
                method(arg)
        ```
        

## 4. 값 출력

- 디버거에서 변수 출력을 담당하는 명령
    - 사용자가 명령어 print를 입력하면 프로그램의 로컬 변수와 값을 출력
    - NAME_command() 패턴을 따르므로, execute() 메서드에 의해 자동으로 명령어로 등록됨
        
        ```python
        def print_command(self, arg: str = "") -> None:
        
            vars = self.local_vars
            self.log("\n".join([f"{var} = {repr(value)}" for var, value in vars.items()]))
        ```
        
    - ex.
        
        ```python
        with Debugger():
            remove_html_markup('abc')
        ```
        
        ![2024-11-23_15-33-30.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/4522932d-244e-4f16-8b7b-218d6268d5d8/2024-11-23_15-33-30.jpg)
        

- 확장 : 입력된 인자(arg)에 따라 동작을 분기 처리
    - arg**가 없을 때**: 모든 로컬 변수를 출력
    - arg**가 있을 때**: arg를 표현식으로 간주하고 평가(evaluate)하여 결과를 출력
        - 표현식 평가 중 오류 발생 시, 예외 메시지를 출력
        
        ```python
        def print_command(self, arg: str = "") -> None:
        
            vars = self.local_vars
            if not arg:
                self.log("\n".join([f"{var} = {repr(value)}" for var, value in vars.items()]))
            else:
                try:
                    self.log(f"{arg} = {repr(eval(arg, globals(), vars))}")
                except Exception as err:
                    self.log(f"{err.__class__.__name__}: {err}")
        ```
        
    - ex.
        
        ```python
        # 약어 설정으로 UX 개선 (print 대신 p를 입력해도 같은 기능을 수행)
        next_inputs(["p s", "c"])
        
        with Debugger():
            remove_html_markup('abc')
        ```
        
        ![2024-11-23_15-36-19.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/cfc893c4-8449-47aa-9a03-181bba07b773/2024-11-23_15-36-19.jpg)
        
    - ex.
        
        ```python
        # print 명령어의 인자는 어떤 Python 표현식도 허용하므로, 다양한 동작을 동적으로 실행 가능
        next_inputs(["print (s[0], 2 + 2)", "continue"])
        
        with Debugger():
            remove_html_markup('abc')
        ```
        
        ![2024-11-23_15-38-26.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/7195e166-0793-471e-adf9-b84dba04858a/2024-11-23_15-38-26.jpg)
        
        ```python
        next_inputs(["help print", "continue"])
        ```
        
        ![2024-11-23_15-39-43.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/7096046b-bfda-44da-a69a-aeff5a60c868/2024-11-23_15-39-43.jpg)
        

## 5. 중단점 조정

- 중단점 설정
    - arg 없으면 중단점 리스트 출력
        
        ```python
        def break_command(self, arg: str = "") -> None:
        
            if arg:
                self.breakpoints.add(int(arg))
            self.log("Breakpoints:", self.breakpoints)
        ```
        
    - ex.
        
        ```python
        _, remove_html_markup_starting_line_number = inspect.getsourcelines(remove_html_markup)
        
        next_inputs([f"break {remove_html_markup_starting_line_number + 13}",
                     "continue", "print", "continue", "continue", "continue"])
        
        with Debugger():
            remove_html_markup('abc')
        ```
        
        ![2024-11-23_17-03-59.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/bb374822-5de6-4969-bb7f-0e66fe990f61/2024-11-23_17-03-59.jpg)
        
- 중단점 삭제
    - 특정 줄 번호에 설정된 중단점을 삭제하거나, arg가 없으면 모든 중단점을 일괄 삭제
        
        ```python
        def delete_command(self, arg: str = "") -> None:
        
            if arg:
                try:
                    self.breakpoints.remove(int(arg))
                except KeyError:
                    self.log(f"No such breakpoint: {arg}")
            else:
                self.breakpoints = set()
            self.log("Breakpoints:", self.breakpoints)
        ```
        
    - ex.
        
        ```python
        next_inputs([f"break {remove_html_markup_starting_line_number + 15}",
                     "continue", "print",
                     f"delete {remove_html_markup_starting_line_number + 15}",
                     "continue"])
                     
        with Debugger():
            remove_html_markup('abc')
        ```
        
        ![2024-11-23_17-06-22.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/3a14985a-619c-41ea-af9c-2eb361af244e/2024-11-23_17-06-22.jpg)
        

## 6. 소스 코드 표시

- 현재 함수의 소스 코드를 표시하는 명령
    - 현재 실행 중인 프레임(self.frame)의 코드 객체(f_code)를 사용하여 소스 코드를 가져옴
        
        ```python
        import inspect
        from bookutils import getsourcelines  # like inspect.getsourcelines(), but in color
        
        def list_command(self, arg: str = "") -> None:
        
            source_lines, line_number = getsourcelines(self.frame.f_code)
            for line in source_lines:
                self.log(f'{line_number:4} {line}', end='')
                line_number += 1
        ```
        
    - ex.
        
        ```python
        next_inputs(["list", "continue"])
        
        with Debugger():
            remove_html_markup('abc')
        ```
        
        ![2024-11-23_16-48-11.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/28e77a11-dbb5-4eff-bff2-0177492d01cb/2024-11-23_16-48-11.jpg)
        

- 개선:
    1. 특정 함수의 소스 코드 출력
        - arg를 입력하면 해당 객체(함수, 클래스 등)의 소스 코드를 출력
        - arg가 없으면 현재 디버깅 중인 함수의 소스 코드 출력
    2. 현재 실행 중인 줄과 중단점을 시각적으로 표시
        - 현재 실행 중인 줄 앞에는 > 기호
        - 중단점이 설정된 줄 앞에는 # 기호
        
        ```python
        def list_command(self, arg: str = "") -> None:
        
            try:
                if arg:
                    obj = eval(arg)
                    source_lines, line_number = inspect.getsourcelines(obj)
                    current_line = -1
                else:
                    source_lines, line_number = \
                        getsourcelines(self.frame.f_code)
                    current_line = self.frame.f_lineno
            except Exception as err:
                self.log(f"{err.__class__.__name__}: {err}")
                source_lines = []
                line_number = 0
        
            for line in source_lines:
                spacer = ' '
                if line_number == current_line:
                    spacer = '>'
                elif line_number in self.breakpoints:
                    spacer = '#'
                self.log(f'{line_number:4}{spacer} {line}', end='')
                line_number += 1
        ```
        
    - ex.
        
        ```python
        _, remove_html_markup_starting_line_number = inspect.getsourcelines(remove_html_markup)
        next_inputs([f"break {remove_html_markup_starting_line_number + 13}",
                     "list", "continue", "delete", "list", "continue"])
                     
        with Debugger():
            remove_html_markup('abc')
        ```
        
        ![2024-11-23_17-25-34.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/0ef2b9b7-4b25-48ca-8013-49818565a83e/2024-11-23_17-25-34.jpg)
        
        ![2024-11-23_17-25-52.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/e3349c71-5c80-4a58-ac6e-69b8950b38e7/2024-11-23_17-25-52.jpg)
        

## 7. 디버거 종료

- 디버거 세션을 종료하기 위한 명령
    - 중단점 삭제: 모든 중단점을 제거하여 디버거가 다시 멈추지 않도록 설정
    - 자동 실행 재개: 현재 함수가 종료될 때까지 실행을 재개
    - 사용자 상호작용 종료: 디버거의 상호작용 모드(self.interact)를 종료
        
        ```python
        def quit_command(self, arg: str = "") -> None:
        
            self.breakpoints = set()   # 모든 중단점을 삭제
            self.stepping = False      # 한 줄 실행 모드 비활성화
            self.interact = False      # 사용자 상호작용 종료
        ```
        

## + 활용할 디버거

- Breakpoint에서만 로그
    
    ```python
    from types import FrameType, TracebackType
    from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, TextIO, Callable, cast
    import inspect
    import traceback
    import sys
    import copy
    
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
    
    class Tracer(StackInspector):
        def __init__(self) -> None:
            self.original_trace_function: Optional[Callable] = None
    
        def __enter__(self) -> Any:
            self.original_trace_function = sys.gettrace()
            sys.settrace(self.traceit)
            return self
    
        def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
            sys.settrace(self.original_trace_function)
            if self.is_internal_error(exc_tp, exc_value, exc_traceback):
                return False
            else:
                return None
    
        def traceit(self, frame: FrameType, event: str, arg: Any) -> Callable:
            self.log(event, frame.f_lineno, frame.f_code.co_name, frame.f_locals)
    
        def log(self, *objects: Any, sep: str = ' ', end: str = '\n', flush: bool = True) -> None:
            print(*objects, sep=sep, end=end, file=sys.stdout, flush=flush)
    
    class Debugger(Tracer):
        def __init__(self) -> None:
            # 사용자가 다음 줄로 이동하기를 원할 때 True로 설정
            self.stepping: bool = True
            # 중단점(줄 번호)을 저장하는 집합
            self.breakpoints: Set[int] = set()
            # 사용자가 특정 위치에서 머무르는 동안 True로 설정
            self.interact: bool = True
    
            # 현재 실행 중인 코드의 프레임 (현재 함수, 로컬 변수, 호출 스택 등의 정보)
            self.frame: FrameType
            # 발생한 이벤트의 종류 (line, call, return)
            self.event: Optional[str] = None
            # arg: 이벤트와 관련된 추가 정보 (ex. return 이벤트의 반환값)
            self.arg: Any = None
            # 로컬 변수 저장
            self.local_vars: Dict[str, Any] = {}
    
            super().__init__()
    
        def traceit(self, frame: FrameType, event: str, arg: Any) -> Callable:
            self.frame = frame
            self.local_vars = frame.f_locals
            self.event = event
            self.arg = arg
    
            if self.stop_here():
                self.log(event, frame.f_lineno, inspect.getsource(inspect.getmodule(frame.f_code)).split('\n')[frame.f_lineno - 1], frame.f_locals)
                self.interaction_loop()
            return self.traceit
    
        def step_command(self, arg: str = "") -> None:
            self.stepping = True
            self.interact = False
    
        def continue_command(self, arg: str = "") -> None:
            self.stepping = False
            self.interact = False
    
        # 디버거가 실행을 멈춰야 할지 결정하는 조건 정의
        def stop_here(self) -> bool:
            # 디버거가 한 줄씩 실행하거나, 중단점에 도달했을 때 True를 반환
            should_stop = self.stepping or self.frame.f_lineno in self.breakpoints
            return should_stop
    
        # 상호작용 루프
        def interaction_loop(self) -> None:
            self.interact = True
            while self.interact:
                command = input("(debugger) ")
                self.execute(command)
    
        # 클래스에 정의된 명령어 목록을 반환
        def commands(self) -> List[str]:
            cmds = [method.replace('_command', '') for method in dir(self.__class__) if method.endswith('_command')]
            cmds.sort()
            return cmds
    
        # 명령어 사용법 안내
        def help_command(self, command: str = "") -> None:
            if command:
                possible_cmds = [possible_cmd for possible_cmd in self.commands() if possible_cmd.startswith(command)]
                if len(possible_cmds) == 0:
                    self.log(f"Unknown command {repr(command)}. Possible commands are:")
                    possible_cmds = self.commands()
                elif len(possible_cmds) > 1:
                    self.log(f"Ambiguous command {repr(command)}. Possible expansions are:")
            else:
                possible_cmds = self.commands()
            for cmd in possible_cmds:
                method = self.command_method(cmd)
                self.log(f"{cmd:10} -- {method.__doc__}")
    
        # 사용자가 입력한 명령어를 해당하는 메서드로 변환
        def command_method(self, command: str) -> Optional[Callable[[str], None]]:
            if command.startswith('#'):
                return None
            possible_cmds = [possible_cmd for possible_cmd in self.commands() if possible_cmd.startswith(command)]
            if len(possible_cmds) != 1:
                self.help_command(command)
                return None
            cmd = possible_cmds[0]
            return getattr(self, cmd + '_command')
    
        # 디버거 명령 처리
        def execute(self, command: str) -> None:
            # 명령어와 인자를 분리하고, 이를 처리할 메서드를 찾아 실행
            sep = command.find(' ')
            if sep > 0:
                cmd = command[:sep].strip()
                arg = command[sep + 1:].strip()
            else:
                cmd = command.strip()
                arg = ""
            method = self.command_method(cmd)
            if method:
                method(arg)
    
        # 디버거에서 변수 출력
        def print_command(self, arg: str = "") -> None:
            # arg가 있을 때 arg를 표현식으로 간주하고 평가하여 결과를 출력
            vars = self.local_vars
            if not arg:
                self.log("\n".join([f"{var} = {repr(value)}" for var, value in vars.items()]))
            else:
                try:
                    self.log(f"{arg} = {repr(eval(arg, globals(), vars))}")
                except Exception as err:
                    self.log(f"{err.__class__.__name__}: {err}")
    
        # 중단점 설정
        def break_command(self, arg: str = "") -> None:
            if arg:
                self.breakpoints.add(int(arg))
            self.log("Breakpoints:", self.breakpoints)
    
        # 중단점 삭제
        def delete_command(self, arg: str = "") -> None:
            if arg:
                try:
                    self.breakpoints.remove(int(arg))
                except KeyError:
                    self.log(f"No such breakpoint: {arg}")
            else:
                self.breakpoints = set()
            self.log("Breakpoints:", self.breakpoints)
    
        # 소스코드 표시
        def list_command(self, arg: str = "") -> None:
            # arg를 입력하면 해당 객체(함수, 클래스 등)의 소스 코드를 출력
            # arg가 없으면 현재 디버깅 중인 함수의 소스 코드 출력
            try:
                if arg:
                    obj = eval(arg)
                    source_lines, line_number = inspect.getsourcelines(obj)
                    current_line = -1
                else:
                    source_lines, line_number = inspect.getsourcelines(self.frame.f_code)
                    current_line = self.frame.f_lineno
            except Exception as err:
                self.log(f"{err.__class__.__name__}: {err}")
                source_lines = []
                line_number = 0
            for line in source_lines:
                spacer = ' '
                if line_number == current_line:
                    # 현재 실행 중인 줄 앞
                    spacer = '>'
                elif line_number in self.breakpoints:
                    # 중단점이 설정된 줄 앞
                    spacer = '#'
                self.log(f'{line_number:4}{spacer} {line}', end='')
                line_number += 1
    
        # 디버거 세션 종료
        def quit_command(self, arg: str = "") -> None:
            self.breakpoints = set()   # 모든 중단점을 삭제
            self.stepping = False      # 한 줄 실행 모드 비활성화
            self.interact = False      # 사용자 상호작용 종료
    ```
    
    ```python
    from RemoveHtmlMarkup import remove_html_markup
    from InteractiveDebugger import Debugger
    
    with Debugger():
        remove_html_markup('abc')
    ```
    
    ![2024-11-24_21-45-21.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/53766f16-2914-4201-b380-41f3bec59d45/2024-11-24_21-45-21.jpg)
    

- 전체 로그
