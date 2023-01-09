#-*-coding:utf-8-*-
import re
import enum
import os
import copy
from random import sample
import sys
import json
from collections import OrderedDict
from elasticsearch_dsl import analyzer
import requests
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
# style.use('dark_background')
# style.use('seaborn-darkgrid')
style.use('ggplot')
plt.rcParams["figure.figsize"] = (8,2)
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['axes.grid'] = True 

sys.path.append('../../')
from card_searcher import CardSearcher
from ranking.card import *
import demo.utils as utils
import demo.codes as codes
from . import common_utils
from myutils.json_parser import JsonParser
from demo.ohs_image import get_image_url

card_searcher = CardSearcher()
json_parser = JsonParser()

DEFAULT_QUERY = '러그'
TOP_K = 500

st.set_page_config(
    page_title="RankingApp",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    # initial_sidebar_state="collapsed",
    # Configure the menu that appears on the top-right side of this app
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

DEBUG_FIELDS = {
    'id': '사진ID',
    'description': '사진설명',
    'place': '공간정보',
    'style': '사진스타일',
    'keyword_list': '키워드들??',
    'view_count': '조회수',
    'scrap_count': '스크랩수',
}

@st.cache
def _read_debug_query(data='../../dataset/card/query.debug.jsonl'):
    sample_queries = {}
    with open(data, 'r') as f:
        for _, line in enumerate(f):
            data = json.loads(line)
            sample_queries[data['query']] = {k:v for k, v in data.items() if k != 'query'}
    return sample_queries

def convert_es_result_to_dataframe(es_result):
    try:
        items = es_result['hits']['hits']
    except:
        print(f'[ERROR] Request failed: es_result is {es_result}')
        return
    new_items = []
    for rank, item in enumerate(items):
        doc = item["_source"]
        debug_data = OrderedDict()
        debug_data['rank'] = rank + 1
        debug_data['image'] = f'<img src="{doc["image_url"]}" width=100></br><a target="_blank" href="http://ohou.se/cards/{doc["id"]}">Page</a>'
        debug_data['score'] = item['_score']
            # if field == 'id':
            #     value = f'<a target="_blank" href="http://ohou.se/cards/{doc["id"]}">Page</a>'
            #     # debug_data['id'] = f'<a target="_blank" href="http://ohou.se/cards/{debug_data["id"]}">{debug_data["id"]}</a>'
            #     # debug_data['id'] = f'[{debug_data["id"]}](http://ohou.se/cards/{debug_data["id"]})'

        # convert categorical variable to explainable text

        exclude_fields = ['id', 'nickname', 'userable_type', 'created_at', 'type']
        space_fields = ['decode_area', 'decode_style', 'decode_residence', 'color', 'style', 'area', 'residence']
        other_text_fields = ['company', 'reinforcement', 'negatives', 'video_duration']
        other_text_list = []
        space_list = []
        numeric_list = []
        for field, value in item['_source'].items():
            if 'url' in field:
                continue
            elif field in exclude_fields:
                continue
            elif field in space_fields:
                space_list.append(f'{field}={value}')
                continue
            elif field in other_text_fields:
                other_text_list.append(f'{field}={value}')
                continue
            elif isinstance(value, list):
                value = utils.list_to_str(value)
            elif isinstance(value, int):
                numeric_list.append(f'{field}={value}')
                continue
            elif isinstance(value, float):
                numeric_list.append(f'{field}={value:.2f}')
                continue

            debug_data[field] = value
        
        # add numeric score
        debug_data['numeric'] = utils.list_to_str(numeric_list)
        debug_data['텍스트'] = utils.list_to_str(other_text_list)
        debug_data['공간정보'] = utils.list_to_str(space_list)

        new_items.append(debug_data)

    # return pd.DataFrame(new_items).round(2).to_html(escape=False, index=False)
    return pd.DataFrame(new_items).round(2).to_html(escape=False, index=False).replace('table', 'table class="small-font"')
    # tobe_data.rename(columns={'image_url': 'image_url2', 'id': 'id2'}, inplace=True)

def get_image_from_es_result(es_result):
    try:
        items = es_result['hits']['hits']
    except:
        print(f'[ERROR] Request failed: es_result is {es_result}')
        return
    images = []
    docs = []
    for rank, item in enumerate(items):
        doc = item['_source']
        doc['_score'] = round(item['_score'], 2)
        if '_explanation' in item:
            doc['_explanation'] = item['_explanation']
        images.append(get_image_url(doc['image_url'], width=180))
        docs.append(doc)
    return images, docs
    
def decode_code(field, value):
    if field == 'decode_area':
        return codes.decode_user_area(value)
    elif field == 'decode_style':
        return codes.decode_card_style(value)
    elif field == 'decode_residence':
        return codes.decode_card_residence(value)
    return value

def compress_doc(doc):
    """ extract necessary fields for debugging """
    exclude_fields = ['id', 'userable_type', 'created_at', 'type']
    space_fields = ['decode_area', 'decode_style', 'decode_residence', 'color', 'style', 'area', 'residence']
    other_text_fields = ['company', 'reinforcement', 'negatives', 'video_duration']
    new_doc = {}
    for k, v in doc.items():
        if k in exclude_fields:
            continue
        if 'url' in k:
            continue
        if v is None:
            continue
        if k == '_explanation':
            continue
        # code number to text
        v = decode_code(k, v)
        # make shorten
        if isinstance(v, list):
            v = utils.list_to_str(v, delimiter="[::]")
        elif isinstance(v, float):
            v = round(v, 2)

        new_doc[k] = v

    return new_doc

def case_page():
    # TODO: 현재는 여러 개의 selectbox를 만들어서 widget을 on_change 같은 콜백함수로 제어하기가 너무 어렵다.
    query = st.selectbox(
            'Bad Cases',
            ('멀티탭 커버', '수도꼭지', '단스탠드 조명'),
        )
    if query:
        st.subheader(f"Result[{card_searcher.ENV}]")
        st.write(f"Query: {query}")
        res = card_searcher.get_asis_search_results(query)
        res

# def ranking_page_debug():
#     """ st.image는 그리드 시스템을 지원하지 않기 때문에 디버깅 정보를 붙이기가 어렵고,
#     높이가 달라서 한눈에 보기 어렵다. 따라서 테이블 형태로 보여준다. """
#     query = st.text_input(
#         label="Search",
#         value=DEFAULT_QUERY
#     )

#     if query:

#         res = card_searcher.get_asis_search_results(query)
#         res2 = copy.deepcopy(res)

#         st.subheader("Result")

#         # col1, col2, col3, col4 = st.columns([1, 8, 1, 8])
#         col1, col2 = st.columns(2)
#         with col1:
#             col1.write(convert_es_result_to_dataframe(res), unsafe_allow_html=True)

def draw_dist(data_list, writer=None, xlabel=None, ylabel=None):
    plt.figure(figsize=(14, 2))
    plt.xticks(range(1, len(data_list)+1))
    plt.plot(range(1, len(data_list)+1), data_list)
    if xlabel is not None: 
        plt.xlabel(xlabel)
    if ylabel is not None: 
        plt.ylabel(ylabel)
    if writer is not None:
        writer.pyplot(plt)
    else:
        st.pyplot(plt)

def parse_explain_(explain):
    # TODO: 일반화
    explained = ''
    desc = explain['description']
    details = explain['details']
    explained += f'[{desc}]'
    for i, detail in enumerate(details):
        desc = detail['description']
        value = detail['value']
        explained += f'\n[{desc}] {value}'
    return explained
    
def parse_explain(explain):
    json_parser.set_json_obj(explain)
    flatted_json = json_parser.traverse()
    # print(json.dumps(flatted_json, indent=2))
    explained = ''
    prev_path = None
    prev_value = None
    # yes = False
    for path, value in flatted_json.items():
        # description
        # if 'weight(description:흙 in 129428)' in str(value):
        #     yes = True
        if 'weight(' in str(value):
            if prev_path is not None:
                explained += f'\n\t{prev_value:.2f} <- '
            explained += f'{value}'
        prev_path = path
        prev_value = value
    # if yes:
    #     print(explained)
    return explained

def _temp(anal):
    # 예: 음식물쓰레기
    # TODO: synonym data 받아보기 -> 음쓰여야 할것 겉은데?
    # {'tokens': [{'token': '음', 'start_offset': 0, 'end_offset': 6, 'type': 'SYNONYM', 'position': 0}, {'token': '음식물', 'start_offset': 0, 'end_offset': 3, 'type': 'word', 'position': 0, 'positionLength': 2}, {'token': '쓰', 'start_offset': 0, 'end_offset': 6, 'type': 'SYNONYM', 'position': 1, 'positionLength': 2}, {'token': '쓰레기', 'start_offset': 3, 'end_offset': 6, 'type': 'word', 'position': 2}]}
    # {'tokens': [{'token': '음식물쓰레기', 'start_offset': 0, 'end_offset': 6, 'type': 'word', 'position': 0, 'positionLength': 2}, {'token': '음식물', 'start_offset': 0, 'end_offset': 3, 'type': 'word', 'position': 0}, {'token': '쓰레기', 'start_offset': 3, 'end_offset': 6, 'type': 'word', 'position': 1}]}
    # {'tokens': [{'token': '음식물쓰레기', 'start_offset': 0, 'end_offset': 6, 'type': 'word', 'position': 0}]}
    position2term = OrderedDict()
    for x in anal['tokens']:
        if x['position'] not in position2term:
            position2term[x['position']] = []
        if x['type'] == 'word':
            position2term[x['position']].append(x['token'])
        else:
            position2term[x['position']].append(f"({x['token']}|{x['type']})")
    # return ', '.join([''.join(v) for k, v in position2term.items()])
    return ', '.join(['[::]'.join(v) for k, v in position2term.items()])

def _exclude_1term(df):
    writer = open('../../dataset/card_search/card.uniq.query.rs.no1term.20220321.20220327.csv', 'w+')
    new_df = []
    writer.write(','.join(['search_keyword', 'qc', 'cc', 'ctr']) + '\n')
    for idx, row in df.iterrows():
        analyzers = ['korean_syn']
        analyzers_result = card_searcher.get_query_analyze_result(row['search_keyword'], analyzers=analyzers)
        tokens = analyzers_result['korean_syn']['tokens']
        if len(set([x['position'] for x in tokens])) == 1:
            continue
        print(','.join(str(x) for x in row.values))
        writer.write(','.join(str(x) for x in row.values) + '\n')
        new_df.append(row)
    return pd.DataFrame(new_df)

def _query_analyzed_result(query):
    analyzers = ['korean_syn', 'korean', 'keyword_case_insensitive']
    analyzers_result = card_searcher.get_query_analyze_result(query, analyzers=analyzers)
    query_cols = st.columns(3)
    # TODO: position 동일 시 합치기
    is_1term = False
    for i, (name, anal) in enumerate(analyzers_result.items()):
        # query_anal = ' '.join([f"{x['token']}/{x['type']}" for x in anal['tokens']])
        # query_cols[i].write(f'[{name}] {query_anal}')
        if name == 'korean_syn' and len(set([x['position'] for x in anal['tokens']])) == 1:
            print(set([x['position'] for x in anal['tokens']]))
            is_1term = True
        query_cols[i].write(f'[{name}] ' + ' '.join([f'"{x["token"]}/{x["type"]}/{x["position"]}"' for x in anal['tokens']]))
        # query_cols[i].write(f'[{name}] {_temp(anal)}')
    return is_1term

def get_id2rank(docs):
    id2rank = {}
    for rank, doc in enumerate(docs):
        id2rank[doc['id']] = rank
    return id2rank

def compare_rank(base, rank):
    if base is None or rank is None:
        return 'same'
    return base - rank
    
def ranking_page_debug():
    # query = st.text_input(
    #     label="Search",
    #     value=DEFAULT_QUERY
    # )
    sample_queries = _read_debug_query()

    query = st.selectbox(
        'Search',
        sample_queries.keys()
    )

    input_query = st.text_input(
        label="Search",
        placeholder='검색어를 입력해주세요.'
    )

    if input_query.strip():
        query = input_query

    if query:
        # -- Request
        # asis = card_searcher.get_asis_search_results(query, explain=True, top_k=TOP_K)
        asis = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase_rescore.generate(query, top_k=TOP_K), explain=True)
        asis_images, asis_docs = get_image_from_es_result(asis)
        # print(json.dumps(asis['hits']['hits'][0]['_explanation'], indent=2))

        # asis = card_searcher.get_search_results(query, request_body=asis_proximity.generate(query), explain=True)
        # asis_images, asis_docs = get_image_from_es_result(asis)

        with st.expander('Search Results (Json)'):
            st.json(asis)

        # -- 부가정보
        # st.write(json.dumps(debug_info['id2rank']))
        # st.subheader(f'Result [QC={debug_info["qc"]}, CC={debug_info["cc"]}]')
        debug_info = sample_queries.get(query)
        # Debug Info
        if debug_info is not None:
            st.subheader(f'Result [QC={debug_info["qc"]}, CC={debug_info["cc"]}]')
        else:
            st.subheader(f'Result')

        plot_cols = st.columns(2)
        if debug_info is not None:
            draw_dist(debug_info['click_dist'], writer=plot_cols[0], xlabel='Rank', ylabel='Click Count')
        score_list = [doc['_score'] for doc in asis_docs]
        draw_dist(score_list, writer=plot_cols[1], xlabel='(This) Rank', ylabel='Score')
            
        # 쿼리 분석 결과
        _query_analyzed_result(query)

        # -- layout
        col_size = 3
        cols = st.columns(col_size)

        for idx, (img, doc) in enumerate(zip(asis_images, asis_docs)):
            doc["id"] = str(doc["id"])
            col = cols[idx % col_size]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]}](https://ohou.se/cards/{doc["id"]})')
                # col.error(col.write(f'<a href="https://ohou.se/cards/{doc["id"]}">Go To Page</a>', unsafe_allow_html=True))
                # if doc["id"] in debug_info["low_quality_ids"]:
                #     col.error('저품질 가능성❗️')
                explained = parse_explain_(doc['_explanation'])
                explained += parse_explain(doc['_explanation'])
                col.text(explained)
                if debug_info is not None:
                    if doc["id"] not in debug_info["id2rank"]:
                        col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                    else:
                        col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

def ranking_page_debug_compare():
    sample_queries = _read_debug_query()

    query = st.selectbox(
        'Search',
        sample_queries.keys()
    )

    input_query = st.text_input(
        label="Search",
        placeholder='검색어를 입력해주세요.'
    )

    if input_query.strip():
        query = input_query

    if query:

        # TODO: Rank 변동폭 붙여주기
        asis = card_searcher.get_asis_search_results(query, explain=True, top_k=TOP_K)
        asis_images, asis_docs = get_image_from_es_result(asis)
        # tobe = card_searcher.get_search_results(query, request_body=asis_proximity_shingle.generate(query, top_k=TOP_K), explain=True)
        # tobe = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase.generate(query, top_k=TOP_K), explain=True)
        tobe = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase_rescore.generate(query, top_k=TOP_K), explain=True)
        tobe_images, tobe_docs = get_image_from_es_result(tobe)

        # -- 부가정보
        # st.write(json.dumps(debug_info['id2rank']))
        # st.subheader(f'Result [QC={debug_info["qc"]}, CC={debug_info["cc"]}]')
        debug_info = sample_queries.get(query)
        # Debug Info
        if debug_info is not None:
            st.subheader(f'Result [QC={debug_info["qc"]}, CC={debug_info["cc"]}]')
        else:
            st.subheader(f'Result')

        plot_cols = st.columns(2)
        if debug_info is not None:
            draw_dist(debug_info['click_dist'], writer=plot_cols[0], xlabel='Rank', ylabel='Click Count')
        score_list = [doc['_score'] for doc in asis_docs]
        draw_dist(score_list, writer=plot_cols[1], xlabel='(This) Rank', ylabel='Score')

        # 쿼리 분석 결과
        _query_analyzed_result(query)

        # column layout
        num_cols = 5    # 홀수로 변경: 5 또는 7 권장
        mid = int((num_cols-1)/2)
        col_size_list = [1]*num_cols
        col_size_list[mid] *= 0.2   # this is border
        cols = st.columns(col_size_list)
        base_cols = cols[:mid]
        comp_cols = cols[mid+1:]

        for idx, (img, doc) in enumerate(zip(asis_images, asis_docs)):
            col = base_cols[idx % mid]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]}](https://ohou.se/cards/{doc["id"]})')
                explained = f"{doc['_score']:.2f}"
                explained += parse_explain_(doc['_explanation'])
                explained += parse_explain(doc['_explanation'])
                col.text(explained)
                if debug_info is not None:
                    if doc["id"] not in debug_info["id2rank"]:
                        col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                    else:
                        col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

        for idx, (img, doc) in enumerate(zip(tobe_images, tobe_docs)):
            col = comp_cols[idx % mid]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]}](https://ohou.se/cards/{doc["id"]})')
                explained = f"{doc['_score']:.2f}\n"
                explained += parse_explain_(doc['_explanation'])
                explained += parse_explain(doc['_explanation'])
                col.text(explained)
                if debug_info is not None:
                    if doc["id"] not in debug_info["id2rank"]:
                        col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                    else:
                        col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

def ranking_page():
    # sample_queries = _read_debug_query()
    # df = pd.read_csv('../../dataset/card_search/card.uniq.query.rs100.20220301.intent.csv')
    df = pd.read_csv('../../dataset/card_search/card.uniq.query.rs.no1term.20220321.20220327.csv')
    # df = _exclude_1term(df)

    sample_queries = {}
    for _, row in df.iterrows():
        # sample_queries[row['search_keyword']] = {'qc': int(row['qc'])}
        sample_queries[row['search_keyword']] = {'qc': row['qc'], 'cc': row.get('cc'), 'ctr': row.get('ctr')}

    # temporary
    sample_queries = {}
    with open('../../diff/card_search/diff.asis.proximity_rescore_max.change.txt') as f:
        for i, line in enumerate(f):
            query = line.split('\t')[0]
            sample_queries[query] = {}

    query = st.selectbox(
        'Search',
        sample_queries.keys()
    )

    input_query = st.text_input(
        label="Search",
        placeholder='검색어를 입력해주세요.'
    )

    if input_query.strip():
        query = input_query

    if query:

        # TODO: Rank 변동폭 붙여주기
        asis = card_searcher.get_asis_search_results(query, explain=True, top_k=300)
        asis_images, asis_docs = get_image_from_es_result(asis)
        # tobe = card_searcher.get_search_results(query, request_body=asis_proximity_shingle.generate(query, top_k=TOP_K), explain=True)
        # tobe = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase.generate(query, top_k=TOP_K), explain=True)
        tobe = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase_rescore.generate(query, top_k=TOP_K), explain=True)
        tobe_images, tobe_docs = get_image_from_es_result(tobe)

        tobe2 = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase_rescore_max.generate(query, top_k=TOP_K), explain=True)
        tobe2_images, tobe2_docs = get_image_from_es_result(tobe2)

        asis_id2rank = get_id2rank(asis_docs)
        tobe_id2rank = get_id2rank(tobe_docs)
        tobe2_id2rank = get_id2rank(tobe2_docs)

        # -- 부가정보
        # st.write(json.dumps(debug_info['id2rank']))
        # st.subheader(f'Result [QC={debug_info["qc"]}, CC={debug_info["cc"]}]')
        debug_info = sample_queries.get(query)
        # Debug Info
        if debug_info is not None:
            st.subheader(f'Result [QC={debug_info.get("qc")}, CC={debug_info.get("cc")}]')
        else:
            st.subheader(f'Result')

        # plot_cols = st.columns(2)
        plot_cols = st.columns(3)
        plot_cols[0].subheader('AS-IS')
        plot_cols[1].subheader('TO-BE-1')
        plot_cols[2].subheader('TO-BE-2')
        # if debug_info is not None:
        #     draw_dist(debug_info['click_dist'], writer=plot_cols[0], xlabel='Rank', ylabel='Click Count')
        score_list = [doc['_score'] for doc in asis_docs]
        draw_dist(score_list, writer=plot_cols[0], xlabel='(This) Rank', ylabel='Score')
        score_list = [doc['_score'] for doc in tobe_docs]
        draw_dist(score_list, writer=plot_cols[1], xlabel='(This) Rank', ylabel='Score')
        score_list = [doc['_score'] for doc in tobe2_docs]
        draw_dist(score_list, writer=plot_cols[2], xlabel='(This) Rank', ylabel='Score')

        # 쿼리 분석 결과
        _query_analyzed_result(query)

        # column layout
        num_cols = 7    # 홀수로 변경: 5 또는 7 권장
        mid = int((num_cols-1)/2)
        col_size_list = [1]*num_cols
        col_size_list[mid] *= 0.2   # this is border
        cols = st.columns(col_size_list)
        base_cols = cols[:mid]
        comp_cols = cols[mid+1:]

        cols = st.columns([1,1,0.2,1,1,0.2,1,1])
        mid = 2
        base_cols = cols[:2]
        comp_cols = cols[3:5]
        comp2_cols = cols[6:]

        for idx, (img, doc) in enumerate(zip(asis_images, asis_docs)):
            col = base_cols[idx % mid]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]}](https://ohou.se/cards/{doc["id"]})')
                with st.expander('Explain'):
                    explained = f"{doc['_score']:.2f}\n"
                    explained += parse_explain_(doc['_explanation'])
                    explained += parse_explain(doc['_explanation'])
                    st.text(explained)
                # if debug_info is not None:
                #     if doc["id"] not in debug_info["id2rank"]:
                #         col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                #     else:
                #         col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

        for idx, (img, doc) in enumerate(zip(tobe_images, tobe_docs)):
            col = comp_cols[idx % mid]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]}](https://ohou.se/cards/{doc["id"]})')

                rank = compare_rank(asis_id2rank.get(doc['id']), tobe_id2rank.get(doc['id']))
                if rank == 'same' or rank == 0:
                    pass
                elif rank > 0:
                    col.success(f'Rank 변동: +{rank}')
                else:
                    col.error(f'Rank 변동: {rank}')
                    
                with st.expander('Explain'):
                    explained = f"{doc['_score']:.2f}\n"
                    explained += parse_explain_(doc['_explanation'])
                    explained += parse_explain(doc['_explanation'])
                    st.text(explained)
                # if debug_info is not None:
                #     if doc["id"] not in debug_info["id2rank"]:
                #         col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                #     else:
                #         col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

        for idx, (img, doc) in enumerate(zip(tobe2_images, tobe2_docs)):
            col = comp2_cols[idx % mid]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]}](https://ohou.se/cards/{doc["id"]})')

                rank = compare_rank(asis_id2rank.get(doc['id']), tobe2_id2rank.get(doc['id']))
                # if doc['id'] == '12369894':
                #     print(rank)
                #     print(asis_id2rank.get(doc['id']))
                #     print(tobe2_id2rank.get(doc['id']))
                if rank == 'same' or rank == 0:
                    pass
                elif rank > 0:
                    col.success(f'Rank 변동: +{rank}')
                else:
                    col.error(f'Rank 변동: {rank}')

                with st.expander('Explain'):
                    explained = f"{doc['_score']:.2f}\n"
                    explained += parse_explain_(doc['_explanation'])
                    explained += parse_explain(doc['_explanation'])
                    st.text(explained)
                # if debug_info is not None:
                #     if doc["id"] not in debug_info["id2rank"]:
                #         col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                #     else:
                #         col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

def ranking_page_share():
    # sample_queries = _read_debug_query()
    st.info('💡 검색창에 텍스트가 입력된 경우에는 예제 질의가 동작하지 않습니다.')
    # st.info('💡 형태소 분석 후 토큰 개수가 1개인 경우는 제외하고 봐주세요')

    # df = pd.read_csv('../../dataset/card_search/card.uniq.query.rs100.20220301.intent.csv')
    df = pd.read_csv('../../dataset/card/card.uniq.query.rs.no1term.20220321.20220327.csv')

    sample_queries = {}
    for _, row in df.iterrows():
        sample_queries[row['search_keyword']] = {'qc': row['qc'], 'cc': row.get('cc'), 'ctr': row.get('ctr')}

    # temporary
    sample_queries = {}
    with open('../../diff/card/diff.asis.proximity_rescore_max.change.txt') as f:
        for i, line in enumerate(f):
            query = line.split('\t')[0]
            sample_queries[query] = {}

    query = st.selectbox(
        'Search',
        sample_queries.keys()
    )

    input_query = st.text_input(
        label="Search",
        placeholder='검색어를 입력해주세요.'
    )

    if input_query.strip():
        query = input_query

    if query:

        # 쿼리 분석 결과
        is_1term = _query_analyzed_result(query)
        # if is_1term:
        #     st.warning('1term')

        # TODO: Rank 변동폭 붙여주기
        asis = card_searcher.get_asis_search_results(query, explain=True, top_k=300)
        asis_images, asis_docs = get_image_from_es_result(asis)

        # tobe = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase_rescore.generate(query, top_k=TOP_K), explain=True)
        tobe = card_searcher.get_search_results(query, request_body=asis_proximity_match_phrase_rescore_max.generate(query, top_k=TOP_K), explain=True)
        # print(json.dumps(tobe["hits"]["hits"][0], indent=2, ensure_ascii=False))
        # print(tobe)
        # print(tobe["hits"]["hits"][0])
        tobe_images, tobe_docs = get_image_from_es_result(tobe)

        asis_id2rank = get_id2rank(asis_docs)
        tobe_id2rank = get_id2rank(tobe_docs)

        # -- 부가정보
        # st.write(json.dumps(debug_info['id2rank']))
        # st.subheader(f'Result [QC={debug_info["qc"]}, CC={debug_info["cc"]}]')
        debug_info = sample_queries.get(query)
        # Debug Info
        if debug_info is not None:
            st.subheader(f'Result [QC={debug_info.get("qc")}, CC={debug_info.get("cc")}]')
        else:
            st.subheader(f'Result')

        plot_cols = st.columns(2)
        plot_cols[0].subheader('AS-IS')
        plot_cols[1].subheader('TO-BE')
        # if debug_info is not None:
        #     draw_dist(debug_info['click_dist'], writer=plot_cols[0], xlabel='Rank', ylabel='Click Count')
        score_list = [doc['_score'] for doc in asis_docs]
        draw_dist(score_list, writer=plot_cols[0], xlabel='(This) Rank', ylabel='Score')
        score_list = [doc['_score'] for doc in tobe_docs]
        draw_dist(score_list, writer=plot_cols[1], xlabel='(This) Rank', ylabel='Score')

        # column layout
        num_cols = 5    # 홀수로 변경: 5 또는 7 권장
        mid = int((num_cols-1)/2)
        col_size_list = [1]*num_cols
        col_size_list[mid] *= 0.2   # this is border
        cols = st.columns(col_size_list)
        base_cols = cols[:mid]
        comp_cols = cols[mid+1:]

        for idx, (img, doc) in enumerate(zip(asis_images, asis_docs)):
            col = base_cols[idx % mid]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]} ({doc["_score"]})](https://ohou.se/cards/{doc["id"]})')
                with st.expander('Explain'):
                    explained = f"{doc['_score']:.2f}\n"
                    explained += parse_explain_(doc['_explanation'])
                    explained += parse_explain(doc['_explanation'])
                    st.text(explained)
                # if debug_info is not None:
                #     if doc["id"] not in debug_info["id2rank"]:
                #         col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                #     else:
                #         col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

        for idx, (img, doc) in enumerate(zip(tobe_images, tobe_docs)):
            col = comp_cols[idx % mid]
            with col:
                col.image(img)
                col.markdown(f'[{doc["id"]} ({doc["_score"]})](https://ohou.se/cards/{doc["id"]})')

                rank = compare_rank(asis_id2rank.get(doc['id']), tobe_id2rank.get(doc['id']))
                if rank == 'same' or rank == 0:
                    pass
                elif rank > 0:
                    col.success(f'Rank 변동: +{rank}')
                else:
                    col.error(f'Rank 변동: {rank}')
                    
                with st.expander('Explain'):
                    explained = f"{doc['_score']:.2f}\n"
                    explained += parse_explain_(doc['_explanation'])
                    explained += parse_explain(doc['_explanation'])
                    st.text(explained)
                # if debug_info is not None:
                #     if doc["id"] not in debug_info["id2rank"]:
                #         col.error(f'Score: {doc["_score"]} [저품질 가능성❗]️')
                #     else:
                #         col.info(f'Score: {doc["_score"]}, Rank: {debug_info["id2rank"][doc["id"]][0]+1}, Click: {debug_info["id2rank"][doc["id"]][1]}')
                with st.expander('Debug'):
                    st.json(compress_doc(doc))

def text_analyzer_page():
    query = st.text_input(
        label="Search",
        value=DEFAULT_QUERY
    )

    if query:
        analyzers_result = card_searcher.get_query_analyze_result(query)
        for name, anal in analyzers_result.items():
            # {'tokens': [{'token': '흙', 'start_offset': 0, 'end_offset': 1, 'type': 'word', 'position': 0}, ...}
            query_anal = ' '.join([f'"{x["token"]}/{x["type"]}/{x["position"]}"' for x in anal['tokens']])
            st.subheader(name)
            st.write(query_anal)
            with st.expander('Detail (Json)'):
                st.json(anal['detail'])
    
    with open('../../elasticsearch_client/service_schema/card_search.md', 'r') as f:
        md = ''.join([line for line in f.readlines()])
    st.markdown(md)

def app():
    """ main """
    st.title("사진 검색(Card Search) 데모")
    utils.set_font_size()

    # query_params = st.experimental_get_query_params()
    # query_params

    page = st.sidebar.radio(
        'Pages',
        (
            'Ranking Demo (공유용)',
            'Ranking Demo (Debug)',
            'Ranking Demo (Debug/Compare)',
            'Ranking Demo',
            'Good & Bad Cases',
            '텍스트 분석',
        )
    )
    # page = st.selectbox(
    #     'Pages',
    #     (
    #         'Ranking Demo',
    #         'Good & Bad Cases',
    #     )
    # )

    # f'You selected: {page}'
    if page == 'Ranking Demo (공유용)':
        ranking_page_share()
    elif page == 'Ranking Demo':
        ranking_page()
    elif page == 'Ranking Demo (Debug/Compare)':
        ranking_page_debug_compare()
    elif page == 'Ranking Demo (Debug)':
        # ranking_page_debug()
        ranking_page_debug()
    elif page == 'Good & Bad Cases':
        case_page()
    elif page == '텍스트 분석':
        text_analyzer_page()
        

if __name__ == '__main__':
    app()
