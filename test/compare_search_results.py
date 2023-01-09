import sys
sys.path.append(".")
import math
import json
import pandas as pd
import numpy as np
from collections import OrderedDict
from services import SERVICE_TO_ES

# FIXME
# from ranking.card import *
# SERVICE = "card"
from ranking.commerce import *
SERVICE = "commerce"
# from ranking.advice import *
# SERVICE = "advice"
# from ranking.question import *
# SERVICE = "question"
# from ranking.project import *
# SERVICE = "project"

# set topK
# TOP_K = 300
TOP_K = 100

# set elasticsearch client
ES = SERVICE_TO_ES[SERVICE]

def get_id2rank(ids):
    id2rank = OrderedDict()
    for rank, id in enumerate(ids):
        id2rank[id] = rank + 1
    return id2rank

def get_rank_changes(asis_ids, tobe_id2rank, top_k):
    """ asis 랭크를 줄여서 본다 """
    changes = []
    for asis_rank, id in enumerate(asis_ids):
        changes.append(abs(asis_rank+1 - tobe_id2rank.get(id, top_k+1)))
    return changes

def get_ids(es_result):
    try:
        items = es_result["result"]["hits"]["hits"]
    except:
        print("[ERROR] parsing search result is failed")
        return
    return [x["_id"] for x in items]
    
def load_test_queries(data_path="./dataset/query.rs.1K.20220321.20220327.csv"):
    return pd.read_csv(data_path)

def get_diff_ratio(asis_ids, tobe_ids):
    if len(asis_ids) == 0:
        return 1.0
    diff_cnt = 0
    for a, b in zip(asis_ids, tobe_ids):
        if a != b:
            diff_cnt += 1
    return diff_cnt / len(asis_ids)

def get_set_diff_ratio(asis_ids, tobe_ids):
    diff_cnt = len(set(asis_ids).difference(set(tobe_ids)))
    return diff_cnt / len(asis_ids)

def _print_evaluations_result(evaluations):
    print(f"\n=== summary ===")
    print(f"[{SERVICE}]")
    print(f"Total Evaluation Sets: {evaluations['total']}")
    print(f"Errors: {evaluations['errorCnt']}")

    print(f"검색결과({TOP_K}개 기준) 순서 변화가 있는 질의비율: {sum(1 for x in evaluations['diffRatio'] if x != 0)/len(evaluations['diffRatio'])*100:.2f}%")
    print(f"상위 4개 문서 기준으로 순서가 바뀐 문서 비율(평균값): {np.mean(evaluations['diffRatio@4'])*100:.2f}%")
    print(f"상위 12개 문서 기준으로 순서가 바뀐 문서 비율(평균값): {np.mean(evaluations['diffRatio@12'])*100:.2f}%")
    print(f"상위 36개 문서 기준으로 순서가 바뀐 문서 비율(평균값): {np.mean(evaluations['diffRatio@36'])*100:.2f}%")
    print(f"상위 64개 문서 기준으로 순서가 바뀐 문서 비율(평균값): {np.mean(evaluations['diffRatio@64'])*100:.2f}%")
    # print(f"상위 100개 문서 기준으로 순서가 바뀐 문서 비율(평균값): {np.mean(evaluations['diffRatio@100'])*100:.2f}%")
    # print(f"상위 200개 문서 기준으로 순서가 바뀐 문서 비율(평균값): {np.mean(evaluations['diffRatio@200'])*100:.2f}%")
    print(f"상위 {TOP_K}개 문서 기준으로 순서가 바뀐 문서 비율(평균값): {np.mean(evaluations['diffRatio'])*100:.2f}%")

    print(f"상위 5개 문서 기준으로 랭크 변동치(평균값): {np.mean(evaluations['RankDiffRatio@5']):.4f}")
    print(f"상위 10개 문서 기준으로 랭크 변동치(평균값): {np.mean(evaluations['RankDiffRatio@10']):.4f}")
    print(f"상위 20개 문서 기준으로 랭크 변동치(평균값): {np.mean(evaluations['RankDiffRatio@20']):.4f}")
    print(f"상위 40개 문서 기준으로 랭크 변동치(평균값): {np.mean(evaluations['RankDiffRatio@40']):.4f}")
    print(f"상위 5개 문서 기준으로 랭크 변동치(평균값)(변동치=0 제외): {np.mean([x for x in evaluations['RankDiffRatio@5'] if x != 0.0]):.4f}")
    print(f"상위 10개 문서 기준으로 랭크 변동치(평균값)(변동치=0 제외): {np.mean([x for x in evaluations['RankDiffRatio@10'] if x != 0.0]):.4f}")
    print(f"상위 20개 문서 기준으로 랭크 변동치(평균값)(변동치=0 제외): {np.mean([x for x in evaluations['RankDiffRatio@20'] if x != 0.0]):.4f}")
    print(f"상위 40개 문서 기준으로 랭크 변동치(평균값)(변동치=0 제외): {np.mean([x for x in evaluations['RankDiffRatio@40'] if x != 0.0]):.4f}")

    print(f"상위 5개 문서 기준으로 못보던 문서가 있는 비율(평균값): {np.mean(evaluations['SetDiffRatio@5'])*100:.4f}%")
    print(f"상위 10개 문서 기준으로 못보던 문서가 있는 비율(평균값): {np.mean(evaluations['SetDiffRatio@10'])*100:.4f}%")
    print(f"상위 20개 문서 기준으로 못보던 문서가 있는 비율(평균값): {np.mean(evaluations['SetDiffRatio@20'])*100:.4f}%")
    print(f"상위 40개 문서 기준으로 못보던 문서가 있는 비율(평균값): {np.mean(evaluations['SetDiffRatio@40'])*100:.4f}%")

    # print(f"Elasped Changes: +{np.mean(evaluations['elapsedChanges']):.2f}%")

