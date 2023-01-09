import os
import sys
sys.path.append(".")
from collections import OrderedDict
import streamlit as st
from services import SERVICE_TO_ES
from demo import SERVICE_LIST_REV
from demo.utils import get_analyze_result

# TODO: https://github.com/o19s/elyzer 이 스크립트 참조하여 형태소분석결과 개선하기
def page(service):
    """ 형태소 분석 결과(Detail)를 볼 수 있는 공통 페이지 """
    query = st.text_input(
        label="Search",
        value="러그"
    )

    if query:
        ES = SERVICE_TO_ES[SERVICE_LIST_REV[service]]
        res, res_json = get_analyze_result(ES, query, analyzers=None, with_json=True)
        res_detail = ES.get_analyze_result(query, detail=True, analyzers=None)

        for analyzer in res.keys():
            st.subheader(analyzer)
            st.write(res[analyzer])
            with st.expander('Json'):
                st.json(res_json[analyzer])
            with st.expander('Detail (Json)'):
                st.json(res_detail[analyzer]['detail'])

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