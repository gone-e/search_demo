import sys
sys.path.append(".")
import copy
import streamlit as st
import pandas as pd
from services import SERVICE_TO_ES
from ranking.commerce import *
# import demo.commerce.utils as card_utils
import demo.commerce.constants as constants
import demo.commerce.view as commerce_view
from demo.utils import (
    get_docs, 
    get_id2rank,
    get_rank_changes,
    get_analyze_result, 
    get_service_doc_url, 
    timediff
)
from demo.ohs_image import get_image_url
import demo.visualize as visualize
from myelasticsearch.explainer import ESExplainParser
import requests



# FIXME
SERVICE = "commerce"
TOBE_SERVICE = "commerce_dev"
DATA_CREATED_AT = "20220509"
ES = SERVICE_TO_ES[SERVICE]
ES_DEV = SERVICE_TO_ES[TOBE_SERVICE]

def load_random_query(data):
    df = pd.read_csv(data, keep_default_na=False)
    out = {}
    for idx, row in df.iterrows():
        out[row["search_keyword"]] = dict(row)
    return out


# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def page():
    """ 내외부 공유 용도의 페이지 """
    st.title("🧽 스토어 검색(Commerce Search) 데모")

    option_debug = st.radio("Mode", ["Debug", "Normal"])

    querydata = load_random_query(f"../dataset/{SERVICE}/search_keywords.qc10.1w.1K.{DATA_CREATED_AT}.csv")

    query = st.selectbox(
        "Search",
        querydata.keys()
    )

    input_query = st.text_input(
        label="Search",
        placeholder="검색어를 입력해주세요."
    )

    content_only_negative = {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "fields": [
                            "content_keywords"
                        ],
                        "operator": "and",
                        "query": input_query
                    }
                }
            ],
            "must_not": [
                {
                    "multi_match": {
                        "fields": [
                            "brand_name",
                            "brand_name.standard",
                            "brand_name.no_syn",
                            "name",
                            "name.standard",
                            "name.no_syn",
                            "search_keywords",
                            "search_keywords.standard",
                            "reinforcement",
                            "reinforcement.keyword",
                            "search_admin_categories",
                            "options"
                        ],
                        "operator": "and",
                        "query": input_query,
                        "type": "cross_fields"
                    }
                }
            ]
        }
    }

    if input_query.strip():
        query = input_query

    if query:
        st.subheader("Query Analyzer")

        dat = querydata.get(query)
        if dat is None:
            dat = {}

        st.subheader("[사진탭 기준] 모바일앱: 4-6개 결과 / 웹: 4-8개 결과")
        st.subheader((
            f"Result"
            f" [QC={dat.get('qc')}, CC={dat.get('cc')}, CTR={dat.get('ctr', -1):.1f}"
            f", uQC(nSearchUsers)={dat.get('uqc')}, uCC(nClickUsers)={dat.get('ucc')}, uCTR={dat.get('uctr', -1):.1f}]"
        ))

        asis_res = ES.get_search_result(
            query, 
            # request_body=asis.generate(query, top_k=constants.TOP_K),
            # request_body=multimatch.generate(query, top_k=constants.TOP_K),
            # request_body=should_validate.generate(query, top_k=constants.TOP_K),
            explain=True, 
            top_k=constants.TOP_K,
            with_elapsed=True,
        )
        asis_docs = get_docs(asis_res)

        tobe_request_body = ES.get_service_request_body(query=query, page_size=constants.TOP_K, timeout_secs=20)

        # new_matching_query
        tobe_request_body['query']['boosting']['positive']['function_score']['query']['bool']['filter'][2]['bool']['must'][0]['multi_match']['fields'].append("content_keywords")
        tobe_request_body['query']['boosting']['positive']['function_score']['query']['bool']['filter'][1]['multi_match'][
            'fields'].append("content_keywords")

        tobe_request_body['query']['boosting']['negative']['bool']['should'].append(content_only_negative)
        """
        if brand_query_res.get("brand_keyword"):
            new_rank_features = [
                {
                    "filter": {
                        "bool": {
                            "minimum_should_match": 1,
                            "should": [
                                {
                                    "multi_match": {
                                        "fields": [
                                            "brand_name",
                                            "processed_brand_name",
                                            "brand_name.standard",
                                            "brand_name.no_syn"
                                        ],
                                        "operator": "or",
                                        "query": brand_query_res.get("brand_keyword"),
                                        "type": "cross_fields"
                                    }
                                }
                            ]
                        }
                    },
                    "weight": 0.02068615
                }
            ]

            tobe_request_body['query']['boosting']['positive']['function_score']['functions'] = tobe_request_body['query']['boosting']['positive']['function_score']['functions'] + new_rank_features
        """
        #print(tobe_request_body)

        tobe_res = ES.get_search_result(
            # request_body=multimatch_to_match.generate(query, top_k=constants.TOP_K),
            # request_body=add_matching_similarity.generate(query, top_k=constants.TOP_K),
            # request_body=proximity.generate(query, top_k=constants.TOP_K),
            # request_body=normalize_bm25.generate(query, top_k=constants.TOP_K),
            # request_body=should_validate2.generate(query, top_k=constants.TOP_K),
            request_body=tobe_request_body,
            explain=True, 
            top_k=constants.TOP_K,
            with_elapsed=True,
        )

        tobe1_res = ES_DEV.get_search_result(
            # request_body=multimatch_to_match.generate(query, top_k=constants.TOP_K),
            # request_body=add_matching_similarity.generate(query, top_k=constants.TOP_K),
            # request_body=proximity.generate(query, top_k=constants.TOP_K),
            # request_body=normalize_bm25.generate(query, top_k=constants.TOP_K),
            # request_body=should_validate2.generate(query, top_k=constants.TOP_K),
            request_body=tobe_request_body,
            explain=True,
            top_k=constants.TOP_K,
            with_elapsed=True,
        )

        tobe_docs = get_docs(tobe_res)
        tobe1_docs = get_docs(tobe1_res)

        # 검색쿼리문
        col1, mid, col2 = st.columns([1, 0.2, 1])
        with col1:
            with st.expander("Request Body"):
                st.json(asis_res["requestBody"])

        with mid:
            with st.expander("Request Body"):
                st.json(tobe1_res["requestBody"])

        with col2:
            with st.expander("Request Body"):
                st.json(tobe_res["requestBody"])

        asis_id2rank = get_id2rank(asis_docs)
        tobe_id2rank = get_id2rank(tobe_docs)
        tobe1_id2rank = get_id2rank(tobe1_docs)

        if option_debug == "Debug":
            debug_cols = st.columns(2)
            # extra_cols[0].info(f"elapsed: {asis_elapsed}")
            # extra_cols[1].info(f"elapsed: {tobe_elapsed}")
            score_list = [doc["_score"] for doc in asis_docs]
            plot = visualize.draw_distribution(
                score_list, 
                x="Rank", 
                y="Score", 
                title="ASIS Score Distribution"
            )
            debug_cols[0].pyplot(plot)
            # debug_cols[0].write(f'검색결과수: {asis_res["result"]["hits"]["total"]["value"]}')

            score_list = [doc["_score"] for doc in tobe_docs]
            plot = visualize.draw_distribution(
                score_list, 
                x="Rank", 
                y="Score", 
                title="TOBE Score Distribution"
            )
            debug_cols[1].pyplot(plot)
            # debug_cols[1].write(f'검색결과수: {tobe_res["result"]["hits"]["total"]["value"]}')

        num_cols = 5    # 홀수로 변경: 5 또는 7 권장
        mid = int((num_cols-1)/2)
        col_size_list = [1]*num_cols
        col_size_list[mid] *= 0.2   # this is border
        cols = st.columns(col_size_list)
        left_cols = cols[:mid]
        mid_cols = cols[mid]
        right_cols = cols[mid+1:]

        for name, docs in [("asis", asis_docs), ("tobe", tobe_docs), ("tobe1", tobe1_docs)]:
            # select columns
            if name == "asis":
                this_cols = left_cols
            elif name == "tobe1":
                this_cols = mid_cols
            else:
                this_cols = right_cols

            if len(docs) == 0:
                col = this_cols[0 % mid]
                col.subheader("🙈 검색결과없음!")
                continue

            for rank, doc in enumerate(docs):
                if name=='tobe1':
                    col = this_cols
                else:
                    col = this_cols[rank % mid]

                if rank == constants.SHOW_K:
                    break

                with col:
                    doc_url, _ = ES.get_document(doc["_id"], only_return_url=True)

                    col.markdown((
                        f'{rank+1}.'
                        f'{get_rank_changes(asis_id2rank, tobe_id2rank, doc["_id"], constants.TOP_K)}'
                        f' **`점수:{doc["_score"]}`**'
                        f' [{doc["_id"]}]({get_service_doc_url("스토어", doc["_id"])})'
                        f' [`doc`]({doc_url})'
                        # f' `{timediff(doc["created_at"][:10])}`'
                    ))
                    commerce_view.service_view(
                        col=col,
                        rank=rank+1, 
                        doc=doc, 
                        doc_url=doc_url, 
                        use_badges=False, 
                        debug=True if option_debug == "Debug" else False
                    )