def main():
    # get sample query
    df = load_test_queries(f"./dataset/{SERVICE}/search_keywords.qc10.1w.1K.20220509.csv")

    evaluations = {
        "total": 0,
        "diffRatio": [],         # 검색결과 변화크기 확인
        "diffRatio@4": [],
        "diffRatio@12": [],
        "diffRatio@36": [],
        "diffRatio@64": [],
        # "diffRatio@100": [],
        # "diffRatio@200": [],
        "RankDiffRatio@5": [],     # 문서 순위 변화폭 확인(예: asis 1등 문서 -> tobe: 12등 문서 => rank_diff = 11)
        "RankDiffRatio@10": [],
        "RankDiffRatio@20": [],
        "RankDiffRatio@40": [],
        "SetDiffRatio@5": [],
        "SetDiffRatio@10": [],
        "SetDiffRatio@20": [],
        "SetDiffRatio@40": [],
        "errorCnt": 0,
        "elapsedChanges": [],    # 속도 비교
        "elapsedASIS": [],
        "elapsedTOBE": [],
    }
    diff_queries = []
    diff_queries_top12 = []
    error_queries = []
    for idx, row in df.iterrows():
        if idx == 100:
            break

        evaluations["total"] += 1
        query = row["search_keyword"]

        res = ES.get_search_result(
            # query, 
            # request_body=multimatch.generate(query, top_k=TOP_K),
            request_body=asis.generate(query, top_k=TOP_K),
            explain=True, 
            top_k=TOP_K,
            with_elapsed=True,
        )
        asis_ids = get_ids(res)
        asis_elapsed = res["elapsed"]

        # LTR_MODEL = "xgb-lambdamart-20220429.card.click.ranking.base.1w.features.grade.txt.card.featureset.v2"
        res = ES.get_search_result(
            # request_body=ltr_test.generate(query, ltr_model=LTR_MODEL, top_k=TOP_K),
            # request_body=tobe.generate(query, top_k=TOP_K),
            # request_body=bm25norm.generate(query, top_k=TOP_K),
            # request_body=add_matching_similarity.generate(query, top_k=TOP_K),
            # request_body=multimatch_to_match.generate(query, top_k=TOP_K),
            request_body=normalize_bm25.generate(query, top_k=TOP_K),
            explain=True,
            top_k=TOP_K,
            with_elapsed=True,
            timeout_secs=30,
        )
        tobe_ids = get_ids(res)
        tobe_elapsed = res["elapsed"]
            
        print((
            f"[query: {query}][performance: {tobe_elapsed / asis_elapsed * 100:.2f}%]"
            f" asis={asis_elapsed}, tobe={tobe_elapsed}"
        ))
        evaluations["elapsedChanges"].append(tobe_elapsed / asis_elapsed * 100)

        if asis_ids is None or tobe_ids is None:
            evaluations["errorCnt"] += 1
            print(f"!에러: {query}")
            error_queries.append(query)
            continue
        
        if len(asis_ids) == 0 or len(tobe_ids) == 0:
            if len(asis_ids) == 0:
                print(f"!검색결과없음(ASIS): {query}")
            if len(tobe_ids) == 0:
                print(f"!검색결과없음(TOBE): {query}")
            continue

        tobe_id2rank = get_id2rank(tobe_ids)

        diff_ratio = get_diff_ratio(asis_ids, tobe_ids)
        if diff_ratio:
            diff_queries.append((query, diff_ratio))

        diff_ratio = get_diff_ratio(asis_ids[:12], tobe_ids[:12])
        if diff_ratio:
            diff_queries_top12.append((query, diff_ratio))

        evaluations["diffRatio"].append(get_diff_ratio(asis_ids, tobe_ids))
        evaluations["diffRatio@4"].append(get_diff_ratio(asis_ids[:4], tobe_ids[:4]))
        evaluations["diffRatio@12"].append(get_diff_ratio(asis_ids[:12], tobe_ids[:12]))
        evaluations["diffRatio@36"].append(get_diff_ratio(asis_ids[:36], tobe_ids[:36]))
        evaluations["diffRatio@64"].append(get_diff_ratio(asis_ids[:64], tobe_ids[:64]))
        # evaluations["diffRatio@100"].append(get_diff_ratio(asis_ids[:100], tobe_ids[:100]))
        # evaluations["diffRatio@200"].append(get_diff_ratio(asis_ids[:200], tobe_ids[:200]))

        evaluations["RankDiffRatio@5"].extend(get_rank_changes(asis_ids[:5], tobe_id2rank, top_k=TOP_K))
        evaluations["RankDiffRatio@10"].extend(get_rank_changes(asis_ids[:10], tobe_id2rank, top_k=TOP_K))
        evaluations["RankDiffRatio@20"].extend(get_rank_changes(asis_ids[:20], tobe_id2rank, top_k=TOP_K))
        evaluations["RankDiffRatio@40"].extend(get_rank_changes(asis_ids[:40], tobe_id2rank, top_k=TOP_K))

        evaluations["SetDiffRatio@5"].append(get_set_diff_ratio(asis_ids[:5], tobe_ids[:5]))
        evaluations["SetDiffRatio@10"].append(get_set_diff_ratio(asis_ids[:10], tobe_ids[:10]))
        evaluations["SetDiffRatio@20"].append(get_set_diff_ratio(asis_ids[:20], tobe_ids[:20]))
        evaluations["SetDiffRatio@40"].append(get_set_diff_ratio(asis_ids[:40], tobe_ids[:40]))
    
    # summary
    # print(evaluations["RankDiffRatio@5"])
    _print_evaluations_result(evaluations)
    print(f"--- 차이나는 질의(@{TOP_K}) Top10 ---")
    diff_queries = [x for x, _ in sorted(diff_queries, key=lambda x:x[1], reverse=True)]
    print(diff_queries[:10])
    print("--- 차이나는 질의(@12) Top10 ---")
    diff_queries = [x for x, _ in sorted(diff_queries_top12, key=lambda x:x[1], reverse=True)]
    print(diff_queries[:10])
    print("--- 에러 질의 Top10 ---")
    print(error_queries[:10])

        

if __name__ == "__main__":
    main()