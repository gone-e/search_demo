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
# from ranking.commerce import *
# SERVICE = "commerce"
# from ranking.advice import *
# SERVICE = "advice"
from ranking.question import *
SERVICE = "question"
# from ranking.project import *
# SERVICE = "project"

# set topK
TOP_K = 300

# set elasticsearch client
ES = SERVICE_TO_ES[SERVICE]

    
def load_test_queries(data_path="./dataset/query.rs.1K.20220321.20220327.csv"):
    return pd.read_csv(data_path)

def get_ids(es_result):
    try:
        items = es_result["result"]["hits"]["hits"]
    except:
        print("[ERROR] parsing search result is failed")
        return
    return [x["_id"] for x in items]

def main():
    # get sample query
    df = load_test_queries(f"./dataset/{SERVICE}/search_keywords.qc10.1w.1K.20220509.csv")

    evaluations = {
        "total": 0,
        "errorCnt": 0,
    }
    error_queries = []
    for idx, row in df.iterrows():
        if idx == 100:
            break

        evaluations["total"] += 1
        query = row["search_keyword"]

        res = ES.get_search_result(
            query, 
            explain=True, 
            top_k=TOP_K,
            with_elapsed=True,
        )
        ids = get_ids(res)
        elapsed = res["elapsed"]
        
        print(f"[query: {query}][performance: {elapsed}]")
            
        if ids is None:
            evaluations["errorCnt"] += 1
            print(f"!에러: {query}")
            error_queries.append(query)
            continue
        
        if len(ids) == 0:
            print(f"!검색결과없음: {query}")
            continue

    
    # summary
    print(error_queries[:10])

        

if __name__ == "__main__":
    main()