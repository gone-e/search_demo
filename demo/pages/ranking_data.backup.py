from dataclasses import dataclass
import os
import sys
from tkinter import W
sys.path.append(".")
from collections import OrderedDict
import ast
import copy
import streamlit as st
import pandas as pd
import numpy as np
from services import card_dev, commerce_dev, advice_dev, question_dev, project_dev
from myelasticsearch.query import ESQuery
from myelasticsearch.query_custom import ESCustomQuery
from myelasticsearch.test.bm25 import get_normalized_bm25_body
from myelasticsearch.explainer import ESExplainParser
from demo import SERVICE_LIST, SERVICE_LIST_REV
from demo.utils import get_analyze_result, get_service_doc_url, timediff
from demo.ohs_image import get_image_url
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

# @st.cache
def load_data_and_es(service, option_period, option_version="v2"):
    if option_version == "v1":
        option_version = ""
    else:
        option_version += "."
    
    if service == "스토어":
        es = commerce_dev
    elif service == "사진":
        es = card_dev
    elif service == "노하우":
        es = advice_dev
    elif service == "집들이":
        es = project_dev
    elif service == "질문과답변":
        es = question_dev
    else:
        raise ValueError(f"Not supported service: {service}")
    return (
        es,
        pd.read_csv(f"../dataset/{SERVICE_LIST_REV[service]}/{SERVICE_LIST_REV[service]}.click.ranking.base.{option_period}.rs.1K.{option_version}sr.csv")
    )

def load_view(service):
    if service == "스토어":
        return view_commerce
    elif service == "사진":
        return view_card
    elif service == "노하우":
        return view_advice
    elif service == "집들이":
        return view_project
    elif service == "질문과답변":
        return view_question
    else:
        raise ValueError(f"Not supported service: {service}")

def _doc_to_table(doc):
    # df = pd.DataFrame.from_dict(dictionary, orient='index', columns=cols[-1])
    # df = pd.DataFrame.from_dict(dictionary, orient='index')
    doc_copy = copy.deepcopy(doc)
    for k in doc_copy.keys():
        if 'url' in k:
            doc.pop(k)
        
    df = pd.DataFrame([doc])
    return df.round(3).to_html(escape=False, index=False).replace('table', 'table class="small-font"')

# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def view_card(es, dat, ranking_data):
    st.subheader("모바일앱: 4-6개 결과 / 웹: 4-8개 결과")
    top_k = 100
    delimiter = " <> "  # 리스트 원소 구분자
    desc_max_len = 40
    num_cols = 5
    cols = st.columns(num_cols)
    for i, (rank, v) in enumerate(ranking_data.items()):
        # limit by top_k
        if int(rank) > top_k:
            break

        click_cnt = v["cc"]
        col = cols[i % num_cols]

        doc_url, doc = es.get_document(id=v["id"])
        if doc is None:
            col.write("! 문서 조회되지 않음")
            continue

        with col:
            col.markdown((
                f'{rank}. '
                f' [{doc["_id"]}]({get_service_doc_url("사진", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f' `{timediff(doc["created_at"][:10])}`'
                f' `avgR:{v["avgRank"]:.1f}`'
                f' `stdR:{v["stdRank"]:.1f}`'
            ))
            col.image(get_image_url(doc['image_url'], width=180, aspect=1.3))
            col.write(doc["description"][:desc_max_len] + "..." if len(doc["description"]) > desc_max_len else doc["description"])
            col.write(f'👀 {doc["view_count"]} 🤍 {doc["praise_count"]} 👉🏻 {doc["scrap_count"]}')
            # (노이즈) 클릭 횟수는 1인 것은 제외한다.
            if click_cnt > 1:
                col.success(f'🥰 cc={v["cc"]}, qc={v["qc"]}, ctr={100*v["cc"]/v["qc"]:.1f}, ucc={v["ucc"]}, uqc={v["uqc"]}, uctr={100*v["ucc"]/v["uqc"]:.1f}')
            
            # 중요한 검색필드값을 보여주는 탭
            with st.expander("Document"):
                st.write(", ".join(["#" + str(x) for x in doc["keyword_list"]]))
                st.write(doc["description"])
                st.write("[제품] " + delimiter.join(doc["prod_name"]))
                st.write("[브랜드] " + delimiter.join(doc["prod_brand_name"]))
                st.write("[카테고리] " + delimiter.join(doc["prod_categories"]))
                if "click_keywords" in doc:
                    st.write("[클릭키워드] " + delimiter.join(doc["click_keywords"]))
                if "search_keywords" in doc:
                    st.write("[운영키워드] " + delimiter.join(doc["search_keywords"].split()))
                # st.write((
                #     f'조회수({doc["view_count"]})'
                #     f' 좋아요수({doc["praise_count"]})'
                #     f' 스크랩수({doc["scrap_count"]})'
                #     f' 답변수({doc["reply_count"]})'
                # ))

            # 스코어, 중요지표 등을 보여주는 탭
            # TODO: key mapping to readable key
            with st.expander("Values"):
                doc_copy = copy.deepcopy(doc)
                for k, v in doc.items():
                    if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict):
                        doc_copy.pop(k)
                    elif isinstance(v, float):
                        doc_copy[k] = round(v, 2)
                st.json(doc_copy)

# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def view_commerce(es, dat, ranking_data):
    st.subheader("모바일앱: 2-4개 결과 / 웹: 4-8개 결과")
    top_k = 100
    delimiter = " <> "  # 리스트 원소 구분자
    num_cols = 6
    cols = st.columns(num_cols)
    for i, (rank, v) in enumerate(ranking_data.items()):
        # limit by top_k
        if int(rank) > top_k:
            break
        doc_url, doc = es.get_document(id=v["id"])
        click_cnt = v["cc"]
            
        col = cols[i % num_cols]
        with col:
            col.markdown((
                f'{rank}. '
                f' [{doc["_id"]}]({get_service_doc_url("스토어", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f'`{timediff(doc["updated_at"][-1][:10]) if doc["updated_at"] else None}`'
            ))
            col.image(get_image_url(doc['image_url'], width=180, aspect=1.3))
            col.write(doc["name"])
            if click_cnt:
                # col.success(f"🥰 Click: {click_cnt}")
                col.success(f'🥰 cc={v["cc"]}, qc={v["qc"]}, ctr={100*v["cc"]/v["qc"]:.1f}, ucc={v["ucc"]}, uqc={v["uqc"]}, uctr={100*v["ucc"]/v["uqc"]:.1f}')
            
            # 중요한 검색필드값을 보여주는 탭
            with st.expander("Document"):
                # st.write(", ".join(["#" + str(x) for x in doc["keyword_list"]]))
                # st.write(doc["description"])
                # st.write("[제품] " + delimiter.join(doc["prod_name"]))
                # st.write("[브랜드] " + delimiter.join(doc["prod_brand_name"]))
                # st.write("[카테고리] " + delimiter.join(doc["prod_categories"]))
                if "click_keywords" in doc:
                    st.write("[클릭키워드] " + delimiter.join(doc["click_keywords"]))
                if "search_keywords" in doc:
                    st.write("[운영키워드] " + delimiter.join(doc["search_keywords"].split()))
                # st.write((
                #     f'조회수({doc["view_count"]})'
                #     f' 좋아요수({doc["praise_count"]})'
                #     f' 스크랩수({doc["scrap_count"]})'
                #     f' 답변수({doc["reply_count"]})'
                # ))

            # 스코어, 중요지표 등을 보여주는 탭
            # TODO: key mapping to readable key
            with st.expander("Values"):
                doc_copy = copy.deepcopy(doc)
                for k, v in doc.items():
                    if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict):
                        doc_copy.pop(k)
                    elif isinstance(v, float):
                        doc_copy[k] = round(v, 2)
                st.json(doc_copy)

# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def view_project(es, dat, ranking_data):
    st.subheader("모바일앱: 4-6개 결과 / 웹: 3-6개 결과")
    top_k = 100
    delimiter = " <> "  # 리스트 원소 구분자
    desc_max_len = 40
    num_cols = 4
    cols = st.columns(num_cols)
    for i, (rank, v) in enumerate(ranking_data.items()):
        # limit by top_k
        if int(rank) > top_k:
            break
        doc_url, doc = es.get_document(id=v["id"])
        click_cnt = v["cc"]
            
        col = cols[i % num_cols]
        with col:
            col.markdown((
                f'{rank}. '
                f' [{doc["_id"]}]({get_service_doc_url("집들이", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f'`{timediff(doc["created_at"][:10])}`'
            ))
            # TODO: 집들이 사진은 이미지서버에서 안되나?
            # col.image(get_image_url(doc['cover_image_url'], width=180, aspect=1.3))
            col.image(doc['cover_image_url'])
            col.write(doc["card_description"][:desc_max_len] + "..." if len(doc["card_description"]) > desc_max_len else doc["card_description"])
            if click_cnt:
                # col.success(f"🥰 Click: {click_cnt}")
                col.success(f'🥰 cc={v["cc"]}, qc={v["qc"]}, ctr={100*v["cc"]/v["qc"]:.1f}, ucc={v["ucc"]}, uqc={v["uqc"]}, uctr={100*v["ucc"]/v["uqc"]:.1f}')
            
            # 중요한 검색필드값을 보여주는 탭
            with st.expander("Document"):
                # st.write(", ".join(["#" + str(x) for x in doc["keyword_list"]]))
                # st.write(doc["description"])
                # st.write("[제품] " + delimiter.join(doc["prod_name"]))
                # st.write("[브랜드] " + delimiter.join(doc["prod_brand_name"]))
                # st.write("[카테고리] " + delimiter.join(doc["prod_categories"]))
                if "click_keywords" in doc:
                    st.write("[클릭키워드] " + delimiter.join(doc["click_keywords"]))
                if "search_keywords" in doc:
                    st.write("[운영키워드] " + delimiter.join(doc["search_keywords"].split()))
                # st.write((
                #     f'조회수({doc["view_count"]})'
                #     f' 좋아요수({doc["praise_count"]})'
                #     f' 스크랩수({doc["scrap_count"]})'
                #     f' 답변수({doc["reply_count"]})'
                # ))

            # 스코어, 중요지표 등을 보여주는 탭
            # TODO: key mapping to readable key
            with st.expander("Values"):
                doc_copy = copy.deepcopy(doc)
                for k, v in doc.items():
                    if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict):
                        doc_copy.pop(k)
                    elif isinstance(v, float):
                        doc_copy[k] = round(v, 2)
                st.json(doc_copy)

# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def view_advice(es, dat, ranking_data):
    st.subheader("모바일앱: 4-5개 결과 / 웹: 8개 결과")
    top_k = 100
    delimiter = " <> "  # 리스트 원소 구분자
    desc_max_len = 40
    num_cols = 5
    cols = st.columns(num_cols)
    for i, (rank, v) in enumerate(ranking_data.items()):
        # limit by top_k
        if int(rank) > top_k:
            break
        doc_url, doc = es.get_document(id=v["id"])
        click_cnt = v["cc"]
            
        col = cols[i % num_cols]
        with col:
            col.markdown((
                f'{rank}. '
                f' [{doc["_id"]}]({get_service_doc_url("노하우", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f'`{timediff(doc["created_at"][:10])}`'
            ))
            # 이미지-텍스트
            # col.image(get_image_url(doc['cover_image_url'], width=180, aspect=1.3))
            col.image(get_image_url(doc['cover_image_url'], width=300, height=200))
            col.write(doc["description"])
            if click_cnt:
                # col.success(f"🥰 Click: {click_cnt}")
                col.success(f'🥰 cc={v["cc"]}, qc={v["qc"]}, ctr={100*v["cc"]/v["qc"]:.1f}, ucc={v["ucc"]}, uqc={v["uqc"]}, uctr={100*v["ucc"]/v["uqc"]:.1f}')
            
            # 중요한 검색필드값을 보여주는 탭
            with st.expander("Document"):
                # st.write(", ".join(["#" + str(x) for x in doc["keyword_list"]]))
                # st.write(doc["description"])
                # st.write("[제품] " + delimiter.join(doc["prod_name"]))
                # st.write("[브랜드] " + delimiter.join(doc["prod_brand_name"]))
                # st.write("[카테고리] " + delimiter.join(doc["prod_categories"]))
                if "click_keywords" in doc:
                    st.write("[클릭키워드] " + delimiter.join(doc["click_keywords"]))
                if "search_keywords" in doc:
                    st.write("[운영키워드] " + delimiter.join(doc["search_keywords"].split()))
                # st.write((
                #     f'조회수({doc["view_count"]})'
                #     f' 좋아요수({doc["praise_count"]})'
                #     f' 스크랩수({doc["scrap_count"]})'
                #     f' 답변수({doc["reply_count"]})'
                # ))

            # 스코어, 중요지표 등을 보여주는 탭
            # TODO: key mapping to readable key
            with st.expander("Values"):
                doc_copy = copy.deepcopy(doc)
                for k, v in doc.items():
                    if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict):
                        doc_copy.pop(k)
                    elif isinstance(v, float):
                        doc_copy[k] = round(v, 2)
                st.json(doc_copy)

# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def view_question(es, dat, ranking_data):
    st.subheader("모바일앱: 1-4개 결과 / 웹: 8개 결과")
    top_k = 100
    delimiter = " <> "  # 리스트 원소 구분자
    desc_max_len = 40
    num_cols = 6
    cols = st.columns(num_cols)
    for i, (rank, v) in enumerate(ranking_data.items()):
        # limit by top_k
        if int(rank) > top_k:
            break
        doc_url, doc = es.get_document(id=v["id"])
        click_cnt = v["cc"]
        expose_cnt = v["qc"]
            
        col = cols[i % num_cols]
        with col:
            col.markdown((
                f'{rank}. '
                f' [{doc["_id"]}]({get_service_doc_url("질문과답변", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f'`{timediff(doc["created_at"][:10])}`'
            ))
            # 이미지-텍스트
            # col.image(get_image_url(doc["first_image"], width=180, aspect=1.3))
            if doc["first_image"]:
                col.image(get_image_url(doc["first_image"], width=100, height=100))
            col.write(doc["title"])
            if click_cnt:
                col.success(f'🥰 cc={v["cc"]}, qc={v["qc"]}, ctr={100*v["cc"]/v["qc"]:.1f}, ucc={v["ucc"]}, uqc={v["uqc"]}, uctr={100*v["ucc"]/v["uqc"]:.1f}')
            
            # 중요한 검색필드값을 보여주는 탭
            with st.expander("Document"):
                # st.write(", ".join(["#" + str(x) for x in doc["keyword_list"]]))
                # st.write(doc["description"])
                # st.write("[제품] " + delimiter.join(doc["prod_name"]))
                # st.write("[브랜드] " + delimiter.join(doc["prod_brand_name"]))
                # st.write("[카테고리] " + delimiter.join(doc["prod_categories"]))
                if "click_keywords" in doc:
                    st.write("[클릭키워드] " + delimiter.join(doc["click_keywords"]))
                if "search_keywords" in doc:
                    st.write("[운영키워드] " + delimiter.join(doc["search_keywords"].split()))
                # st.write((
                #     f'조회수({doc["view_count"]})'
                #     f' 좋아요수({doc["praise_count"]})'
                #     f' 스크랩수({doc["scrap_count"]})'
                #     f' 답변수({doc["reply_count"]})'
                # ))

            # 스코어, 중요지표 등을 보여주는 탭
            # TODO: key mapping to readable key
            with st.expander("Values"):
                doc_copy = copy.deepcopy(doc)
                for k, v in doc.items():
                    if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict):
                        doc_copy.pop(k)
                    elif isinstance(v, float):
                        doc_copy[k] = round(v, 2)
                st.json(doc_copy)

