import sys
sys.path.append(".")
import ast
import copy
import pandas as pd
import numpy as np
from tqdm import tqdm
from services import SERVICE_TO_ES
from myelasticsearch.ltr_wrapper import LTRWrapper

ltr = LTRWrapper()


class Featurer:
    """ 클릭 기반의 랭킹데이터(base)에 미리 정의된 Featureset과 검색결과를 붙여준다 """

    def _set_click_log(self, data_path):
        """ "search_keyword", "docid", "avgRank", "stdevRank", "impressions", "clicks",
        "uimpressions", "uclicks", "scrapCnt", "qc", "cc", "uqc", "ucc" """
        print(f"... Read {data_path}")
        df = pd.read_csv(data_path)
        if "docid" not in df.columns:
            df = df.copy()
            df["docid"] = df["object_id"]
            df.insert(1, "docid", df.pop("docid"))
            df.pop("object_id")
        return df
    
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

    def add_features(self, data_path, service, featureset):
        
        def _is_in_top_k(docid, id2rank):
            if docid in id2rank:
                return True
            return False

        def _add_rank(docid, id2rank):
            return id2rank.get(docid, np.nan)

        df = self._set_click_log(data_path)
        es = self._get_elasticsearch_client(service)

        # df = df.iloc[:10000]
        num_queries = len(df["search_keyword"].unique())
        df_copy = copy.deepcopy(df)

        df = None
        for query, group_df in tqdm(df_copy.groupby(["search_keyword"]), total=num_queries):

            group_df = group_df.astype({"docid": str})
            ids = group_df["docid"].values.tolist()

            # TODO: 랭크정보는 활용하지 않는다. 그 이유는 1)클릭피드백 순위변동, 2)랭크정보로 논클릭이지만 의미있는 문서를 걸러내기도 쉽지 않음
            # 최근 검색결과 기준으로 상위 K개 문서만 대상으로 랭킹 데이터를 구성한다.
            # id2rank = self._get_id2rank(es, query, top_k=500)
            # ids 필터링
            # group_df["is_in_top_k"] = group_df.apply(lambda row: _is_in_top_k(row["docid"], id2rank), axis=1)
            # group_df["rank"] = group_df.apply(lambda row: _add_rank(row["docid"], id2rank), axis=1)
            # group_df["temp"] = group_df["rank"].isna()
            # group_df = group_df.loc[group_df["temp"] == False, :]
            # group_df.pop("temp")
            # group_df["rank"] = pd.to_numeric(group_df["rank"])
            # group_df = group_df.astype({"rank": int})
            # group_df.insert(1, "rank", group_df.pop("rank"))
            # rank_list = group_df["rank"].values.tolist()
            # max_rank = max(rank_list)
            # missing_rank_list = set(range(1, max_rank+1)).difference(set(rank_list))
            # print(query)
            # print(f"빈 랭크 개수: {max_rank - len(group_df)}")
            # print(missing_rank_list)
            # ids = group_df["docid"].values.tolist()
            # ids = [x for x in ids if x in id2rank]
            # assert ids == group_df["docid"].values.tolist()
            
            # get features by using predefined featureset
            matches = ltr.get_predefined_features(
                ids=ids,
                params={"query": query},
                service=service,
                featureset=featureset
            )

            if len(matches) == 0:
                continue

            features = self._extract_features(matches)
            features_df = pd.DataFrame(features)
            # NOTE: 조회된 문서만 활용한다.
            group_df = pd.merge(
                group_df, 
                features_df,
                left_on="docid", 
                right_on="docid", 
                how="right"
            )
            # not_found_cnt = before_len - len(group_df)
            # if not_found_cnt:
            #     ids_sr = set([x["docid"] for x in features])
            #     not_found_ids = set(ids).difference(ids_sr)
            #     print(f"[Warning] {query}: {len(ids)} 중 {not_found_cnt}개의 데이터가 조회되지 않았습니다")
            #     print(f"  > 미조회: {not_found_ids}")
            #     print(f"  Stage2 색인이 최신화되었는지 확인해보세요.")
            # print(group_df.head())

            if df is None:
                df = group_df
            else:
                df = pd.concat([df, group_df])
        
        return df

            
def main():
    # pd.set_option('display.max_columns', 1000)
    # pd.set_option('display.max_rows', 1000)
    # FIXME
    # from reranking.card.featureset_v2 import FEATURE_SET, SERVICE
    from reranking.card.featureset_v3 import FEATURE_SET, SERVICE
    import datetime
    DATA_CREATED_AT = datetime.datetime.today().strftime("%Y%m%d")
    DATA_CREATED_AT = '20220504'

    featurer = Featurer()
    periods = ["3m"]

    for period in periods:

        data_path = f"../rdataset/{SERVICE}/base/{SERVICE}.ranking.{period}.{DATA_CREATED_AT}.csv"

        df = featurer.add_features(
            data_path=data_path,
            service=SERVICE, 
            featureset=FEATURE_SET
        )

        # dump
        save_path = data_path.replace(".csv", ".features.csv")
        print(f"... save to csv: {save_path}")
        df.to_csv(save_path, index=False)
            

if __name__ == "__main__":
    main()
            
            
            
            
            
            
            
            
            
            
            
