import json
import datetime
import streamlit as st
from myelasticsearch.analyzer_parser import AnalyzerParser
import requests


def set_font_size():
    st.markdown("""
    <style>
    .small-font {
        font-size: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)


def set_plt_style():
    import matplotlib.pyplot as plt
    from matplotlib import style
    # style.use('dark_background')
    # style.use("seaborn-darkgrid")
    style.use("ggplot")
    plt.rcParams["figure.figsize"] = (8, 2)
    plt.rcParams["lines.linewidth"] = 2
    plt.rcParams["axes.grid"] = True
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams['axes.unicode_minus'] = False


def list_to_str(mylist, delimiter="</br>"):
    return delimiter.join(mylist)


def convert_service_code_to_explainable(code):
    return


def get_docs(es_result):
    try:
        items = es_result["result"]["hits"]["hits"]
    except:
        st.error(f"[ERROR] Request failed: es_result is {es_result}")
        print(f"[ERROR] Request failed: es_result is {es_result}")
        return

    docs = []
    for rank, item in enumerate(items):
        doc = item["_source"]
        doc["_id"] = item["_id"]
        # doc["_score"] = round(item["_score"], 2)
        doc["_score"] = item["_score"]
        if "_explanation" in item:
            doc["_explanation"] = item["_explanation"]
        docs.append(doc)
    return docs


def get_id2rank(docs):
    id2rank = {}
    for rank, doc in enumerate(docs):
        id2rank[doc["_id"]] = rank + 1
    return id2rank


def get_rank_changes(asis_id2rank, tobe_id2rank, id, top_k):
    if len(tobe_id2rank) == 0:
        return ""

    asis_rank = asis_id2rank.get(id, top_k + 1)
    tobe_rank = tobe_id2rank.get(id, top_k + 1)
    change = asis_rank - tobe_rank
    # TODO: top_k에 없는 경우 + 추가 (예: 300+)
    if change == 0:
        mdtext = ""
    elif change > 0:
        mdtext = f"⬆️ {change}"
    elif change < 0:
        mdtext = f'⬇️ {str(change).replace("-", "")}'
    return f"**`{mdtext}`**" if mdtext else ""


def get_analyze_result(es_wrapper, query, analyzers=None, detail=False, with_json=False):
    category_id_name_map = {
         1007000: "수납가구",
         1121000: '주방가전',
         1102000: '계절가전',
         1013000: '주방가구',
         1117000: '냉장고',
         1006000: '소파',
         1014000: '침대',
         1012000: '의자',
         1707000: '홈패브릭/커버',
         1009000: '오피스/서재가구',
         1705000: '커튼/블라인드',
         1120000: 'TV',
         1119000: '영상가전',
         1108000: '이미용가전',
         1111000: '청소기',
         1118000: '세탁기/건조기',
         1017000: '화장대/콘솔',
         1706000: '쿠션/방석',
         1005000: '병풍/파티션',
         1105000: '생활가전',
         1010000: '옷장/드레스룸',
         1701000: '러그/카페트/매트',
         1002000: '거울',
         1704000: '침구',
         1016000: '행거',
         1004000: '매트리스(150T이상)',
         1015000: '토퍼'
    }

    analyzer_result = es_wrapper.get_analyze_result(query, analyzers=analyzers)
    parsed_result = {}
    for analyzer, res in analyzer_result.items():
        parsed_result[analyzer] = AnalyzerParser.aggregate_by_offset(res)
    if with_json:
        return parsed_result, analyzer_result

    def check_query_term_type(analyzed_result):
        result = []
        brand_keyword = None
        query_category = None
        if analyzed_result.get("category"):
            query_category = analyzed_result.get("category")

        if len(analyzed_result['result']) > 0:
            for token in analyzed_result['result']:
                if token['slot_type'] == "브랜드명":
                    brand_keyword = token['slot_text']
                result.append(token['slot_text'] + "/" + token['slot_type'])
            return " ".join(result), brand_keyword, query_category
        return False, brand_keyword, query_category

    query_analyzed_result = requests.get(
        f"http://localhost:8000/analysis/collections/commerce?query={query}&v=v2").json()
    query_term_type, brand_keyword, query_category = check_query_term_type(query_analyzed_result)
    parsed_result['query_term_analyze'] = query_term_type
    parsed_result['brand_keyword'] = brand_keyword
    parsed_result['query_category'] = f"{query_category} / {category_id_name_map[query_category]}"
    parsed_result['nlu'] = f"https://search-nlu.datahou.se/analysis/?query={query}"
    return parsed_result


def get_service_doc_url(service, id):
    if service == "스토어":
        return f"https://ohou.se/productions/{id}"
    elif service == "사진":
        return f"https://ohou.se/cards/{id}"
    elif service == "노하우":
        return f"https://ohou.se/advices/{id}"
    elif service == "집들이":
        return f"https://ohou.se/projects/{id}"
    elif service == "질문과답변":
        return f"https://ohou.se/questions/{id}"


def timediff(created_at, format="%Y-%m-%d"):
    created_at = datetime.datetime.strptime(created_at, format)
    return f"-{(datetime.datetime.today() - created_at).days} days"
