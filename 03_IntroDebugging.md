## 1. HTML 마크업 제거 디버깅

- HTML markup : 텍스트를 둘러싸는 괄호 안의 태그로 구성되어 텍스트를 해석하는 방법에 대한 정보를 제공
    
    ```html
    <!-- 이텔릭체 강조 -->
    This is <em>emphasized</em>
    ```
    

- 그러나 모든 HTML을 사용하면, 실제 텍스트에 접근하는 데에 어려움 존재 → HTML 마크업을 제거하고 텍스트로 변환하는 기능 구현이 필요함
- ex. 간단한 방법 (모두 적용은 X)
    
    ```python
    def remove_html_markup(s):  # type: ignore
        tag = False
        out = ""
    
        for c in s:
            if c == '<':    # start of markup
                tag = True
            elif c == '>':  # end of markup
                tag = False
            elif not tag:
                out = out + c
    
        return out
    ```
    
    ![2024-11-03_06-15-49.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/c36b0a24-ac3c-4336-8670-f203f831662e/2024-11-03_06-15-49.jpg)
    

- 작동 방식을 알기 위해 다이어그램 그리기
    - remove_html_markup() : 두 개의 state 태그와 ¬ 태그로 state machine을 구현
    - ¬ (NOT), ∧ (AND), ∨ (OR), → (IMPLIES)
        
        ```python
        from graphviz import Digraph, nohtml
        from IPython.display import display
        
        def graph(comment: str ="default") -> Digraph:
            return Digraph(name='', comment=comment, graph_attr={'rankdir': 'LR'},
                node_attr={'style': 'filled',
                           'fillcolor': STEP_COLOR,
                           'fontname': FONT_NAME},
                edge_attr={'fontname': FONT_NAME})
        
        state_machine = graph()
        state_machine.node('Start', )
        state_machine.edge('Start', '¬ tag')
        state_machine.edge('¬ tag', '¬ tag', label=" ¬ '<'\\nadd character")
        state_machine.edge('¬ tag:s', '¬ tag', label="'>'")
        state_machine.edge('¬ tag', 'tag', label="'<'")
        state_machine.edge('tag', '¬ tag', label="'>'")
        state_machine.edge('tag', 'tag', label="¬ '>'")
        
        display(state_machine)
        ```
        
        ![2024-11-03_06-47-58.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/a42eb17d-d829-4c8a-9062-b4d6f342124d/2024-11-03_06-47-58.jpg)
        
        1. non-tag state (¬ tag)에서 시작
        2. '<'가 아닌 모든 문자에 대해 추가하고 태그 없음 상태를 유지 ('>' 문자는 건너뜀)
        3. '<'을 읽으면 태그 상태(tag)로 전환하고 태그 상태를 유지
        4. 문자를 닫는 '>' 문자까지 건너뛰어 다시 태그가 아닌 상태로 전환

- `assert`
    
    주어진 검사가 거짓인 경우 실패하는 테스트
    
    ```python
    assert remove_html_markup("Here's some <strong>strong argument</strong>.") == "Here's some strong argument."
    ```
    

## 2. 텍스트 내부 괄호 처리

- 반례 - 텍스트 내부에 괄호가 존재하는 경우 (quote)
    
    ```html
    remove_html_markup('<input type="text" value="<your name>">')
    ```
    
    > '"'
    

- `ExpectError`
    
    코드 블록에서 발생하는 오류를 허용하며, 오류가 발생해도 테스트 실패로 간주되지 않음
    
    → 해당 오류를 고쳐야함을 알 수 있음
    
    ```python
    from ExpectError import ExpectError
    
    with ExpectError():
        assert remove_html_markup('<input type="text" value="<your name>">') == ""
    ```
    
    ![2024-11-03_06-43-11.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/14d3b845-90ef-4078-a3c2-7e5bc7d8d312/2024-11-03_06-43-11.jpg)
    
- 첫번째 수정
    - <input type="text" value="<your name>"> 에서,
    - 따옴표 안에 들어있는 >, <는 마크업이 아닌 텍스트로 인식해야 함
        
        ![2024-11-03_06-55-30.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/1b805eb2-cc1e-4bc0-bc80-4494c9a17587/2024-11-03_06-55-30.jpg)
        
        - < 이후 따옴표가 나오면 괄호 구분 X, “” 나올떄까지 quote state로 인식
    - 코드
        
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
        
    - 결과
        
        ```python
        remove_html_markup('<input type="text" value="<your name>">')
        ```
        
        > ‘’
        

