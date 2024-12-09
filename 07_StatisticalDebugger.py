from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import inspect
import traceback
import sys
import warnings
import html
import math

Location = Tuple[Callable, int]
Coverage = Set[Tuple[Callable, int]]

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


class Tracer(StackInspector):
    def __init__(self, target_func: str) -> None:
        self.target_func = target_func

    def traceit(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        if frame.f_code.co_name == self.target_func:
            if event == 'call':
                return self.traceit
        return None
                
    def log(self, *objects: Any, sep: str = ' ', end: str = '\n', flush: bool = True) -> None:
        print(*objects, sep=sep, end=end, file=sys.stdout, flush=flush)
        
    def __enter__(self) -> 'Tracer':
        self.original_trace_function = sys.gettrace()
        sys.settrace(self.traceit)
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        sys.settrace(self.original_trace_function)
        return None


class Collector(Tracer):
    def __init__(self) -> None:
        self._function: Optional[Callable] = None
        self._args: Optional[Dict[str, Any]] = None
        self._argstring: Optional[str] = None
        self._exception: Optional[Type] = None
        self.items_to_ignore: List[Union[Type, Callable]] = [self.__class__]
    
    def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
        for item in self.items_to_ignore:
            if (isinstance(item, type) and 'self' in frame.f_locals and
                isinstance(frame.f_locals['self'], item)):
                return
            if item.__name__ == frame.f_code.co_name:
                return
        if self._function is None and event == 'call':
            self._function = self.create_function(frame)
            self._args = frame.f_locals.copy()
            self._argstring = ", ".join([f"{var}={repr(self._args[var])}" for var in self._args])
        self.collect(frame, event, arg)
    
    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        pass

    def events(self) -> Set:
        return set()

    def id(self) -> str:
        return f"{self.function().__name__}({self.argstring()})"
        
    def __repr__(self) -> str:
        return self.id()
    
    def function(self) -> Callable:
        if not self._function:
            raise ValueError("No call collected")
        return self._function

    def argstring(self) -> str:
        if not self._argstring:
            raise ValueError("No call collected")
        return self._argstring
    
    def args(self) -> Dict[str, Any]:
        if not self._args:
            raise ValueError("No call collected")
        return self._args

    def exception(self) -> Optional[Type]:
        return self._exception

    def add_items_to_ignore(self, items_to_ignore: List[Union[Type, Callable]]) -> None:
        self.items_to_ignore += items_to_ignore
        
    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        ret = super().__exit__(exc_tp, exc_value, exc_traceback)
        if not self._function:
            if exc_tp:
                return False  # re-raise exception
            else:
                raise ValueError("No call collected")
        return ret

    def covered_functions(self) -> Set[Callable]:
        return set()

    def coverage(self) -> Coverage:
        return set()


class CoverageCollector(Collector, StackInspector):
    def __init__(self) -> None:
        super().__init__()
        self._coverage: Coverage = set()

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

    def events(self) -> Set[Tuple[str, int]]:
        return {(func.__name__, lineno) for func, lineno in self._coverage}

    def covered_functions(self) -> Set[Callable]:
        return {func for func, lineno in self._coverage}

    def coverage(self) -> Coverage:
        return self._coverage

    def code_with_coverage(function: Callable, coverage: Coverage) -> None:
        # 함수의 소스 코드와 시작 라인 번호 설정
        source_lines, starting_line_number = sys.getsourcelines(function)
        # 첫 번째 라인의 번호 설정
        line_number = starting_line_number
        # 각 라인 앞에 실행 여부를 나타내는 별표 표시
        for line in source_lines:
            marker = '*' if (function, line_number) in coverage else ' '
            print(f"{line_number:4} {marker} {line}", end='')
            line_number += 1


class StatisticalDebugger:
    def __init__(self, collector_class: Type = CoverageCollector, log: bool = False):
        # 사용할 Collector 클래스 지정 (기본: CoverageCollector)
        self.collector_class = collector_class
        # 결과별 Collector 저장
        self.collectors: Dict[str, List[Collector]] = {}
        # 로그 출력 여부 설정
        self.log = log 

    def collect(self, outcome: str, *args: Any, **kwargs: Any) -> Collector:
        # Collector 생성
        collector = self.collector_class(*args, **kwargs)
        # 디버깅 클래스 무시 설정
        collector.add_items_to_ignore([self.__class__])
        # 목록에 Collector 저장
        return self.add_collector(outcome, collector)

    def add_collector(self, outcome: str, collector: Collector) -> Collector:
        # 결과에 대한 리스트 초기화
        if outcome not in self.collectors:
            self.collectors[outcome] = []
        # 목록에 추가 후 저장된 Collector 반환
        self.collectors[outcome].append(collector)
        return collector
    
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


class DifferenceDebugger(StatisticalDebugger):
    PASS = 'PASS'
    FAIL = 'FAIL'

    def collect_pass(self, *args: Any, **kwargs: Any) -> Collector:
        return self.collect(self.PASS, *args, **kwargs)

    def collect_fail(self, *args: Any, **kwargs: Any) -> Collector:
        return self.collect(self.FAIL, *args, **kwargs)
    
    def pass_collectors(self) -> List[Collector]:
        return self.collectors[self.PASS]

    def fail_collectors(self) -> List[Collector]:
        return self.collectors[self.FAIL]
    
    def all_fail_events(self) -> Set[Any]:
        return self.all_events(self.FAIL)

    def all_pass_events(self) -> Set[Any]:
        return self.all_events(self.PASS)
    
    # 실패 실행에서만 관찰된 이벤트를 반환
    def only_fail_events(self) -> Set[Any]:
        return self.all_fail_events() - self.all_pass_events()

    # 성공 실행에서만 관찰된 이벤트를 반환
    def only_pass_events(self) -> Set[Any]:
        return self.all_pass_events() - self.all_fail_events()

    def __enter__(self) -> Any:
        self.collector = self.collector_class()
        self.collector.add_items_to_ignore([self.__class__])
        self.collector.__enter__()
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException, exc_traceback: TracebackType) -> Optional[bool]:
        status = self.collector.__exit__(exc_tp, exc_value, exc_traceback)
        if status is None:
            pass
        else:
            return False
		# 실행 결과를 PASS 또는 FAIL로 분류
        if exc_tp is None:
            outcome = self.PASS
        else:
            outcome = self.FAIL
		# Collector를 실행 결과에 따라 저장
        self.add_collector(outcome, self.collector)
        return True 


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
    
    def color(self, event: Any) -> Optional[str]:
        suspiciousness = self.suspiciousness(event)
        if suspiciousness is None:
            return None  # 실행되지 않은 코드
        if suspiciousness > 0.8:
            return 'mistyrose'  # 실패 실행에서만 발생
        if suspiciousness >= 0.5:
            return 'lightyellow'  # 성공과 실패 모두에서 발생
        return 'honeydew'  # 성공 실행에서만 발생

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


