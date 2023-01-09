import streamlit as st
import json

@st.cache
def _read_debug_query(data='../../dataset/card/query.debug.jsonl'):
    sample_queries = {}
    with open(data, 'r') as f:
        for _, line in enumerate(f):
            data = json.loads(line)
            sample_queries[data['query']] = {k:v for k, v in data.items() if k != 'query'}
    return sample_queries