## 3. 피해야하는 디버깅 방법

- 아직 해결 못한 반례
    
    ```python
    with ExpectError():
        assert remove_html_markup('<b>foo</b>') == 'foo'
    ```
    
    ```python
    with ExpectError():
        assert remove_html_markup('<b>"foo"</b>') == '"foo"'
    ```
    
    > AssertionError
    
    ```python
    with ExpectError():
        assert remove_html_markup('"<b>foo</b>"') == '"foo"'
    ```
    
    > AssertionError
    
    ```python
    with ExpectError():
        assert remove_html_markup('<"b">foo</"b">') == 'foo'
    ```
    

1. Printf Debugging
    
    ```python
    def remove_html_markup_with_print(s): 
        ...
        print("c =", repr(c), "tag =", tag, "quote =", quote)
    		...
    ```
    
    - print() 로 직접 모든 로그를 찍는 방법 → 시간 낭비, 미삭제시 보안 문제  발생 가능

1. Debugging into Existence
    - 문제되는 코드 돌아갈때까지 고치는 방법 → 기존 코드가 안돌아갈 가능성

1. Use the Most Obvious Fix
    
    ```python
    def remove_html_markup_fixed(s):
        if s == '<b>"foo"</b>':
            return '"foo"'
        ..
    ```
    
    - 반례 예외처리 → 근복적인 해결 방법 X

## 4. 문제에 대한 깊은 이해

- 일반적인 디버깅 상황
    - 프로그램(실행)이 있고, 일부 입력을 받고 일부 출력을 생성
    - error(✘) : 올바른 것 또는 사실에서 원치 않거나 의도하지 않은 편차가 발생
    - correct(✔) : 반대

- 일반적인 실패 상황
    
    ```python
    execution_diagram(show_steps=False, steps=0, error_step=0)
    ```
    
    ![2024-11-03_17-06-25.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/d177c0e4-79c0-4400-9f28-3f8fec28af4a/2024-11-03_17-06-25.jpg)
    
    - Execution_diagram 코드
        
        ```python
        from typing import List, Optional
        
        def execution_diagram(show_steps: bool = True, variables: List[str] = [],
                              steps: int = 3, error_step: int = 666,
                              until: int = 666, fault_path: List[str] = []) -> Digraph:
            dot = graph()
        
            dot.node('input', shape='none', fillcolor='white', label=f"Input {PASS}",
                     fontcolor=PASS_COLOR)
            last_outgoing_states = ['input']
        
            for step in range(1, min(steps + 1, until)):
        
                step_color: Optional[str]
                if step == error_step:
                    step_label = f'Step {step} {FAIL}'
                    step_color = FAIL_COLOR
                else:
                    step_label = f'Step {step}'
                    step_color = None
        
                if step >= error_step:
                    state_label = f'State {step} {FAIL}'
                    state_color = FAIL_COLOR
                else:
                    state_label = f'State {step} {PASS}'
                    state_color = PASS_COLOR
        
                state_name = f's{step}'
                outgoing_states = []
                incoming_states = []
        
                if not variables:
                    dot.node(name=state_name, shape='box',
                             label=state_label, color=state_color,
                             fontcolor=state_color)
                else:
                    var_labels = []
                    for v in variables:
                        vpath = f's{step}:{v}'
                        if vpath in fault_path:
                            var_label = f'<{v}>{v} ✘'
                            outgoing_states.append(vpath)
                            incoming_states.append(vpath)
                        else:
                            var_label = f'<{v}>{v}'
                        var_labels.append(var_label)
                    record_string = " | ".join(var_labels)
                    dot.node(name=state_name, shape='record',
                             label=nohtml(record_string), color=state_color,
                             fontcolor=state_color)
        
                if not outgoing_states:
                    outgoing_states = [state_name]
                if not incoming_states:
                    incoming_states = [state_name]
        
                for outgoing_state in last_outgoing_states:
                    for incoming_state in incoming_states:
                        if show_steps:
                            dot.edge(outgoing_state, incoming_state,
                                     label=step_label, fontcolor=step_color)
                        else:
                            dot.edge(outgoing_state, incoming_state)
        
                last_outgoing_states = outgoing_states
        
            if until > steps + 1:
                # Show output
                if error_step > steps:
                    dot.node('output', shape='none', fillcolor='white',
                             label=f"Output {PASS}", fontcolor=PASS_COLOR)
                else:
                    dot.node('output', shape='none', fillcolor='white',
                             label=f"Output {FAIL}", fontcolor=FAIL_COLOR)
        
                for outgoing_state in last_outgoing_states:
                    label = "Execution" if steps == 0 else None
                    dot.edge(outgoing_state, 'output', label=label)
        
            display(dot)
        ```
        