def view_rearrage(es, dat, ranking_data):
    st.subheader("모바일앱: 4-6개 결과 / 웹: 4-8개 결과")
    top_k = 100
    desc_max_len = 40

    # ranking data 제한
    ranking_data= {rank:docinfo for rank, docinfo in ranking_data.items() if int(rank) <= top_k}
    # ctr_list = [100*docinfo["cc"]/(docinfo["qc"]+5) for rank, docinfo in ranking_data.items()]
    ctr_list = [100*docinfo["ucc"]/(docinfo["uqc"]+5) for rank, docinfo in ranking_data.items()]
    # ranking_data_rearrange = sorted(ranking_data.items(), key=lambda x:100*x[1]["cc"]/(x[1]["qc"]+5), reverse=True)
    ranking_data_rearrange = sorted(ranking_data.items(), key=lambda x:100*x[1]["ucc"]/(x[1]["uqc"]+5), reverse=True)
    ctr_95 = np.quantile(ctr_list, 0.95)
    ctr_75 = np.quantile(ctr_list, 0.75)
    ctr_50 = np.quantile(ctr_list, 0.50)
    ctr_25 = np.quantile(ctr_list, 0.25)
    st.subheader(f"CTR {ctr_95:.1f}(95%), {ctr_75:.1f}(75%), {ctr_50:.1f}(50%), {ctr_25:.1f}(25%)")

    # column layout
    # asis, _, tobe = st.columns([5, 1, 5])
    num_cols = 7    # 홀수로 변경: 5 또는 7 권장
    mid = int((num_cols-1)/2)
    col_size_list = [1]*num_cols
    col_size_list[mid] *= 0.3   # this is border
    cols = st.columns(col_size_list)
    asis_cols = cols[:mid]
    tobe_cols = cols[mid+1:]

    # for i, (rank, v) in enumerate(ranking_data.items()):
    #     col = asis_cols[i % mid]

    #     doc_url, doc = es.get_document(id=v["id"])
    #     click_cnt = v["cc"]
    #     col.markdown((
    #         f'{rank}. '
    #         f' [{doc["_id"]}]({get_service_doc_url("사진", doc["_id"])})'
    #         f' [`doc`]({doc_url})'
    #         f' `{timediff(doc["created_at"][:10])}`'
    #         f' `avgR:{v["avgRank"]:.1f}`'
    #         f' `stdR:{v["stdRank"]:.1f}`'
    #     ))
    #     col.image(get_image_url(doc['image_url'], width=180, aspect=1.3))
    #     col.write(doc["description"][:desc_max_len] + "..." if len(doc["description"]) > desc_max_len else doc["description"])
    #     col.write(f'👀 {doc["view_count"]} 🤍 {doc["praise_count"]} 👉🏻 {doc["scrap_count"]}')
    #     # (노이즈) 클릭 횟수는 1인 것은 제외한다.
    #     # if click_cnt > 1:
    #     #     col.success(f'🥰 cc={v["cc"]}, qc={v["qc"]}, ctr={100*v["cc"]/v["qc"]:.1f}, ucc={v["ucc"]}, uqc={v["uqc"]}, uctr={100*v["ucc"]/v["uqc"]:.1f}')
    

    for i, (asis_rank, v) in enumerate(ranking_data_rearrange):

        left = asis_cols[i % mid]
        right = tobe_cols[i % mid]

        doc_url, doc = es.get_document(id=v["id"])
        click_cnt = v["cc"]
        # (노이즈) 클릭 횟수는 1인 것은 제외한다.
        # if click_cnt > 1:
        #     continue

        # ctr = 100 * v["cc"] / (v["qc"] + 5)
        ctr = 100 * v["ucc"] / (v["uqc"] + 5)
        if ctr >= ctr_95:
            col = left
        elif ctr <= ctr_25:
            col = right
        else:
            continue

        col.markdown((
            # f'{rank}. '
            # f'{asis_rank}. '
            f' [{doc["_id"]}]({get_service_doc_url("사진", doc["_id"])})'
            f' [`doc`]({str(doc_url)})'
            f'`{timediff(doc["created_at"][:10])}`'
            f' `avgR:{v["avgRank"]:.1f}`'
            f' `stdR:{v["stdRank"]:.1f}`'
        ))
        # col.markdown((
        #     f'`qc={v["qc"]}`'
        #     f' `uqc={v["uqc"]}`'
        #     f' `cc={v["cc"]}`'
        #     f' `ucc={v["ucc"]}`'
        #     f' `ctr={v["uctr"]}`'
        #     f' `uctr={v["uctr"]}`'
        #     f' `umctr={100*v["ucc"]/(v["uqc"]+5):.1f}`'
        # ))
        col.image(get_image_url(doc['image_url'], width=180, aspect=1.3))
        col.write(doc["description"][:desc_max_len] + "..." if len(doc["description"]) > desc_max_len else doc["description"])
        col.write(f'👀 {doc["view_count"]} 🤍 {doc["praise_count"]} 👉🏻 {doc["scrap_count"]}')
        if ctr >= ctr_95:
            col.info(f"[4점] ctr:{ctr:.1f}")
        elif ctr <= ctr_25:
            col.warning(f"[0~1점] ctr:{ctr:.1f}")


