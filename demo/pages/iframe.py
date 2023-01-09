import os
import sys
sys.path.append(".")
import requests
import streamlit as st
import streamlit.components.v1 as components


def page():
    r = requests.get("https://search.shopping.naver.com/search/all?where=all&frm=NVSCTAB&query=파라핀치료")
    components.html(r.content, height=1000, scrolling=True)