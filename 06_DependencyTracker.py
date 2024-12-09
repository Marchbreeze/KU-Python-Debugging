from types import FunctionType, FrameType, TracebackType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import warnings
import itertools

Location = Tuple[Callable, int]
Node = Tuple[str, Location]
Dependency = Dict[Node, Set[Node]]

class StackInspector:
    def caller_frame(self) -> FrameType:
        frame = cast(FrameType, inspect.currentframe())
        while self.our_frame(frame):
            frame = cast(FrameType, frame.f_back)
        return frame

    def our_frame(self, frame: FrameType) -> bool:
        return isinstance(frame.f_locals.get('self'), self.__class__)
    
    def search_frame(self, name: str, frame: Optional[FrameType] = None) -> Tuple[Optional[FrameType], Optional[Callable]]:
        if frame is None:
            frame = self.caller_frame()
        while frame:
            item = None
            if name in frame.f_globals:
                item = frame.f_globals[name]
            if name in frame.f_locals:
                item = frame.f_locals[name]
            if item and callable(item):
                return frame, item
            frame = cast(FrameType, frame.f_back)
        return None, None

    def search_func(self, name: str, frame: Optional[FrameType] = None) -> Optional[Callable]:
        frame, func = self.search_frame(name, frame)
        return func
    
    _generated_function_cache: Dict[Tuple[str, int], Callable] = {}

    def create_function(self, frame: FrameType) -> Callable:
        name = frame.f_code.co_name
        cache_key = (name, frame.f_lineno)
        if cache_key in self._generated_function_cache:
            return self._generated_function_cache[cache_key]
        try:
            generated_function = cast(Callable,FunctionType(frame.f_code,globals=frame.f_globals,name=name))
        except TypeError:
            generated_function = self.unknown
        except Exception as exc:
            warnings.warn(f"Couldn't create function for {name} " f" ({type(exc).__name__}: {exc})")
            generated_function = self.unknown
        self._generated_function_cache[cache_key] = generated_function
        return generated_function
    
    def caller_location(self) -> Location:
        return self.caller_function(), self.caller_frame().f_lineno

    def caller_function(self) -> Callable:
        frame = self.caller_frame()
        name = frame.f_code.co_name
        func = self.search_func(name)
        if func:
            return func
        return self.create_function(frame)

    def unknown(self) -> None:
        pass

    def is_internal_error(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> bool:
        if not exc_tp:
            return False
        for frame, lineno in traceback.walk_tb(exc_traceback):
            if self.our_frame(frame):
                return True
        return False


class DataTracker(StackInspector):
    def __init__(self, log: bool = False) -> None:
        self.log = log
    
    # 특정 변수(name)에 값(value)을 할당할 때, 해당 작업을 추적
    def set(self, name: str, value: Any, loads: Optional[Set[str]] = None) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: setting {name}")
        return value
    
    # 특정 변수(name)의 값을 읽는 작업을 추적
    def get(self, name: str, value: Any) -> Any:
        if self.log:
            caller_func, lineno = self.caller_location()
            print(f"{caller_func.__name__}:{lineno}: getting {name}")
        return value


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
        
    def get(self, name: str, value: Any) -> Any:
        self.check_location()
        self.last_read.append(name)
        return super().get(name, value)
    
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
                # 위치가 변경되었다면 읽기 변수 초기화
                self.clear_read()
        self.last_checked_location = location

    # 다음 줄 실행 시 발생하는 위치 변경에 의한 last_read 리스트 초기화를 방지
    def ignore_next_location_change(self) -> None:
        self._ignore_location_change = True

    # 현재 줄 실행 시 발생하는 위치 변경에 의한 last_read 리스트 초기화를 방지
    def ignore_location_change(self) -> None:
        self.last_checked_location = self.caller_location()

    TEST = '<test>'
    
    # 변수 name에 값 value를 설정하고 데이터 및 제어 의존성을 기록
    def set(self, name: str, value: Any, loads: Optional[Set[str]] = None) -> Any:
        
        # 읽은 변수(vars_read)의 출처를 dependencies에 추가
        def add_dependencies(dependencies: Set[Node], vars_read: List[str], tp: str) -> None:
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


# _test_data = DependencyTracker()
# x = _test_data.set('x', 1)
# y = _test_data.set('y', _test_data.get('x', x))
# z = _test_data.set('z', _test_data.get('x', x) + _test_data.get('y', y))
# print(_test_data.origins)
# print(_test_data.data_dependencies)