- 여러 단계인 경우, 어느 시점에서 오류 발생 후 이후 실행을 따라 전파됨
    
    ```python
    execution_diagram(show_steps=True, until=5, error_step=2)
    ```
    
    ![2024-11-03_17-08-58.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/2ac06bf0-3d13-43f0-b43e-713b13fb790c/2024-11-03_17-08-58.jpg)
    
    ```python
    execution_diagram(show_steps=True, variables=['var1', 'var2', 'var3'],
                          error_step=2,
                          until=5, fault_path=['s2:var2', 's3:var2'])
    ```
    
    ![2024-11-03_17-09-06.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/b2f88ca8-375f-481c-b9a7-2ed671386833/2024-11-03_17-09-06.jpg)
    
    → 오류가 발생하는 단계를 우선적으로 탐색해서 수정해야 함
    

- 일반적인 Error
    1. mistake : 에러를 만든 인간의 행동이나 결정
    2. defect(bug) : 코드 상의 오류
    3. fault(infection) : 프로그램 상태의 오류
    4. failure(malfunction) : 외부에서 볼 수 있는 오류 (오작동)

- cause-effect chain
    - Mistake → Defect → Fault → ... → Fault → Failure

- 오류 해결 위해 전파를 따라서 추적해야 하지만, 디버깅이 항상 이렇게 작동하지는 않음
    1. 프로그램 상태는 규모가 큼 - 수동 검색 시 단일 상태에 많은 시간 소요
    2. 중간 상태가 정확한지 여부를 항상 알 수는 없음
    3. 실행 단계의 규모가 큼
    
      ⇒ 디버깅 전략 
    
    검색을 효율적으로 하기 위해, 가장 가능성이 높은 원인부터 시작하여 점차 가능성이 낮은 원인으로 진행하여 검색에 집중
    

## 5. **The Scientific Method**

- The Scientific Method
    1. 질문을 공식화
    2. 관찰된 행동을 설명할 수 있는 가설을 수립
    3. 가설의 논리적 결과를 결정하고 가설을 뒷받침하거나 반박할 수 있는 예측을 공식화
    4. 실험에서 예측(및 가설)을 테스트
    
    ![2024-11-03_17-43-30.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/88b9b684-3131-45a7-a311-3ab074ea75c6/2024-11-03_17-43-30.jpg)
    
    - 코드
        
        ```python
        dot = graph()
        
        dot.node('Hypothesis')
        dot.node('Observation')
        dot.node('Prediction')
        dot.node('Experiment')
        
        dot.edge('Hypothesis', 'Observation',
                 label="<Hypothesis<BR/>is <I>supported:</I><BR/>Refine it>",
                 dir='back')
        dot.edge('Hypothesis', 'Prediction')
        
        dot.node('Problem Report', shape='none', fillcolor='white')
        dot.edge('Problem Report', 'Hypothesis')
        
        dot.node('Code', shape='none', fillcolor='white')
        dot.edge('Code', 'Hypothesis')
        
        dot.node('Runs', shape='none', fillcolor='white')
        dot.edge('Runs', 'Hypothesis')
        
        dot.node('More Runs', shape='none', fillcolor='white')
        dot.edge('More Runs', 'Hypothesis')
        
        dot.edge('Prediction', 'Experiment')
        dot.edge('Experiment', 'Observation')
        dot.edge('Observation', 'Hypothesis',
                 label="<Hypothesis<BR/>is <I>rejected:</I><BR/>Seek alternative>")
        ```
        
    

### (1) Finding Hypothesis

