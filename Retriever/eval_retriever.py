# evaluation_script.py
import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple
from hybrid_retriever import hybrid_search # 위에서 제공된 리트리버 코드를 모듈로 가정

def evaluate_retriever_and_save_results(data_path: str, top_k: int = 5):
    """
    전체 리트리버 성능을 평가하고, 직무별 상세 결과를 JSON 파일로 저장합니다.

    Args:
        data_path (str): 가짜 데이터셋이 담긴 JSON 파일 경로.
        top_k (int): 리트리버가 반환할 상위 문서의 개수.
    """
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 경로를 다시 확인해주세요.")
        return
    except json.JSONDecodeError:
        print(f"오류: '{file_path}' 파일이 유효한 JSON 형식이 아닙니다.")
        return

    # 전체 및 직무별 성능 지표를 저장할 변수
    overall_hit_count = 0
    overall_reciprocal_rank_sum = 0
    overall_total_queries = len(dataset)
    
    category_results = defaultdict(lambda: {'hit_count': 0, 'reciprocal_rank_sum': 0, 'total_queries': 0})

    print(f"--- 리트리버 성능 평가 시작 (총 {overall_total_queries}개 쿼리, top_k={top_k}) ---")

    for i, data_point in enumerate(dataset, 1):
        query_info = data_point['query']
        gold_doc_id = data_point['gold_doc_id']
        category_name = query_info.get('candidate_interest', '기타')

        # 리트리버 호출
        _, retrieved_doc_ids, _ = hybrid_search(user_profile=query_info, top_k=top_k)

        # 평가 지표 계산
        rank = 0
        for idx, doc_id in enumerate(retrieved_doc_ids):
            if doc_id == gold_doc_id:
                rank = idx + 1
                break
        
        # 전체 성능 지표 업데이트
        if rank > 0:
            overall_hit_count += 1
            overall_reciprocal_rank_sum += 1 / rank
            print(f"✅ 쿼리 {i}/{overall_total_queries}: 정답 문서 발견! 순위: {rank} (직무: {category_name})")
        else:
            print(f"❌ 쿼리 {i}/{overall_total_queries}: 정답 문서 미발견. 정답 ID: {gold_doc_id} (직무: {category_name})")
        
        # 직무별 성능 지표 업데이트
        category_results[category_name]['total_queries'] += 1
        if rank > 0:
            category_results[category_name]['hit_count'] += 1
            category_results[category_name]['reciprocal_rank_sum'] += 1 / rank

    # 최종 결과 계산
    overall_hit_rate = overall_hit_count / overall_total_queries if overall_total_queries > 0 else 0
    overall_mrr = overall_reciprocal_rank_sum / overall_total_queries if overall_total_queries > 0 else 0
    
    final_results = {
        'overall': {
            'total_queries': overall_total_queries,
            'hit_rate': overall_hit_rate,
            'mrr': overall_mrr,
        },
        'by_category': {}
    }

    print("\n" + "="*80)
    print("⭐ 최종 종합 평가 결과 ⭐")
    print(f"총 쿼리 수: {overall_total_queries}")
    print(f"적중 쿼리 수: {overall_hit_count}")
    print(f"평가 기준: 상위 {top_k}개 결과")
    print(f"Hit Rate (적중률): {overall_hit_rate:.4f}")
    print(f"MRR: {overall_mrr:.4f}")
    print("="*80)

    # 직무별 상세 결과 계산 및 출력
    print("\n⭐ 직무별 상세 평가 결과 ⭐")
    print("="*80)
    for category, results in category_results.items():
        category_hit_rate = results['hit_count'] / results['total_queries'] if results['total_queries'] > 0 else 0
        category_mrr = results['reciprocal_rank_sum'] / results['total_queries'] if results['total_queries'] > 0 else 0
        
        print(f"▷ 직무: {category} (쿼리 수: {results['total_queries']}개)")
        print(f"  - Hit Rate (적중률): {category_hit_rate:.4f}")
        print(f"  - MRR: {category_mrr:.4f}")
        print("-" * 80)

        final_results['by_category'][category] = {
            'total_queries': results['total_queries'],
            'hit_rate': category_hit_rate,
            'mrr': category_mrr
        }
    
    # 결과를 파일로 저장
    output_file_name = "evaluation_results.json"
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file_name)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ 평가 결과가 '{output_file_name}' 파일에 저장되었습니다.")


if __name__ == "__main__":
    # 이전에 만든 가짜 데이터 파일 경로
    fake_data_file = "retriever_sample_data.json"
    
    # 평가 실행
    evaluate_retriever_and_save_results(fake_data_file, top_k=5)