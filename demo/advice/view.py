import copy
import streamlit as st
from demo.ohs_image import get_image_url
from demo.utils import get_service_doc_url, timediff
from demo.card.utils import arrange_ranking_features
from myelasticsearch.explainer import ESExplainParser

def service_view(col, rank, doc, doc_url, use_badges=True, debug=True):
    delimiter = " <> "  # 리스트 원소 구분자
    content_max_len = 200

    with col:
        if use_badges:
            col.markdown((
                f' {rank}. '
                f' [{doc["_id"]}]({get_service_doc_url("노하우", doc["_id"])})'
                f' [`doc`]({doc_url})'
                f' `{timediff(doc["created_at"][:10])}`'
            ))
    
        # NOTE: 이미지 > 텍스트
        col.image(get_image_url(doc['cover_image_url'], width=300, height=200))
        col.write(doc["title"])
        col.write(",".join(doc["decode_category"]))
        col.write(f'조회수 {doc["view_count"]} / 스크랩 {doc["scrap_count"]}')
    
        if debug:
            # Explain 정보들
            with st.expander("Explain"):
                explained = ESExplainParser.get_general_explain(doc["_explanation"], pretty=True)
                st.text(explained)

            # 중요한 검색필드값을 보여주는 탭
            with st.expander("Document"):
                # st.write(", ".join(["#" + str(x) for x in doc["keyword_list"]]))
                st.write("[제목] " + doc["title"])
                st.write("[내용] " + doc["content"][:content_max_len] + "..." if len(doc["content"]) > content_max_len else doc["content"])
                st.write("[설명] " + doc["description"])
                # st.write("[브랜드] " + doc["brand_name"])
                # # st.write("[카테고리] " + delimiter.join(doc["prod_categories"]))
                # st.write("[클릭키워드] " + delimiter.join(doc["click_keywords"]))
                # st.write("[검색어키워드] " + delimiter.join(doc["search_keywords"].split()))
                # st.write("[관리카테고리] " + delimiter.join(doc["search_admin_categories"]))
                # st.write("[보강어] " + "" if doc["reinforcement"] is None else doc["reinforcement"])
                # st.write("[옵션] " + delimiter.join(doc["options"]))
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


def ranking_data_view(col, rank, doc, doc_url, row, use_badges=True, debug=True):
    delimiter = " <> "  # 리스트 원소 구분자
    desc_max_len = 40

    with col:
        if use_badges:
            col.markdown((
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
    
        col.image(get_image_url(doc['image_url'], width=180, aspect=1.3))
        col.write(doc["description"][:desc_max_len] + "..." if len(doc["description"]) > desc_max_len else doc["description"])
        col.write(f'👀 {doc["view_count"]} 🤍 {doc["praise_count"]} 👉🏻 {doc["scrap_count"]}')
    
        if debug:
            # Features 정보를 보여주는 탭
            with st.expander("Features"):
                features = {k:v for k, v in row.items() if k.startswith("f__") and v != 0.0}
                features = arrange_ranking_features(features)
                st.text(features)

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