class ContinuousSpectrumDebugger(DiscreteSpectrumDebugger):
	# 주어진 이벤트를 관찰한 Collector(실행 데이터)를 반환
    def collectors_with_event(self, event: Any, category: str) -> Set[Collector]:
        all_runs = self.collectors[category]
        collectors_with_event = set(collector for collector in all_runs if event in collector.events())
        return collectors_with_event

	# 주어진 이벤트를 실행하지 않은 Collector를 반환
    def collectors_without_event(self, event: Any, category: str) -> Set[Collector]:
        all_runs = self.collectors[category]
        collectors_without_event = set(collector for collector in all_runs if event not in collector.events())
        return collectors_without_event

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

    def hue(self, event: Any) -> Optional[float]:
        passed = self.passed_fraction(event)
        failed = self.failed_fraction(event)
        if passed + failed > 0:
            return passed / (passed + failed)
        else:
            return None

    def suspiciousness(self, event: Any) -> Optional[float]:
        hue = self.hue(event)
        if hue is None:
            return None
        return 1 - hue
        
    def tooltip(self, event: Any) -> str:
        return self.percentage(event)

    def brightness(self, event: Any) -> float:
        return max(self.passed_fraction(event), self.failed_fraction(event))

    def color(self, event: Any) -> Optional[str]:
        hue = self.hue(event)
        if hue is None:
            return None
        saturation = self.brightness(event)
        return f"hsl({hue * 120}, {saturation * 100}%, 80%)"


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


class TarantulaDebugger(ContinuousSpectrumDebugger, RankingDebugger):
    pass


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