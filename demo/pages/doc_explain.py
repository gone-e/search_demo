import os
import sys
sys.path.append(".")
import streamlit as st
from demo import MYELASTICSEARCH_RESOURCE_DIR
from demo import SERVICE_LIST_REV
from services import SERVICE_TO_ES
from ranking.card import __all__ as card_ranker
from ranking.commerce import __all__ as commerce_ranker
from ranking.advice import __all__ as advice_ranker
from ranking.project import __all__ as project_ranker
from ranking.question import __all__ as question_ranker

SERVICE_TO_RANKER = {
    "card": card_ranker,
    "commerce": commerce_ranker,
    "advice": advice_ranker,
    "project": project_ranker,
    "question": question_ranker,
}

def page(service):
    # set elasticsearch client
    ES = SERVICE_TO_ES[SERVICE_LIST_REV[service]]
    
    # st.write(card_ranker)

    # Declare a form and call methods directly on the returned object
    form = st.form(key="my_form")
    document_id = form.text_input(label="문서 ID", value="2206090")
    query = form.text_input(label="검색키워드", value="티비삼각대")
    # ranker = form.selectbox("Ranker(ES Request Body)", ["서비스"] + SERVICE_TO_RANKER[SERVICE_LIST_REV[service]])
    submit = form.form_submit_button(label="Submit")

    if submit:
        if not document_id.strip() or not query.strip():
            st.error("문서 ID와 검색키워드 모두 입력해주세요")
        else:
            # st.write(ranker)
            res = ES.explain_specific_document(document_id=document_id, query=query)
            # if ranker == "서비스":
            #     res = ES.explain_specific_document(document_id=document_id, query=query)
            # else:
            #     res = ES.explain_specific_document(document_id=document_id, request_body=eval(ranker).generate(query))
            st.json(res)




