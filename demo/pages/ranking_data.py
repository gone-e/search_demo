import sys
sys.path.append(".")
from collections import OrderedDict
import random
import glob
import ast
import copy
import streamlit as st
import pandas as pd
import numpy as np
from services import card_dev, SERVICE_TO_ES
from myelasticsearch.query import ESQuery
from myelasticsearch.query_custom import ESCustomQuery
from myelasticsearch.test.bm25 import get_normalized_bm25_body
from myelasticsearch.explainer import ESExplainParser
from demo import SERVICE_LIST, SERVICE_LIST_REV
from demo.utils import get_analyze_result, get_service_doc_url, timediff
from demo.ohs_image import get_image_url
import demo.visualize as visualize
import demo.card.view as card_view

from plotnine import *

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
def load_data_and_es(service, option_data):
    return (
        SERVICE_TO_ES[SERVICE_LIST_REV[service]],
        pd.read_csv(option_data)
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
def view_card(es, df, opt_order):

    if opt_order == "Label":

        # with st.expander("Visualize"):
        #     viz_cols = [x for x in df.columns if x.endswith(".bm25") or x.endswith(".proximity")]
        #     num_cols = 2
        #     cols = st.columns(num_cols)
        #     for i, colname in enumerate(viz_cols):
        #         cols[i%num_cols].pyplot(visualize.draw_scatter_plot(df, x="factor(grade)", y=colname, figsize=(14,2)))

        # 기준(예: grade)에 따라 문서를 나눠주기
        grade_list = sorted(df.grade.unique())
        cols = st.columns(len(grade_list))
        for col, grade in zip(cols, grade_list):
            col.subheader(f"{grade}점")
            for _, row in df[df.grade == grade].iterrows():
                # get document info
                doc_url, doc = es.get_document(id=row["docid"])
                if doc is None:
                    col.write("! 문서 조회되지 않음")
                    continue

                # get features
                features = {k.replace("f__", ""):v for k, v in row.items() if k.startswith("f__")}

                # grade 별 feature 분포
                card_view.ranking_data_view(col, rank=None, doc=doc, doc_url=doc_url, row=row)

    elif opt_order == "mCTR":
        num_cols = 4
        cols = st.columns(num_cols)
        df = df.sort_values(["mctr"], ascending=False)[:100]
        for rank, (_, row) in enumerate(df.iterrows()):
            col = cols[rank % num_cols]
            # get document info
            doc_url, doc = es.get_document(id=row["docid"])
            if doc is None:
                col.write("! 문서 조회되지 않음")
                continue

            col.markdown((
                f'{rank}.'
                f' [{row["grade"]}점]'
                f' [{doc["_id"]}]({get_service_doc_url("사진", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f' `{timediff(doc["created_at"][:10])}`'
                f' `avgRank:{row["avgRank"]:.1f}`'
                f' `stdevRank:{row["stdevRank"]:.1f}`'
                f' `clicks:{row["clicks"]}`'
                f' `imps:{row["impressions"]}`'
                f' `uclicks:{row["uclicks"]}`'
                f' `uimps:{row["uimpressions"]}`'
                f' `uctr:{row["uclicks"]/row["uimpressions"]:.1f}`'
                f' `mctr:{row["mctr"]:.1f}`'
            ))

            card_view.ranking_data_view(col, rank=None, doc=doc, doc_url=doc_url, row=row, use_badges=False)

    elif opt_order == "Clicks":
        num_cols = 4
        cols = st.columns(num_cols)
        df = df.sort_values(["uclicks"], ascending=False)[:100]
        for rank, (_, row) in enumerate(df.iterrows()):
            col = cols[rank % num_cols]
            # get document info
            doc_url, doc = es.get_document(id=row["docid"])
            if doc is None:
                col.write("! 문서 조회되지 않음")
                continue

            col.markdown((
                f'{rank}.'
                f' [{row["grade"]}점]'
                f' [{doc["_id"]}]({get_service_doc_url("사진", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f' `{timediff(doc["created_at"][:10])}`'
                f' `avgRank:{row["avgRank"]:.1f}`'
                f' `stdevRank:{row["stdevRank"]:.1f}`'
                f' `clicks:{row["clicks"]}`'
                f' `imps:{row["impressions"]}`'
                f' `uclicks:{row["uclicks"]}`'
                f' `uimps:{row["uimpressions"]}`'
                f' `uctr:{row["uclicks"]/row["uimpressions"]:.1f}`'
                f' `mctr:{row["mctr"]:.1f}`'
            ))

            card_view.ranking_data_view(col, rank=None, doc=doc, doc_url=doc_url, row=row, use_badges=False)
    
    elif opt_order == "검색결과":
        docinfo = {str(row["docid"]):row for _, row in df.iterrows()}

        num_cols = 4
        cols = st.columns(num_cols)
        query = df["search_keyword"].unique()[0]
        res = es.get_search_result(query, top_k=200)
        for rank, item in enumerate(res["result"]["hits"]["hits"]):
            col = cols[rank % num_cols]
            # get document info
            doc_url, _ = es.get_document(id=item["_id"], only_return_url=True)
            doc = item["_source"]
            doc["_id"] = item["_id"]
            row = docinfo.get(str(doc["_id"]), {})
            col.markdown((
                f'{rank+1}.'
                # f' [{row["grade"]}점]'
                f' [{doc["_id"]}]({get_service_doc_url("사진", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f' `{timediff(doc["created_at"][:10])}`'
                f' `avgRank:{row.get("avgRank")}`'
                f' `stdevRank:{row.get("stdevRank")}`'
                f' `clicks:{row.get("clicks")}`'
                f' `imps:{row.get("impressions")}`'
                f' `uclicks:{row.get("uclicks")}`'
                f' `uimps:{row.get("uimpressions")}`'
                # f' `uctr:{row["uclicks"]/row["uimpressions"]:.1f}`'
                f' `mctr:{row.get("mctr")}`'
            ))
            if row.get("mctr", -1) > 0.05 or row.get("uclicks", -1) > 1:
                col.info(f"🚀 Clicks: {row.get('mctr')}")
            card_view.service_view(col, rank=rank+1, doc=doc, doc_url=doc_url, use_badges=False)

    if opt_order == "Custom":
        # mCTR이 높고(3, 4점) <-> mCTR이 낮고(0점) + description이 낮고
        # good = df[(df.grade == "3") & (df.grade == "2")]
        # bad = df[(df.grade == "0") & (df["f__description.bm25"] < 0.2)]
        # bad = df[(df.grade == "0")].sample(100)
        st.write(len(df), df["grade"].value_counts())
        df["grade"] = df["grade"].astype(str)
        grade_list = ["Good", "Bad"]
        num_cols = 2
        cols = st.columns(len(grade_list))
        for col, grade in zip(cols, grade_list):
            col.subheader(f"{grade}")
            if grade == "Bad":
                this_df = df[(df.grade == "0") & ( (df["f__description.bm25"] < 0.1) & (df["f__prod_categories.bm25"] < 0.05) )]
                this_df = this_df[(df["f__prod_name.proximity"] < 0.3) & (df["f__keyword_list.korean.proximity"] < 0.3)]
                print(this_df)
                this_df = this_df.sample(min(len(this_df), 100))
            else:
                # this_df = df[(df.grade == "4") | (df.grade == "3")]
                this_df = df[(df.grade == "4") | (df.grade == "3") | (df.grade == "2")]

            col.write(f"data_len: {len(this_df)}")

            for _, row in this_df.iterrows():
                # get document info
                doc_url, doc = es.get_document(id=row["docid"])
                if doc is None:
                    col.write("! 문서 조회되지 않음")
                    continue

                # get features
                features = {k.replace("f__", ""):v for k, v in row.items() if k.startswith("f__")}

                # grade 별 feature 분포
                card_view.ranking_data_view(col, rank=None, doc=doc, doc_url=doc_url, row=row)

# NOTE: 가능한 서비스 페이지와 비슷한 느낌으로 노출하여 사용자와 비슷한 경험을 느낄 수 있도록 한다.
def view_commerce(es, df):
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
def view_project(es, df):
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
def view_advice(es, df):
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
def view_question(es, df):
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

def set_options():
    col1, col2, col3, col4, col5 = st.columns(5)
    opt_order = col1.radio("Order", ["Label", "mCTR", "uCTR", "Clicks", "검색결과", "Custom"])
    opt_qc = col2.radio("QC", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])
    opt_cc = col3.radio("CC", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])
    opt_uqc = col4.radio("UQC(=NumSearchUsers)", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])
    opt_ucc = col5.radio("UCC(=NumClickUsers)", ["전체", ">=25%", ">=50%", ">=75%", ">=95%"])
    return (
        opt_order,
        opt_qc,
        opt_cc,
        opt_uqc,
        opt_ucc,
    )

