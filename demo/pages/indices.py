import os
import sys
sys.path.append(".")
import streamlit as st
from demo import MYELASTICSEARCH_RESOURCE_DIR


def page():
    """ 서비스별로 인덱스 정보를 보여주는 페이지 """
    # TODO: runtime 으로 변경
    with st.expander('사진검색 Mappings'):
        with open(os.path.join(MYELASTICSEARCH_RESOURCE_DIR, "index/card_search.md"), "r") as f:
            md = ''.join([line for line in f.readlines()])
        st.markdown(md)
