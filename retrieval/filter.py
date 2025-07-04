import json
import re
import argparse

def extract_job_fields(text):
    def extract(pattern, default="(Unknown)"):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else default

    role    = extract(r"직무:\s*([^\n]+)")
    company = extract(r"회사:\s*([^\n]+)")
    region  = extract(r"지역:\s*([^\n]+)", default="")  # 예시
    exp     = extract(r"(신입|경력)[^\n]*", default="기타")
    url     = extract(r"채용공고 URL:\s*(https?://\S+)", default="(No URL)")
    techs   = []
    for m in re.finditer(r"(기술스택|우대기술):\s*([^\n]+)", text):
        techs += [t.strip() for t in m.group(2).split(",")]

    return {
        "role": role,
        "company": company,
        "region": region,
        "experience": exp,
        "url": url,
        "skills": techs
    }

def compute_final_score(user, job, dense_score):
    desired_role = user['preferences'].get('desired_role', '')
    user_skills  = set(user.get('skills', {}).get('tech_stack', []))
    user_region  = user.get('location', '')
    user_is_exp  = user.get('career', {}).get('years', 0) > 0

    is_role_match   = desired_role and desired_role in job['role']
    tech_overlap    = len(user_skills & set(job['skills']))
    is_region_match = user_region and user_region in job['region']
    is_exp_match    = ("경력" in job['experience']) == user_is_exp

    score = (
        0.5 * dense_score +
        0.2 * int(is_role_match) +
        0.15 * min(tech_overlap / 3, 1.0) +
        0.1 * int(is_region_match) +
        0.05 * int(is_exp_match)
    )

    explanation = []
    if is_role_match:
        explanation.append("✔️ 희망 직무와 일치")
    if tech_overlap > 0:
        explanation.append(f"✔️ 기술스택 {tech_overlap}개 일치")
    if is_region_match:
        explanation.append("✔️ 지역 조건 일치")
    if is_exp_match:
        explanation.append("✔️ 경력 조건 일치")

    return score, explanation

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topk_json", required=True, help="Top-K 결과 JSON 파일")
    parser.add_argument("--user_json", required=True, help="유저 프로필 JSON 파일")
    args = parser.parse_args()

    with open(args.topk_json, encoding="utf-8") as f:
        topk = json.load(f)
    with open(args.user_json, encoding="utf-8") as f:
        user = json.load(f)

    reranked = []

    for item in topk:
        text = item["text"]
        dense_score = item["score"]
        job = extract_job_fields(text)
        final_score, explanation = compute_final_score(user, job, dense_score)

        reranked.append({
            "score": final_score,
            "dense": dense_score,
            "job": job,
            "explanation": explanation
        })

    reranked.sort(key=lambda x: x["score"], reverse=True)
    best = reranked[0]

    print(f"\n🎯 최종 Top-1 추천 공고\n")
    print(f"회사: {best['job']['company']}")
    print(f"직무: {best['job']['role']}")
    print(f"링크: {best['job']['url']}")
    print(f"최종 점수: {best['score']:.4f} (Dense: {best['dense']:.4f})")
    print("매칭 근거:")
    for line in best["explanation"]:
        print(f"   - {line}")

if __name__ == "__main__":
    main()