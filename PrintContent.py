from types import FrameType, TracebackType, FunctionType
from typing import Any, Dict, List, Set, Optional, Union, Tuple, Type, Callable, cast

def print_content(content: str, filename: Optional[str] = None, lexer: Optional[Any] = None, start_line_number: Optional[int] = None) -> None:
    from pygments import highlight, lexers, formatters
    from pygments.lexers import get_lexer_for_filename, guess_lexer

    if rich_output():
        if lexer is None:
            if filename is None:
                lexer = guess_lexer(content)
            else:
                lexer = get_lexer_for_filename(filename)

        colorful_content = highlight(
            content, lexer,
            formatters.TerminalFormatter())
        content = colorful_content.rstrip()

    if start_line_number is None:
        print(content, end="")
    else:
        content_list = content.split("\n")
        no_of_lines = len(content_list)
        size_of_lines_nums = len(str(start_line_number + no_of_lines))
        for i, line in enumerate(content_list):
            content_list[i] = ('{0:' + str(size_of_lines_nums) + '} ').format(i + start_line_number) + " " + line
        content_with_line_no = '\n'.join(content_list)
        print(content_with_line_no, end="")

def rich_output() -> bool:
    try:
        get_ipython()  # type: ignore
        rich = True
    except NameError:
        rich = False

    return rich