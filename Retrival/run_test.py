import json, sys
from hybrid_retriever import ensemble_retriever

def build_prompt(user: dict) -> str:
    parts = []
    if lvl := user.get("education",{}).get("level"):
        parts.append(f"학력:{lvl}")
    if yrs := user.get("career",{}).get("years"):
        parts.append(f"{yrs}년차 {user['career']['job_category']}")
    if skills := user.get("skills",{}).get("tech_stack",[]):
        parts.append(f"기술:{', '.join(skills)}")
    if sal := user.get("preferences",{}).get("desired_salary"):
        parts.append(f"희망연봉:{sal}")
    prof = "; ".join(parts)
    conv = user.get("conversation","")
    return f"{conv}  |  프로필: {prof}"

if __name__=="__main__":
    user_file = sys.argv[1] if len(sys.argv)>1 else "fake_user.json"
    user = json.load(open(user_file, encoding="utf-8"))
    prompt = build_prompt(user)

    hits = ensemble_retriever(prompt, top_k=5)

    # ➊ 반환된 raw hits 전체 구조 확인
    print("=== RAW HITS ===")
    for h in hits:
        print(h)
    print()

    # ➋ ID만 따로 뽑아서 확인
    print("=== RETURNED IDs ===")
    for i, h in enumerate(hits,1):
        print(f"[{i}] {h.get('id')!r}")
    print()

    # ➌ 기존 출력을 그대로
    print("=== FORMATTED OUTPUT ===")
    for i, h in enumerate(hits,1):
        # 이제 ID가 어떤 값인지 확인했으니, 아래 라인에 원하는 필드를 넣으세요
        print(f"[{i}] {h.get('title')} | {h.get('company')} | {h.get('location')} | rerank={h.get('rerank')}")
