from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import sys
from Tracer import Tracer

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
        
        self.print_debugger_status(frame, event, arg)

        if self.stop_here():
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