import sys
sys.path.append(".")
import ast
import copy
import pandas as pd
import numpy as np
import argparse
import multiprocessing as mp
from functools import partial
from collections import deque
from tqdm import tqdm
from services import SERVICE_TO_ES
from myelasticsearch.ltr_wrapper import LTRWrapper

ltr = LTRWrapper()


class Featurer:
    """ 클릭 기반의 랭킹데이터(base)에 미리 정의된 Featureset과 검색결과를 붙여준다 """

    def _get_elasticsearch_client(self, service):
        es = SERVICE_TO_ES.get(service)
        if es is None:
            raise ValueError
        return es
    
    def _get_id2rank(self, es, query, top_k=1000):
        res = es.get_search_result(query=query, doc_fields={"excludes": "*"}, top_k=top_k)
        try:
            id2rank = {str(x["_id"]):rank+1 for rank, x in enumerate(res["result"]["hits"]["hits"])}
        except:
            id2rank = {}
        return id2rank
    
    def _extract_features(self, matches, id2rank=None):
        features = [] 
        for doc in matches:
            # feature column prefix: f__
            temp = {f"f__{x}":y for x, y in zip(doc["ltr_features_name"], doc["ltr_features"])}
            temp.update({"docid": str(doc["_id"])})
            if id2rank is not None:
                temp.update({"rank": id2rank.get(doc["_id"], np.nan)})
            features.append(temp)
        return features

    def add_features(self, df, service, featureset):
        query = df["search_keyword"].unique()[0]
        df = df.astype({"docid": str})
        ids = df["docid"].values.tolist()

        # get features by using predefined featureset
        matches = ltr.get_predefined_features(
            ids=ids,
            params={"query": query},
            service=service,
            featureset=featureset
        )

        if len(matches) == 0:
            return

        features = self._extract_features(matches)
        features_df = pd.DataFrame(features)

        # NOTE: 조회된 문서만 활용한다.
        df = pd.merge(
            df, 
            features_df,
            left_on="docid", 
            right_on="docid", 
            how="right"
        )
        
        return df

def _set_click_log(data_path):
    """ "search_keyword", "docid", "avgRank", "stdevRank", "impressions", "clicks",
    "uimpressions", "uclicks", "scrapCnt", "qc", "cc", "uqc", "ucc" """
    print(f"... Read {data_path}")
    df = pd.read_csv(data_path)
    if "docid" not in df.columns:
        df = df.copy()
        df["docid"] = df["object_id"]
        df.insert(1, "docid", df.pop("docid"))
        df.pop("object_id")
    print(f"[DataLen] {len(df)}")
    return df
    
def mp_func(gdf, featurer, service, featureset):
    """ independent function worked by each processe """
    print(f"[proc][query={gdf['search_keyword'].unique()[0]}] {mp.current_process()}", flush=True)
    return featurer.add_features(
        df=gdf,
        service=service, 
        featureset=featureset
    )

def main():
    """ max_cores = os.cpu_count() """
    # FIXME
    # from reranking.card.featureset_v2 import FEATURE_SET, SERVICE
    from reranking.card.featureset_v3 import FEATURE_SET, SERVICE
    import datetime

    NUM_WORKERS = 10
    DATA_CREATED_AT = datetime.datetime.today().strftime("%Y%m%d")
    DATA_CREATED_AT = '20220504'

    featurer = Featurer()

    periods = ["1m"]
    for period in periods:

        data_path = f"./rdataset/{SERVICE}/{DATA_CREATED_AT}/{SERVICE}.click.ranking.{period}.csv"
        df = _set_click_log(data_path)
        # df = df.loc[:10000]

        # initialize Pool Class
        pool = mp.Pool(processes=NUM_WORKERS)
        gdf_list = pool.map(
            partial(mp_func, featurer=featurer, service=SERVICE, featureset=FEATURE_SET),
            [gdf for _, gdf in df.groupby(["search_keyword"])]
        )
        pool.close()

        # dump
        df = pd.concat([x for x in gdf_list if x is not None])
        df = df.sort_values(["search_keyword"])
        save_path = data_path.replace(".csv", ".features.csv")
        print(f"... save to csv: {save_path}")
        df.to_csv(save_path, index=False)

        
if __name__ == "__main__":
    main()