def _get_quantile_option_value(data_df, value, field):
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

def get_query2data(df):
    random.seed(100)
    query2data = {}
    for query, gdf in df.groupby(["search_keyword"]):
        # 다양한 점수대로 제한 & grade별로 샘플 개수 주기
        if len(gdf.grade.unique()) < 2:
            continue
        # get samples
        # sample_size = 100
        # sample_df = pd.concat([
        #     gdf[gdf.grade ==  0].sample(min(len(gdf[gdf.grade == 0]), sample_size)),
        #     gdf[gdf.grade ==  1].sample(min(len(gdf[gdf.grade == 1]), sample_size)),
        #     gdf[gdf.grade ==  2].sample(min(len(gdf[gdf.grade == 2]), sample_size)),
        #     gdf[gdf.grade ==  3].sample(min(len(gdf[gdf.grade == 3]), sample_size)),
        #     gdf[gdf.grade ==  4].sample(min(len(gdf[gdf.grade == 4]), sample_size)),
        # ])
        sample_df = gdf
        query2data[query] = sample_df
        # query2data[query] = gdf

    # suffle query
    query2data_suffle = OrderedDict()
    keys = list(query2data.keys())
    random.shuffle(keys)
    for key in keys:
        query2data_suffle[key] = query2data[key]
    return query2data_suffle

