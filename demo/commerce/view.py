import copy
import streamlit as st
from demo.ohs_image import get_image_url
from demo.utils import get_service_doc_url, timediff
from demo.card.utils import arrange_ranking_features
from myelasticsearch.explainer import ESExplainParser
from services import commerce_dev

def service_view(col, rank, doc, doc_url, use_badges=True, debug=True):
    delimiter = " <> "  # 리스트 원소 구분자
    desc_max_len = 40

    def get_delivery_method(method, delivery_score):
        if delivery_score>0.01:
            return "오늘출발"
        if method==4:
            return "빠른가전배송"
        elif method==3:
            return "오늘의집배송"
        elif method==2:
            return "화물배송"
        elif method==1:
            return "직접배송"
        else:
            return "택배"

    with col:
        if use_badges:
            col.markdown((
                f' {rank}. '
                f' [{doc["_id"]}]({get_service_doc_url("스토어", doc["_id"])})'
                f' [`doc`]({doc_url})'
                # f' `{timediff(doc["created_at"][:10])}`'
            ))
    
        # col.image(get_image_url(doc['image_url'], width=180, aspect=1.3))
        # col.write(doc["description"][:desc_max_len] + "..." if len(doc["description"]) > desc_max_len else doc["description"])
        # col.write(f'👀 {doc["view_count"]} 🤍 {doc["praise_count"]} 👉🏻 {doc["scrap_count"]}')
        # TODO: 이미지 > 할인율(discount_rate), 가격 > 평점, 리뷰(스크랩) > 태그들:[무료배송][특가]
        col.image(get_image_url(doc['image_url'], width=180, aspect=1.3))

        col.write(doc["name"])
        if doc["name"] != doc["search_name"]:
            col.write(f"> 검색: {doc['search_name']}")
        if debug:
            # TODO: 속도가 느려서 잠시 제외
            # col.write(" | ".join(
            #         [x["token"] for x in commerce_dev.get_analyze_result(doc["name"], analyzers=["korean"])["korean"]["tokens"]]))
            # if doc["name"] != doc["search_name"]:
            #     col.write(f'> 검색: {" | ".join([x["token"] for x in commerce_dev.get_analyze_result(doc["search_name"], analyzers=["korean"])["korean"]["tokens"]])}')
            col.write(f"[브랜드] {doc['brand_name']}")
            col.write(f"[관리카테고리(검색용)] {doc['search_admin_categories']}")
            col.write(f"[카테고리키워드] {doc['category_keywords']}")
        has_content_keyword = True if doc.get("content_keywords") else False
        col.write("[컨텐츠키워드] " + str(has_content_keyword))
        col.write(f"[배송] { get_delivery_method(doc['delivery_method'], doc['delivery_score'])}")
        col.write(f"[스타일링샷] { doc['card_count']}")
        col.write(f"[쿠폰] {'있음' if doc['has_coupon']==1 else '없음'}")
        col.write(f"{doc['discount_rate']}% / {doc['selling_cost']}")
        col.write(f"⭐️ {doc['review_avg']} / 리뷰 {doc['review_count']}")
        if doc["is_free_delivery"]:
            col.write(f"`무료배송`")
    
        if debug:
            # Explain 정보들
            with st.expander("Explain"):
                explained = ESExplainParser.get_general_explain(doc["_explanation"], pretty=True)
                st.text(explained)

            # 중요한 검색필드값을 보여주는 탭
            with st.expander("Document"):
                if doc["search_keywords"] is None: doc["search_keywords"] = ""
                if doc["reinforcement"] is None: doc["reinforcement"] = []
                if doc["negatives"] is None: doc["negatives"] = []
                # st.write(", ".join(["#" + str(x) for x in doc["keyword_list"]]))
                st.write("[상품명] " + doc["name"])
                # st.write("[상품명(형태소)] " + " | ".join(
                #     [x["token"] for x in commerce_dev.get_analyze_result(doc["name"], analyzers=["korean"])["korean"]["tokens"]]))
                st.write("[브랜드] " + doc["brand_name"])
                # st.write("[브랜드(형태소)] " + " | ".join(
                #     [x["token"] for x in commerce_dev.get_analyze_result(doc["brand_name"], analyzers=["korean"])["korean"]["tokens"]]))
                # st.write("[카테고리] " + delimiter.join(doc["prod_categories"]))
                st.write("[컨텐츠키워드] " + delimiter.join(doc["content_keywords"]))
                st.write("[클릭키워드] " + delimiter.join(doc["click_keywords"]))
                st.write("[검색키워드(MD/Seller)] " + delimiter.join(doc["search_keywords"]))
                st.write("[관리카테고리] " + delimiter.join(doc["admin_categories"]))
                st.write("[관리카테고리(검색용)] " + delimiter.join(doc["search_admin_categories"]))
                st.write("[카테고리키워드] " + delimiter.join(doc["category_keywords"]))
                st.write("[보강어] " + delimiter.join(doc["reinforcement"]))
                st.write("[불용어] " + delimiter.join(doc["negatives"]))
                st.write("[옵션] " + delimiter.join(doc["options"]))
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
                        doc_copy[k] = round(v, 4)
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
                        doc_copy[k] = round(v, 4)
                st.json(doc_copy)
