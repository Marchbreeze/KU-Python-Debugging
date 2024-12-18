from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast
import random

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

def middle_testcase() -> Tuple[int, int, int]:
    x = random.randrange(10)
    y = random.randrange(10)
    z = random.randrange(10)
    return x, y, z

def middle_test(x: int, y: int, z: int) -> None:
    m = middle(x, y, z)
    assert m == sorted([x, y, z])[1]

def middle_passing_testcase() -> Tuple[int, int, int]:
    while True:
        try:
            x, y, z = middle_testcase()
            middle_test(x, y, z)
            return x, y, z
        except AssertionError:
            pass

def middle_failing_testcase() -> Tuple[int, int, int]:
    while True:
        try:
            x, y, z = middle_testcase()
            middle_test(x, y, z)
        except AssertionError:
            return x, y, z

MIDDLE_TESTS = 100
MIDDLE_PASSING_TESTCASES = [middle_passing_testcase() for i in range(MIDDLE_TESTS)]
MIDDLE_FAILING_TESTCASES = [middle_failing_testcase() for i in range(MIDDLE_TESTS)]