def page(service):
    """ 클릭 정보와 함께 검색결과를 볼 수 있는 페이지 """
    opt_order, opt_qc, opt_cc, opt_uqc, opt_ucc = set_options()
    opt_data = st.selectbox(
        "SampleData",
        glob.glob(f"../dataset/{SERVICE_LIST_REV[service]}/*.{SERVICE_LIST_REV[service]}.click.ranking.*")
    )
    try:
        es, data_df = load_data_and_es(service, opt_data)
        view = load_view(service)
    except:
        st.error("해당 데이터는 지원이 안됩니다")
        return

    opt_qc = _get_quantile_option_value(data_df, opt_qc, "qc")
    opt_cc = _get_quantile_option_value(data_df, opt_cc, "cc")
    opt_uqc = _get_quantile_option_value(data_df, opt_uqc, "uqc")
    opt_ucc = _get_quantile_option_value(data_df, opt_ucc, "ucc")

    st.info(f"Your Condition: QC>={opt_qc}, CC>={opt_cc}, UQC(NumSearchUsers)>={opt_uqc}, UCC(NumClickUsers)>={opt_ucc}")

    new_data_df = data_df[
        (data_df.qc >= opt_qc ) 
        & (data_df.cc >= opt_cc) 
        & (data_df.uqc >= opt_uqc) 
        & (data_df.ucc >= opt_ucc) 
    ]

    query2data = get_query2data(new_data_df)

    if len(data_df) != len(new_data_df):
        st.info((
            f"데이터 개수: {len(data_df)}(Q:{len(data_df['search_keyword'].unique())})"
            f" -> {len(new_data_df)}(Q:{len(new_data_df['search_keyword'].unique())})"
        ))
    
    query = st.selectbox(
        "예제 질의들:",
        query2data.keys()
    )

    input_query = st.text_input(
        label="검색창:",
        placeholder="샘플질의에 있는 질의만 동작합니다. 해당 질의를 입력해주세요."
    )

    if input_query.strip():
        if input_query in query2data:
            query = input_query
            # 쿼리를 직접 입력한 경우에는 전체 질의에서 찾기 위해 다시 전체 데이터로 바꿔준다.
            query2data = get_query2data(data_df)
        else:
            st.warning(f"[{input_query}]는 샘플질의에 없습니다.")

    if query:

        st.subheader("Query Analyzer")
        res = get_analyze_result(card_dev, query, analyzers=["korean", "korean_syn"])
        st.write(res)

        df = query2data[query]

        st.subheader((
            f"Result"
            f" [QC={df.qc.unique()[0]}, CC={df.cc.unique()[0]}"
            f", CTR={100*df.cc.unique()[0]/df.qc.unique()[0]:.1f}"
            f", uQC(nSearchUsers)={df.uqc.unique()[0]}, uCC(nClickUsers)={df.ucc.unique()[0]}"
            f", uCTR={100*df.ucc.unique()[0]/df.uqc.unique()[0]:.1f}]"
        ))

        view(es, df, opt_order)
        
        #TODO: query, page 파라미터 받아서 overwrite하기