- 예시 확인
    
    ```python
    for i, html in enumerate(['<b>foo</b>',
                              '<b>"foo"</b>',
                              '"<b>foo</b>"',
                              '<b id="bar">foo</b>']):
        result = remove_html_markup(html)
        print("%-2d %-15s %s" % (i + 1, html, result))
    ```
    
    ![2024-11-03_17-45-10.jpg](https://prod-files-secure.s3.us-west-2.amazonaws.com/edfd69d1-6c01-4d0c-9269-1bae8a4e3915/1e26d2e9-06a4-476c-854a-9652e858da8f/2024-11-03_17-45-10.jpg)
    
1. tagged input에서 큰따옴표가 제거됨
2. 큰따옴표 내부의 tag는 제거되지 않음

### (2) Testing Hypothesis

- 두 가설이 연결되어있을 가능성을 염두에 두고 우선 1번 가설에 집중
- 1번 가설을 확인해볼 수 있는 반례 추가
    
    ```python
    remove_html_markup('"foo"')
    ```
    
    > 'foo' (기대 결과 : '"foo"')
    

### (3) Refining Hypothesis

- 가설1 : tag가 설정되는 과정에서 오류가 발생한다.
- assert 로 확인
    
    ```python
    def remove_html_markup_with_tag_assert(s):
        tag = False
        quote = False
        out = ""
    
        for c in s:
            assert not tag  # <=== Just added
    
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
    with ExpectError():
        result = remove_html_markup_with_tag_assert('"foo"')
    result
    ```
    
    > 'foo' (오류 발생 X)
    

### (4) Refuting a Hypothesis

- exception이 발생하지 않았으므로 가설1 기각
- 가설2 : quote 조건이 true로 평가되어 오류가 발생한다.
- 확인
    
    ```python
    def remove_html_markup_with_quote_assert(s):
        tag = False
        quote = False
        out = ""
    
        for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
            elif c == '"' or c == "'" and tag:
                assert False  # <=== Just added
                quote = not quote
            elif not tag:
                out = out + c
    
        return out
    ```
    
    ```python
    with ExpectError():
        result = remove_html_markup_with_quote_assert('"foo"')
    ```
    
    > AssertionError (expected)
    
    ⇒ 가설 검증 완료
    

### (5) Fixing the Bug

- 디버깅 시, 2가지의 Diagnose가 있는 경우에만 수정을 진행해야 함
    1. 인과관계 (Causality) : 실패의 이유와 방법을 설명해야 함
    2. 부정확성 (Incorrectness) : 코드가 잘못된 이유와 방법을 설명해야 함
    
- 문제점 : c == '"' or c == "'" and tag : and 연산자가 우선적으로 처리됨
    
    →`(c **==** '"' or c **==** "'") and tag` 로 수정
    
    ```python
    def remove_html_markup(s):  # type: ignore
        tag = False
        quote = False
        out = ""
    
        for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
            elif (c == '"' or c == "'") and tag:  # <-- FIX
                quote = not quote
            elif not tag:
                out = out + c
    
        return out
    ```
    
    ```python
    assert remove_html_markup('<input type="text" value="<your name>">') == ""
    assert remove_html_markup('<b>foo</b>') == 'foo'
    assert remove_html_markup('<b>"foo"</b>') == '"foo"'
    assert remove_html_markup('"<b>foo</b>"') == '"foo"'
    assert remove_html_markup('<b id="bar">foo</b>') == 'foo'
    ```
    
    > (오류 발생 X)
    

### (6) Homework after the fix

1. 추가 defect 발생 여부 확인
2. 자동화된 테스트를 추가해 이후 회귀 방지
3. assertion 추가 : `assert tag or not quote`
    
    ```python
    def remove_html_markup(s):
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
    

1. 커밋!

## 6. 좋은 디버거

1. Follow the Process
    - 문제를 즉시 발견하고 수정하는 것은 위험
    - 문제를 이해하고, 진단하는 단계가 필요함
2. Keep a Log
    - 기록을 통해 모든 관찰과 가설을 추적해야 함
3. Rubberducking
    - 다른 사람에게 문제를 설멸하는 과정은 새로운 가설을 세우는 데 도움이 될 수 있음
4. Debugging Aftermath
    - 버그를 수정한 후 코드의 형태와 이유에 대해 적어두면, 이후 리팩토링에 도움

## 7. 추가 과제

- 아직 모든 HTML 마크업을 제거하지 못함
    
    ```python
    with ExpectError():
        assert(remove_html_markup('<b title="<Shakespeare's play>">foo</b>') == "foo")
    ```
    
    > AssertionError (expected)
    
- 해결책
    
    ```python
    def remove_html_markup_with_proper_quotes(s):  # type: ignore
        tag = False
        quote = ''
        out = ""
    
        for c in s:
            assert tag or quote == ''
    
            if c == '<' and quote == '':
                tag = True
            elif c == '>' and quote == '':
                tag = False
            elif (c == '"' or c == "'") and tag and quote == '':
                # beginning of string
                quote = c
            elif c == quote:
                # end of string
                quote = ''
            elif not tag:
                out = out + c
    
        return out
    ```
    
    - `not quote` = `quote == ''`
