import sys
sys.path.append(".")
import copy
import streamlit as st
import pandas as pd
from services import SERVICE_TO_ES
from ranking.card import *
import demo.card.utils as card_utils
import demo.card.constants as constants
import demo.card.view as card_view
import demo.card.data_loader as data_loader
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


# FIXME
SERVICE = "card"
ES = SERVICE_TO_ES[SERVICE]

def load_random_query(data):
    df = pd.read_csv(data, keep_default_na=False)
    out = {}
    for idx, row in df.iterrows():
        out[row["search_keyword"]] = dict(row)
    return out

# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def page():
    """ 내외부 공유 용도의 페이지 """
    st.title("🌁 사진 검색(Card Search) 데모")

    option_debug = st.radio("Mode", ["Debug", "Normal"])

    querydata = load_random_query(f"../dataset/{SERVICE}/search_keywords.qc10.1w.1K.20220509.csv")

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
        res = get_analyze_result(ES, query, analyzers=["korean", "korean_syn"])
        st.write(res)

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
            # request_body=summation.generate(query, top_k=constants.TOP_K),
            # request_body=summation_with_factors.generate(query, top_k=constants.TOP_K),
            explain=True, 
            top_k=constants.TOP_K,
            with_elapsed=True,
        )
        asis_docs = get_docs(asis_res)

        # # TODO: OPTION으로 빼거나 하기
        # # LTR_MODEL = "xgb-lambdamart-1w.v3.20220427.card.test.v1"
        # # LTR_MODEL = "xgb-lambdamart-20220429.card.click.ranking.base.1w.features.grade.txt.card.featureset.v2"
        # # LTR_MODEL = "xgb-lambdamart-20220503.card.click.ranking.base.1w.features.grade.binary.txt.card.featureset.v2"
        # # LTR_MODEL = "xgb-lambdamart-20220503.card.click.ranking.base.1m.features.grade.binary.txt.card.featureset.v2"
        LTR_MODEL = "xgb-lambdamart-20220504.card.click.ranking.base.1m.features.grade.binary.txt.card.featureset.v3"
        # LTR_MODEL = "xgb-lambdamart-20220504.card.click.ranking.3m.features.grade.binary.txt-card.featureset.v3"
        # st.info(f"LTR Model: {LTR_MODEL}")
        tobe_res = ES.get_search_result(
            # request_body=ltr_test.generate(query, ltr_model=LTR_MODEL, top_k=constants.TOP_K),
            # request_body=ltr_all.generate(query, ltr_model=LTR_MODEL, top_k=constants.TOP_K),
            # request_body=summation.generate(query, top_k=constants.TOP_K),
            request_body=summation_with_factors2.generate(query, top_k=constants.TOP_K),
            explain=True,
            top_k=constants.TOP_K,
            with_elapsed=True,
            timeout_secs=30,
        )

        tobe_docs = get_docs(tobe_res)

        # 검색쿼리문
        col1, _, col2 = st.columns([1, 0.2, 1])
        with col1:
            with st.expander("Request Body"):
                st.json(asis_res["requestBody"])
        with col2:
            with st.expander("Request Body"):
                st.json(tobe_res["requestBody"])

        asis_id2rank = get_id2rank(asis_docs)
        tobe_id2rank = get_id2rank(tobe_docs)

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
            score_list = [doc["_score"] for doc in tobe_docs]
            plot = visualize.draw_distribution(
                score_list, 
                x="Rank", 
                y="Score", 
                title="TOBE Score Distribution"
            )
            debug_cols[1].pyplot(plot)

        num_cols = 5    # 홀수로 변경: 5 또는 7 권장
        mid = int((num_cols-1)/2)
        col_size_list = [1]*num_cols
        col_size_list[mid] *= 0.2   # this is border
        cols = st.columns(col_size_list)
        left_cols = cols[:mid]
        right_cols = cols[mid+1:]

        for name, docs in [("asis", asis_docs), ("tobe", tobe_docs)]:
            # select columns
            if name == "asis":
                this_cols = left_cols
            else:
                this_cols = right_cols
            
            if len(docs) == 0:
                col = this_cols[0 % mid]
                col.subheader("🙈 검색결과없음!")
                continue

            for rank, doc in enumerate(docs):
                col = this_cols[rank % mid]

                if rank == constants.SHOW_K:
                    break

                with col:
                    doc_url, _ = ES.get_document(doc["_id"], only_return_url=True)
                    
                    col.markdown((
                        f'{rank+1}.'
                        f'{get_rank_changes(asis_id2rank, tobe_id2rank, doc["_id"], constants.TOP_K)}'
                        f' **`점수:{doc["_score"]:.4f}`**'
                        f' [{doc["_id"]}]({get_service_doc_url("사진", doc["_id"])})'
                        f' [`doc`]({doc_url})'
                        f' `{timediff(doc["created_at"][:10])}`'
                    ))
                    card_view.service_view(
                        col=col,
                        rank=rank+1, 
                        doc=doc, 
                        doc_url=doc_url, 
                        use_badges=False, 
                        debug=True if option_debug == "Debug" else False
                    )


