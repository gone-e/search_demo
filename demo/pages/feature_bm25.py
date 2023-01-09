import os
import sys
sys.path.append(".")
from collections import OrderedDict
import streamlit as st
import pandas as pd
from services import card_dev
from myelasticsearch.query import ESQuery
from myelasticsearch.query_custom import ESCustomQuery
from myelasticsearch.test.bm25 import get_normalized_bm25_body
from myelasticsearch.explainer import ESExplainParser
from demo.utils import get_analyze_result
from demo.visualize import draw_dist

def make_table(es_result, norm=None):
    try:
        items = es_result["hits"]["hits"]
    except:
        print(f"[ERROR] Request failed: es_result is {es_result}")
        return

    table = []
    for item in items:
        explain = item["_explanation"]
        doc = item["_source"]
        data = OrderedDict()
        data["id"] = item["_id"] 
        data["score"] = item["_score"]

        if norm is not None:
            if norm == "정규화없음":
                explained = ESExplainParser.get_bm25_explain(explain)
                for term, scoredict in explained.items():
                    if term in ["avgdl", "dl"]:
                        continue
                    if term == "lengthNorm":
                        data["lengthNorm"] = scoredict
                        continue
                    for score, value in scoredict.items():
                        if score == "score":
                            data[f"{term}"] = value
                        else:
                            data[f"{term}.{score}"] = value
            else:
                explained = ESExplainParser.get_bm25_scripted_explain(explain)
                for term, scoredict in explained.items():
                    for score, value in scoredict.items():
                        if score == "score":
                            data[f"{term}"] = value
                        else:
                            data[f"{term}.{score}"] = value

        data["desc"] = doc["description"] 

        table.append(data)
    # return pd.DataFrame(table).round(2).to_html(escape=False, index=False)
    return pd.DataFrame(table).round(3).to_html(escape=False, index=False).replace('table', 'table class="small-font"')

def set_bg_uprank_cell(html_table, uprank_ids):
    # <td>108245</td>
    for id in uprank_ids:
        html_table = html_table.replace(f"<td>{id}<", f'<td bgcolor="#0ccf6d">{id}<')
    return html_table

def get_uprank_ids(es_result, anchor_ids):
    uprank_ids = []
    for rank, item in enumerate(es_result["hits"]["hits"]):
        id = item["_id"]
        if id not in anchor_ids:
            uprank_ids.append(id)
        else:
            if rank < anchor_ids.index(id):
                uprank_ids.append(id)
    return uprank_ids

def guide_section():
    with st.expander("BM25 Formula & Normalization Factor"):
        st.subheader("BM25 Formula")
        st.latex(r"""
            \text{Given a query } Q, \text{ containing terms } q_1, q_2, ...,q_N, \\ \; \\
            \text{BM25(q, d)}_{elasticsearch} =: \sum_{i}^{N}\text{idf}(q_i) \left(\frac{\text{tf}_i}{\text{tf}_i + k_1(1-b+b \times \text{lengthNorm})} \right) (\text{q.boost})   \\ \text{ where } k_1=1.2 \text{ and } b=0.75 \text{ and } \text{q.boost}=1.0 \\
            \text{idf}(q_i) = \log \left( 1 + \frac{N - \text{df}_i + 0.5}{\text{df}_i + 0.5} \right) 
        """) 
        st.subheader("정규화 버전 1. (idfL2Norm)")
        st.latex(r"""
            \text{BM25NormFactor} = \frac{1}{\sqrt{\sum_{i}^{N}(\text{q.boost} \times \text{idf}(q_i))^2}}
        """)
        st.subheader("정규화 버전 2. (idfL1Norm)")
        st.latex(r"""
            \text{BM25NormFactor} = \frac{1}{\sum_{i}^{N}|\text{q.boost} \times\text{idf}(q_i)|}
        """)
        st.subheader("정규화 버전 3. (idfMaxNorm)")
        st.latex(r"""
            \text{BM25NormFactor} = \frac{1}{\text{idf}_{max}} \text{ where } \text{df}_i = 1
        """)
        st.subheader("정규화 버전 4. (idfMaxNormSaturatedQboost)")
        st.latex(r"""
            \text{idfMaxNorm과 동일하되 } \text{q.boost} \text{ 를 변형}
        """)

def page():
    """ BM25 정규화 결과를 볼 수 있는 페이지 
    [formula]
      * elasticsearch formula
      * idfL2Norm version
      * idfL1Norm version
      * idfMaxNorm version
    
    [sample query & query]
    
    [best topk documents]

    [by id]
    """
    guide_section()

    query_to_docid = {
        "원룸": "",
        "원룸인테리어": "",
        "인테리어": "",
        "원룸인테리어 쇼파 거실꾸미기": "",
        "#거실 #안방 #원룸 #원룸인테리어 #거실인테리어": "16046151", 
        "lg전자냉장고": "12197921",
    }

    query = st.selectbox(
        "Search",
        query_to_docid.keys(),
    )
    input_query = st.text_input(
        label="Search",
        placeholder="검색어를 입력해주세요."
    )

    if input_query.strip():
        query = input_query

    if query:

        st.info("동일 점수의 경우 순위 차이는 의미가 없습니다. 현재는 description 필드에 대해서만 실험합니다!")
        st.info("기존 BM25 랭킹 대비 순위가 상승한 문서는 디버깅 용도로 초록색으로 표시됩니다.")
        option_anlyzer = st.radio(label="SearchAnalyzer:", options=["korean_syn", "korean"])
        option_view = st.radio(label="View:", options=["detail", "simple"])

        st.subheader("Query Analyzer")
        res = get_analyze_result(card_dev, query, analyzers=["korean", "korean_syn"])
        st.write(res)

        st.subheader("Result")

        norm_list=[
        	"정규화없음",
        	"idfL2Norm",
        	# "idfL2NormSaturatedQboost",
        	# "idfL1Norm",
        	"idfMaxNorm",
        	"idfMaxNormSaturatedQboost",
        ]


        if option_view == "simple":
            cols = st.columns(len(norm_list))

            for col, norm in zip(cols, norm_list):
                res = body = get_normalized_bm25_body(query, norm, analyzer=option_anlyzer)
                res = card_dev.get_search_result(
                    query=query, 
                    request_body=body,
                    explain=True,
                    top_k=10
                )

                html_table = make_table(res)
                if norm == "정규화없음":
                    anchor_ids = [item["_id"] for item in res["result"]["hits"]["hits"]]
                else:
                    uprank_ids = get_uprank_ids(res, anchor_ids)
                    html_table = set_bg_uprank_cell(html_table, uprank_ids)

                col.markdown(f"""`{norm}`""")
                # draw_dist([x["_score"] for x in res["hits"]["hits"]], writer=col, xlabel='Rank', ylabel='Score')
                col.write(html_table, unsafe_allow_html=True)
        else:

            for norm in norm_list:
                res = body = get_normalized_bm25_body(query, norm, analyzer=option_anlyzer)
                res = card_dev.get_search_result(
                    query=query, 
                    request_body=body,
                    explain=True,
                    top_k=10
                )

                html_table = make_table(res, norm)
                if norm == "정규화없음":
                    anchor_ids = [item["_id"] for item in res["result"]["hits"]["hits"]]
                else:
                    uprank_ids = get_uprank_ids(res, anchor_ids)
                    html_table = set_bg_uprank_cell(html_table, uprank_ids)

                st.markdown(f"""### `{norm}`""")
                # draw_dist([x["_score"] for x in res["hits"]["hits"]], writer=st, xlabel='Rank', ylabel='Score')
                st.write(html_table, unsafe_allow_html=True)
