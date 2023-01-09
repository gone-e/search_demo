from dataclasses import dataclass
import os
import sys
sys.path.append(".")
from collections import OrderedDict
import ast
import pandas as pd
import streamlit as st
from demo import SERVICE_LIST, SERVICE_LIST_REV

def load_all_data():
    def _to_json(x):
        return ast.literal_eval(x)

    option_period = "1m"
    df = None
    for i, service in enumerate(SERVICE_LIST.keys()):
        # each_df = pd.read_csv(f"../dataset/{service}/{service}.click.ranking.base.{option_period}.rs.1K.sr.csv")
        each_df = pd.read_csv(f"./dataset/{service}/{service}.click.ranking.base.{option_period}.rs.1K.sr.csv")
        each_df["rank2clickCntAndId"] = each_df["rank2clickCntAndId"].apply(_to_json)
        each_df = each_df[["search_keyword", "rank2clickCntAndId"]]
        if i == 0:
            df = each_df
            q_ueries = set(df["search_keyword"].values.tolist())
            continue
        df = pd.merge(df, each_df, left_on='search_keyword', right_on='search_keyword', how='inner')
        print(df.head())
    


def page():
    """ 클릭 정보와 함께 검색결과를 볼 수 있는 페이지 """
    load_all_data()

    # try:
    #     es, data_df = load_data_and_es(service, option_period)
    # except:
    #     st.error("해당 데이터는 지원이 안됩니다")
    #     return

    # view = load_view(service)

    # new_data_df = data_df[
    #     (data_df.qc >= option_qc ) 
    #     & (data_df.cc >= option_cc) 
    #     & (data_df.uqc >= option_uqc) 
    #     & (data_df.ucc >= option_ucc) 
    #     & (data_df.numClickUsers>= option_num_click_users)
    # ]
    # query2data = {row["search_keyword"]:row.to_dict() for idx, row in new_data_df.iterrows()}
    # if len(data_df) != len(new_data_df):
    #     st.info(f"데이터 개수: {len(data_df)} -> {len(new_data_df)}")
    
    # query = st.selectbox(
    #     "예제 질의들:",
    #     query2data.keys()
    # )

    # input_query = st.text_input(
    #     label="검색창:",
    #     placeholder="샘플질의에 있는 질의만 동작합니다. 해당 질의를 입력해주세요."
    # )

    # if input_query.strip() and input_query in query2data:
    #     query = input_query
    #     # 쿼리를 직접 입력한 경우에는 전체 질의에서 찾기 위해 다시 전체 데이터로 바꿔준다.
    #     query2data = {row["search_keyword"]:row.to_dict() for idx, row in data_df.iterrows()}

    # if query:
    #     # st.header(es.env)
    #     # st.header(es.service)
    #     # st.header(view)

    #     st.subheader("Query Analyzer")
    #     # col1, col2 = st.columns(2)
    #     res = get_analyze_result(card_dev, query, analyzers=["korean", "korean_syn"])
    #     st.write(res)

    #     dat = query2data[query]

    #     st.subheader((
    #         f"Result [ClickUsers={dat.get('numClickUsers')}"
    #         f", QC={dat.get('qc')}, CC={dat.get('cc')}, CTR={dat.get('ctr'):.0f}"
    #         f", uQC={dat.get('uqc')}, uCC={dat.get('ucc')}, uCTR={dat.get('uctr'):.0f}]"
    #     ))

    #     ranking_data = ast.literal_eval(dat["rank2clickCntAndId"])

    #     # top100 dist
    #     click_list = [x["clickCnt"] for rank, x in ranking_data.items() if int(rank) <= 100]
    #     avg_click = np.mean(click_list)
    #     avg_click_nonzero = np.mean([x for x in click_list if x > 0])
    #     draw_dist(click_list, writer=st, figsize=(30,2), hlines=[avg_click, avg_click_nonzero])


if __name__ == "__main__":
    page()