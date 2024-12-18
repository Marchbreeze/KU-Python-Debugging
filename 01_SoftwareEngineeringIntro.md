## 1. Software Engineering이란

- 전체 개발 주기를 포함함
    - 소프트웨어 개발은 단순한 코드 작성만이 아니라, 요구사항 분석, 설계, 구현, 테스트, 배포, 유지보수까지 이어지는 전체 주기를 다룸
    - 각 단계는 서로 연관되어 있어, 어느 한 단계가 잘못되면 전체 시스템에 영향을 미칠 수 있음

- 문제를 분해하고 해결함
    - 복잡한 문제를 작은 부분으로 분해한 후, 각 부분을 개별적으로 해결하는 방식
    - Test, fix, retry
        - 테스트로 문제를 찾아내고, 수정 후 다시 시도하는 반복 과정이 필수적 → 품질과 안정성 개선
    - Design, create, test, iterate
        - 소프트웨어는 한 번에 완성되는 것이 아니라, 설계하고 구현한 후, 다시 테스트하고, 필요하면 반복해서 개선해 나가는 과정
        - 반복적 개발(iterative development) 과정은 소프트웨어가 사용자 요구사항에 맞고, 신뢰성 있게 동작할 수 있도록 도움
        
- Mary Shaw의 정의:
    - 컴퓨터 과학의 한 분야로서,
    - 실용적이고 비용 효율적인 방식으로 컴퓨팅 문제에 대한 해결책을 만들고,
    - 과학적 지식을 적용하는 것이 바람직하며,
    - 인류에게 봉사할 수 있는 소프트웨어 시스템을 개발하는 것을 목표로 함
    
    → 소프트웨어 공학은 단순히 소프트웨어를 만드는 것에 그치지 않고, 과학적 원리를 기반으로 인류에게 실질적인 도움을 줄 수 있는 시스템을 구축하는 과정이며, 비용 효율성을 고려하면서도 문제를 효과적으로 해결하는 것을 중요한 목표로 삼음
    

## 2. Software Engineering의 필요성

- 산업 현장에서의 SE와 코딩 과제의 차이점
    - 요구사항이 모호하고 개발 중에 변경되는 경우가 많음
    - 대규모 프로젝트에서는 팀워크와 다양한 설계 기술이 필요
    - 개발이 끝난 후에도 소프트웨어는 진화하므로 몇 주, 몇 달, 또는 몇 년 동안 유지보수 필요
    - 실패의 비용이 더 큼 → 금전적 손실, 명성 손상, 고객 이탈 등으로 이어질 수 있음

- Software Engineering의 필요성
    - 소프트웨어와 버그
        - 현대 사회에서 소프트웨어는 거의 모든 분야에 걸쳐 사용되지만, 그만큼 버그와 오류도 많음
        - 신뢰성 높은 소프트웨어를 만들기 위해 체계적 접근이 필요
    - magical triangle(품질, 시간, 비용)을 달성하기 위해
        - 소프트웨어 공학은 이 세 가지 요소의 균형을 효과적으로 관리할 수 있는 방법을 제시
        - 높은 품질을 유지하면서도 정해진 시간 안에 프로젝트를 완료하고, 비용도 효율적으로 사용해야
    - 무질서한 코딩 노력을 공학적 원칙으로 변환하는 해결책으로
        - 단순한 코딩은 시간이 지나면서 복잡해지고 관리하기 어려워질 수 있음
        - 이러한 무질서한 코딩을 조직적이고 체계적인 공학적 원칙으로 전환하여 효율적이고 유지 가능한 시스템을 만드는 데 기여함
    - 대규모 복잡한 소프트웨어를 설계, 개발, 유지보수하는 체계적 접근의 적용으로
        - 대규모의 복잡한 시스템을 개발할 때는 체계적인 접근이 필수적
        - **소프트웨어 공학은 설계, 개발, 유지보수의 각 단계를 체계적으로 다루는 방법을 제공하여, 복잡한 소프트웨어를 효과적으로 관리**
