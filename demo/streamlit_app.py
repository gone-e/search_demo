import sys
sys.path.append(".")
import streamlit as st
import demo.utils as utils
from demo import SERVICE_LIST, SERVICE_LIST_REV
# view page
from demo.pages import (
    analyzer,
    indices,
    feature_bm25,
    ranking_commerce,
    ranking_selling_feature,
    ranking_seller_grade,
    ranking_nlu_category_boosting,
    ranking_option_property,
    ranking_doc_expansion,
    ranking_card,
    ranking_advice,
    ranking_project,
    ranking_question,
    ranking_data,
    ranking_and_boosting,
    ranking_brand_query,
    iframe,
    doc_explain,

)


st.set_page_config(
    page_title="Ohsearch",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
    # initial_sidebar_state="collapsed",
)

def ranking_page_share(service):
    """ 서비스별 랭킹 페이지 (내외부 공유 용도) """
    if service == "스토어":
        ranking_commerce.page()
    elif service == "사진":
        ranking_card.page()
    elif service == "노하우":
        ranking_advice.page()
    elif service == "집들이":
        ranking_project.page()
    elif service == "질문과답변":
        ranking_question.page()

def app():
    """ main """
    utils.set_font_size()
    utils.set_plt_style()

    # query_params = st.experimental_get_query_params()
    # query_params

    with st.sidebar:
        # st.image("./ohouselogo.jpeg", width=150)
        page = st.radio(
            "페이지 선택",
            (
                "질의카테고리",
                "속성매칭",
                "공간/가구 부분매칭",
                "스타일링샷&쿠폰",
                "배송(conan)",
                "문서 확장",
                "랭킹 데이터",                # weak labeled ranking data result
                "형태소 분석",                # elasticsearch analyzer result
                "인덱스 정보",
                "개별문서 랭킹디버깅(Explain)",
                "[Feat] BM25 정규화",
                "iframe",
            )
        )

        service = st.radio(
            "서비스 선택",
            SERVICE_LIST.values()
        )
        st.write("\n")
        st.info("💡 검색창에 텍스트가 입력된 경우에는 예제 질의가 동작하지 않습니다.")

    if page == "스타일링샷&쿠폰":
        ranking_seller_grade.page()
    elif page == "배송(conan)":
        ranking_brand_query.page()
    elif page == "랭킹 데이터":
        ranking_data.page(service)
    elif page == "속성매칭":
        ranking_option_property.page()
    elif page == "공간/가구 부분매칭":
        ranking_and_boosting.page()
    elif page == "질의카테고리":
        ranking_nlu_category_boosting.page()
    elif page == "문서 확장":
        ranking_doc_expansion.page()
    elif page == "형태소 분석":
        analyzer.page(service)
    elif page == "인덱스 정보":
        indices.page()
    elif page == "[Feat] BM25 정규화":
        feature_bm25.page()
    elif page == "iframe":
        iframe.page()
    elif page == "개별문서 랭킹디버깅(Explain)":
        doc_explain.page(service)
        

if __name__ == "__main__":
    app()
