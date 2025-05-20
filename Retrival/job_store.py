import json
import os

# 원본 JSONL 파일 경로
JSONL_PATH = os.path.expanduser("../wanted.result.updated.jsonl")

# 메모리에 전체 로드 (파일 크기가 너무 크면 캐싱 로직 변경 필요)
_job_map = {}
with open(JSONL_PATH, encoding="utf-8") as f:
    for line in f:
        job = json.loads(line)
        _job_map[job["url"]] = job

def get_meta_by_id(job_id: str) -> dict:
    """
    job_id(URL)로 원본 JSONL에서 메타 데이터를 꺼내
    통일된 포맷으로 반환합니다.
    """
    job = _job_map.get(job_id, {})
    return {
        "id":          job_id,
        "title":       job.get("title", ""),
        "company":     job.get("company_name", ""),
        "description": job.get("position_detail", "") or "",
        "location":    job.get("location", ""),
        "category":    job.get("job_name", ""),  # 소프트웨어 직군 등
    }
    