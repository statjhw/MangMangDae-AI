사용자의 프로필과 대화의 맥락을 깊이 이해하여, 맞춤형 채용 공고 추천부터 심층 분석, 합격 전략 제시까지 수행하는 고도로 지능화된 멀티턴(Multi-turn) 대화형 취업 어드바이저입니다. LangGraph 프레임워크를 기반으로, 상태(State)를 유지하며 사용자의 다양한 의도에 따라 동적으로 작업 흐름을 변경하는 유연한 에이전트 아키텍처를 구현했습니다.

# 핵심 아키텍처: LangGraph 기반

- **상태 관리 (`GraphState`)**: 워크플로우의 핵심은 `GraphState`라는 상태 객체입니다. 이 객체는 `user_input`(사용자 프로필), `chat_history`(전체 대화 기록), `summary`(장기 기억을 위한 요약본), `job_list`(추천 후보), `selected_job`(분석 대상 공고) 등 대화의 모든 맥락을 저장합니다. 이 상태는 각 노드를 거치며 점진적으로 업데이트되어, 시스템이 이전 대화를 기억하고 다음 행동을 결정하는 기반이 됩니다.
- **노드 (Nodes)**: 각 노드는 특정 작업을 수행하는 독립적인 기능 단위입니다.
    - **핵심 도구**: `recommend_jobs`(OpenSearch 검색), `get_company_info`(웹 검색), `get_preparation_advice`(LLM 기반 조언 생성), `reformulate_query`(LLM 기반 검색어 재구성) 등 11개의 전문화된 도구들이 각자의 역할을 수행합니다.
- **엣지 및 조건부 라우팅 (Edges & Conditional Routing)**: 워크플로우의 지능은 `should_route`라는 조건부 엣지 함수에 집약되어 있습니다. 이 함수는 LLM이 분석한 사용자의 `intent`뿐만 아니라, 현재 `state` (예: `selected_job`의 존재 여부)를 종합적으로 판단하여 다음에 실행할 노드를 동적으로 결정합니다. 이는 LLM의 실수를 코드 레벨에서 보완하는 강력한 '가드레일' 역할을 수행합니다.

# 주요 대화 흐름 분석

1. **초기 탐색 및 후보 제시**: 사용자가 처음 직무를 요청하면(`initial_search`), 시스템은 `recommend_jobs`를 통해 후보 목록을 검색하고 `present_candidates`가 이 목록을 사용자에게 제시하는 것으로 답변이 마무리됩니다.
2. **심층 분석**: 사용자가 후보 중 하나를 선택하면(`select_job`), 시스템은 `load_selected_job`으로 해당 공고를 상태에 고정한 뒤, `get_company_info` (기본 정보), `research_for_advice` (면접/문화 정보), `get_preparation_advice` (맞춤형 합격 전략)를 순차적으로 실행하여 정보를 수집하고 가공합니다. 최종적으로 `generate_final_answer`가 모든 수집된 정보를 종합하여 분석 보고서를 생성합니다.
3. **후속 질문 (Q&A)**: 심층 분석이 끝난 공고에 대해 추가 질문(`follow_up_qa`)이 들어오면, `contextual_qa` 노드가 LLM의 판단에 따라 웹 검색을 동적으로 수행하여 답변을 생성합니다.
4. **조건 변경 및 재탐색**: 사용자가 "다른 회사 찾아줘" 또는 "재택근무 가능한 곳으로" 와 같이 새로운 검색을 요청하면(`new_search`), 시스템은 `reformulate_query` 노드를 먼저 호출합니다. 이 노드는 전체 대화 맥락을 바탕으로 최적의 새 검색어를 생성하여 `recommend_jobs`를 다시 실행합니다.
    
    ```mermaid
    graph TD
        subgraph "시작 및 상태 관리"
            A(START) --> B[main.py: load_state]
            B --> C[parse_input_node]
            C --> D{analyze_intent_node}
        end
    
        subgraph "의도 기반 동적 라우팅"
            D -- "initial_search (첫 질문)" --> E[recommend_jobs]
            D -- "new_search (다른거 찾아줘)" --> F[reformulate_query]
            D -- "select_job (1번 알려줘)" --> H[load_selected_job]
            D -- "follow_up_qa (연봉은?)" --> I[contextual_qa]
            D -- "chit_chat (고마워)" --> J[generate_final_answer]
        end
    
        subgraph "핵심 작업 경로"
            subgraph "A. 신규 추천 경로"
                F --> E
                E --> K[present_candidates]
                K --> J
            end
    
            subgraph "B. 심층 분석 경로"
                H --> L[get_company_info]
                L --> M[research_for_advice]
                M --> N[get_preparation_advice]
                N --> J
            end
    
            subgraph "C. 후속 질문 경로"
                I --> I1[웹 검색 수행]
                I1 --> I2[답변 생성]
                I2 --> J
            end
        end
    
        subgraph "종료 및 기록"
            J --> O[record_history]
            O --> P(END)
        end
    
        %% 스타일링
        style D fill:#cde4ff,stroke:#444,stroke-width:2px
        style J fill:#d5fada,stroke:#444,stroke-width:2px
        style P fill:#ffcaca,stroke:#444,stroke-width:2px
        style A fill:#ffcaca,stroke:#444,stroke-width:2px
        style I1 fill:#fff2cc,stroke:#444,stroke-width:1px
        style I2 fill:#fff2cc,stroke:#444,stroke-width:1px
    ```
    

# 고급 기능 및 강점

- **상태 기반 맥락 유지**: `pkl`과 `json`으로 대화 상태를 영구 저장하여, 사용자와의 이전 대화를 완벽하게 기억하고 이어 나갈 수 있습니다.
- **지능형 검색어 재구성**: 단순 키워드 검색을 넘어, LLM이 대화의 전체 흐름을 이해하고 사용자의 숨은 의도까지 반영하여 검색어를 동적으로 재구성합니다.
- **다단계 정보 수집 및 종합**: 하나의 질문에 답하기 위해 채용 공고, 웹 검색(기본 정보, 면접 후기, 기업 문화) 등 여러 소스의 정보를 종합하여, 깊이 있고 실행 가능한 조언을 생성합니다.
- **오류 방지 라우팅**: LLM의 의도 분석 실수를 코드 레벨의 상태 확인을 통해 보완함으로써, 워크플로우가 논리적 오류에 빠지는 것을 방지하는 높은 안정성을 갖추었습니다.

# 결론

본 워크플로우는 단순한 정보 검색 챗봇을 넘어, 사용자와의 상호작용을 통해 점진적으로 문제를 해결해 나가는 **정교한 대화형 에이전트**의 모범적인 사례입니다. 상태 관리, 동적 라우팅, 외부 도구 연동, LLM을 활용한 추론 등 LangGraph의 핵심 기능을 효과적으로 활용하여, 복잡한 멀티턴 대화 시나리오를 안정적으로 처리할 수 있는 뛰어난 아키텍처를 구현했습니다.
