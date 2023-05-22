import logging
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
ES_DEV = SERVICE_TO_ES[SERVICE]


def load_random_query(data):
    df = pd.read_csv(data, keep_default_na=False)
    out = {}
    for idx, row in df.iterrows():
        out[row["search_keyword"]] = dict(row)
    return out


def get_nlu(search_keyword):
    url = f"https://search-nlu.datahou.se/analysis?v=v2&query={search_keyword}"
    return requests.get(url).json()


def get_es_doc(pid):
    url = f"""https://search-dev.dev.es.datahou.se:443/commerce_search_2023-01-11t06351673418938__gone/_doc/{pid}/"""
    return requests.get(url).json()


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

        tobe1_request_body = copy.deepcopy(tobe_request_body)

        # new_matching_query
        tobe_request_body['query']['boosting']['positive']['function_score']['query']['bool']['filter'][2]['bool'][
            'must'][0]['multi_match']['fields'].append("option_properties")

        tobe_request_body['query']['boosting']['positive']['function_score']['query']['bool']['filter'][1][
            'multi_match']['fields'].append("option_properties")

        nlu_res = get_nlu(query)
        print(nlu_res)
        # slot_data = {}
        # for r in nlu_res['result_list']:
        #    for s in r:
        #        slot_data[s['slot_type']] = s['slot_text']

        if len(nlu_res['result_list']) > 0:
            slot_data = {s['slot_type']: s['slot_text'] for s in nlu_res['result_list'][0]['curr_list']}
            # slot_data = {s['slot_type']:s['slot_text'] for r in nlu_res['result_list'][0] for s in r['curr_list']}

        property_match_query = ""

        query_property = ""
        target_properties = ["형태", "소재", "기능"]
        for target_property in target_properties:
            if target_property in slot_data.keys():
                query_property = target_property

        if query_property:
            property_match_query = \
                {
                    "bool": {
                        "should": [
                            {
                                "bool": {
                                    "must": [
                                        {
                                            "multi_match": {
                                                "fields": [
                                                    "brand_name^3",
                                                    "brand_name.standard^3",
                                                    "brand_name.no_syn^3",
                                                    "name^5",
                                                    "name.standard^5",
                                                    "name.no_syn^5",
                                                    "search_keywords^2",
                                                    "search_keywords.standard^2",
                                                    "reinforcement^2",
                                                    "reinforcement.keyword^2",
                                                    "search_admin_categories^0.1",
                                                    "admin_category_keywords^0.1",
                                                    "display_category_keywords^0.1",
                                                    "display_category_leaf_depth_names^0.1",
                                                ],
                                                "minimum_should_match": "1%",
                                                "query": query,
                                                "type": "cross_fields"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "bool": {
                                    "must": [
                                        {
                                            "multi_match": {
                                                "fields": [
                                                    "brand_name^3",
                                                    "brand_name.standard^3",
                                                    "brand_name.no_syn^3",
                                                    "name^5",
                                                    "name.standard^5",
                                                    "name.no_syn^5",
                                                    "search_keywords^2",
                                                    "search_keywords.standard^2",
                                                    "reinforcement^2",
                                                    "reinforcement.keyword^2",
                                                    "search_admin_categories^0.1",
                                                    "admin_category_keywords^0.1",
                                                    "display_category_keywords^0.1",
                                                    "display_category_leaf_depth_names^0.1",
                                                ],
                                                "minimum_should_match": "1%",
                                                "query": query.replace(slot_data[query_property], ""),
                                                #"query": query,
                                                "type": "cross_fields"
                                            }
                                        },
                                        {
                                            "match": {
                                                "option_properties": {
                                                    "query": slot_data[query_property],
                                                    "operator": "and"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }

        if property_match_query:
            tobe1_request_body['query']['boosting']['positive']['function_score']['query']['bool']['filter'][1]['multi_match']['fields'].append("option_properties^0.1")
            tobe1_request_body['query']['boosting']['positive']['function_score']['query']['bool']['filter'][2] = property_match_query

        tobe_res = ES.get_search_result(
            request_body=tobe_request_body,
            explain=True,
            top_k=constants.TOP_K,
            with_elapsed=True,
        )

        tobe1_res = ES.get_search_result(
            # request_body=multimatch_to_match.generate(query, top_k=constants.TOP_K),
            # request_body=add_matching_similarity.generate(query, top_k=constants.TOP_K),
            # request_body=proximity.generate(query, top_k=constants.TOP_K),
            # request_body=normalize_bm25.generate(query, top_k=constants.TOP_K),
            # request_body=should_validate2.generate(query, top_k=constants.TOP_K),
            request_body=tobe1_request_body,
            explain=True,
            top_k=constants.TOP_K,
            with_elapsed=True,
        )

        tobe_docs = get_docs(tobe_res)
        tobe1_docs = get_docs(tobe1_res)

        # 검색쿼리문
        col1, mid, col2 = st.columns([1, 1, 1])
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
            debug_cols = st.columns(3)
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

            score_list = [doc["_score"] for doc in tobe1_docs]
            #print(doc)
            plot = visualize.draw_distribution(
                score_list,
                x="Rank",
                y="Score",
                title="v1(only card) Score Distribution"
            )
            debug_cols[1].pyplot(plot)
            # debug_cols[1].write(f'검색결과수: {tobe_res["result"]["hits"]["total"]["value"]}')

            score_list = [doc["_score"] for doc in tobe_docs]
            plot = visualize.draw_distribution(
                score_list,
                x="Rank",
                y="Score",
                title="v2(click, sim) Score Distribution"
            )
            debug_cols[2].pyplot(plot)
            # debug_cols[1].write(f'검색결과수: {tobe_res["result"]["hits"]["total"]["value"]}')

        num_cols = 8    # 홀수로 변경: 5 또는 7 권장
        col_size_list = [1]*num_cols

        borders = []

        for idx, size in enumerate(col_size_list):
            if (idx+1) % 3 == 0:
                col_size_list[idx] = 0.2
                borders.append(idx)

        cols = st.columns(col_size_list)

        left_cols = cols[:borders[0]]
        mid_cols = cols[borders[0]+1:borders[1]]
        right_cols = cols[borders[1]+1:]

        for name, docs in [("asis", asis_docs), ("tobe", tobe_docs), ("tobe1", tobe1_docs)]:
            # select columns
            if name == "asis":
                this_cols = left_cols
            elif name == "tobe1":
                this_cols = mid_cols
            else:
                this_cols = right_cols

            if len(docs) == 0:
                col = this_cols[0]
                col.subheader("🙈 검색결과없음!")
                continue

            for rank, doc in enumerate(docs):
                col = this_cols[rank % 2]

                if rank == constants.SHOW_K:
                    break

                with col:
                    doc_url, _ = ES.get_document(doc["_id"], only_return_url=True)

                    rank_diff = 0
                    if (rank % 2) == 3 or (rank % 2) == 4:
                        rank_diff = get_rank_changes(asis_id2rank, tobe1_id2rank, doc["_id"], constants.TOP_K)
                    elif (rank % 2) == 6 or (rank % 2) == 7:
                        rank_diff = get_rank_changes(asis_id2rank, tobe_id2rank, doc["_id"], constants.TOP_K)
                    else:
                        rank_diff = get_rank_changes(asis_id2rank, tobe1_id2rank, doc["_id"], constants.TOP_K)


                    col.markdown((
                        f'{rank+1}.'
                        f'{rank_diff}'
                        #f'{get_rank_changes(asis_id2rank, tobe1_id2rank, doc["_id"], constants.TOP_K)}'
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