def page(service):
    """ 클릭 정보와 함께 검색결과를 볼 수 있는 페이지 """

    col0, col1, col2, col3, col4, col5, col6 = st.columns(7)
    option_version = col0.radio("Version", ["v2"])
    option_order = col1.radio("Order", ["검색결과", "CTR", "mCTR"])
    option_period = col2.radio("Period", ["1m", "1w"])
    option_qc = col3.radio("QC", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])
    option_cc = col4.radio("CC", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])
    option_uqc = col5.radio("UQC(=NumSearchUsers)", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])
    option_ucc = col6.radio("UCC(=NumClickUsers)", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])

    try:
        es, data_df = load_data_and_es(service, option_period, option_version)
    except:
        st.error("해당 데이터는 지원이 안됩니다")
        return

    view = load_view(service)

    # limit data by option
    def get_quantile_option_value(data_df, value, field):
        if value == "전체":
            return 0.0
        elif value == ">=25%":
            return data_df[field].quantile(0.25)
        elif value == ">=50%":
            return data_df[field].quantile(0.5)
        elif value == ">=75%":
            return data_df[field].quantile(0.75)
        elif value == ">=95%":
            return data_df[field].quantile(0.95)
        else:
            raise ValueError

    option_qc = get_quantile_option_value(data_df, option_qc, "qc")
    option_cc = get_quantile_option_value(data_df, option_cc, "cc")
    option_uqc = get_quantile_option_value(data_df, option_uqc, "uqc")
    option_ucc = get_quantile_option_value(data_df, option_ucc, "ucc")
    st.write(f"QC>={option_qc}, CC>={option_cc}, UQC(NumSearchUsers)>={option_uqc}, UCC(NumClickUsers)>={option_ucc}")

    new_data_df = data_df[
        (data_df.qc >= option_qc ) 
        & (data_df.cc >= option_cc) 
        & (data_df.uqc >= option_uqc) 
        & (data_df.ucc >= option_ucc) 
    ]
    query2data = {row["search_keyword"]:row.to_dict() for idx, row in new_data_df.iterrows()}
    if len(data_df) != len(new_data_df):
        st.info(f"데이터 개수: {len(data_df)} -> {len(new_data_df)}")
    
    query = st.selectbox(
        "예제 질의들:",
        query2data.keys()
    )

    input_query = st.text_input(
        label="검색창:",
        placeholder="샘플질의에 있는 질의만 동작합니다. 해당 질의를 입력해주세요."
    )

    if input_query.strip() and input_query in query2data:
        query = input_query
        # 쿼리를 직접 입력한 경우에는 전체 질의에서 찾기 위해 다시 전체 데이터로 바꿔준다.
        query2data = {row["search_keyword"]:row.to_dict() for idx, row in data_df.iterrows()}

    if query:
        # st.header(es.env)
        # st.header(es.service)
        # st.header(view)

        st.subheader("Query Analyzer")
        # col1, col2 = st.columns(2)
        res = get_analyze_result(card_dev, query, analyzers=["korean", "korean_syn"])
        st.write(res)

        dat = query2data[query]

        st.subheader((
            f"Result"
            f" [QC={dat.get('qc')}, CC={dat.get('cc')}, CTR={dat.get('ctr'):.0f}"
            f", uQC(nSearchUsers)={dat.get('uqc')}, uCC(nClickUsers)={dat.get('ucc')}, uCTR={dat.get('uctr'):.0f}]"
        ))

        # ranking_data = ast.literal_eval(dat["rank2clickCntAndId"])
        ranking_data = ast.literal_eval(dat["rank2docinfo"])

        # click distribution (top100)
        click_list = [x["ucc"] for rank, x in ranking_data.items() if int(rank) <= 100]
        avg_click = np.mean(click_list)
        avg_click_nonzero = np.mean([x for x in click_list if x > 0])
        draw_dist(click_list, writer=st, figsize=(30,2), hlines=[avg_click, avg_click_nonzero], title="uCC(top100)")
        # uctr distribution (top100)
        uctr_list = [100*x["ucc"]/(x["uqc"]+5) for rank, x in ranking_data.items() if int(rank) <= 100]
        avg_uctr = np.mean(uctr_list)
        avg_uctr_nonzero = np.mean([x for x in uctr_list if x > 0])
        draw_dist(uctr_list, writer=st, figsize=(30,2), hlines=[avg_uctr, avg_uctr_nonzero], title="uCTR(top100)")

        if option_order == "검색결과":
            view(es, dat, ranking_data)
        else:
            # TODO: 현재 카드만 지원
            view_rearrage(es, dat, ranking_data)
        
        #TODO: query, page 파라미터 받아서 overwrite하기
