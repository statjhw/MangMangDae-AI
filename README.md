# 망망대 프로젝트

이 프로젝트는 실무와 유사한 환경에서 협업을 진행하기 위해 아래의 **코드 리뷰, 테스트 자동화, 코드 스타일** 규칙을 따릅니다.  
이 규칙을 준수하여 코드 품질을 유지하고, 효율적인 개발을 진행합니다.  

---

## 📌 1. 실무 환경 조성

### ✅ 1.1 GitHub Pull Request(PR) 기반 코드 리뷰
- 모든 코드 변경 사항은 **Pull Request(PR)**를 통해 리뷰 후 병합합니다.
- **2명 이상의 코드 리뷰 승인(`Approve`)이 필요**하며, 승인 없이 `main` 브랜치에 Merge할 수 없습니다.

#### 참고 자료
https://wayhome25.github.io/git/2017/07/08/git-first-pull-request-story/

### ✅ 1.2 코드 포맷팅 자동화
코드 스타일을 통일하고 일관성을 유지하기 위해 `black`과 `isort`를 사용합니다.

#### 📌 **포맷팅 도구 설치 및 실행**
```bash
pip install black isort
black .
isort .
```

### ✅ 1.3 커밋 컨벤션 (Commit Naming & 단위)

PR 리뷰를 원활하게 하기 위해, 커밋 메시지는 Conventional Commits 규칙을 따릅니다.

📌 커밋 메시지 예시
```plantext
feat: 모델 서빙 API 추가
fix: AI 예측 결과 JSON 응답 오류 수정
refactor: 데이터 파이프라인 코드 리팩토링
test: 모델 서빙 엔드포인트 유닛테스트 추가
docs: README.md 수정
```

## 2. 테스트 환경 조성

### 2.1 pytest 기반 유닛 테스트
- 모든 함수 및 기능 추가 시 유닛 테스트(pytest)를 작성해야 합니다.
- PR 생성 시, pytest를 통과하지 않으면 Merge가 불가능합니다.

### 2.2 GitHub Actions을 이용한 자동화 (CI/CD)

Github Actions을 활용하여 PR이 생성되거나 코드 변경 시 자동으로 pytest 실행합니다.

#### pytest와 CI 환경 조성 참고자료
https://various-grouse-4e1.notion.site/pytest-and-github-action-1798597bc5a580078ed0eb60016666b5?pvs=4

## 3. 프로젝트 협업 규칙 정리
| 항목         | 규칙                           |
|-------------|------------------------------|
| **코드 리뷰** | GitHub PR 리뷰 필수           |
| **코드 포맷팅** | `black`, `isort` 자동 적용   |
| **커밋 메시지** | `feat`, `fix`, `refactor`, `test` 등 사용 |
| **Merge 기준** | **2명 이상의 승인 필요**       |
| **테스트 자동화** | `pytest` + GitHub Actions 적용 |
