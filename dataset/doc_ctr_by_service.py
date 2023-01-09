import sys
sys.path.append(".")
from demo import SERVICE_LIST, SERVICE_LIST_REV
from demo.pages.ranking_data import load_data_and_es
import numpy as np
import json
import ast
import pandas as pd

option_period = "1w"
data_list = {}
for service_name, service in SERVICE_LIST.items():
    df = pd.read_csv(f"./dataset/{service_name}/{service_name}.click.ranking.base.{option_period}.rs.1K.sr.csv")
    data_list[service] = df

# 문서별 CTR 평균
# 문서별 CTR, 보정 CTR, 표본평균의 정규화

for service, df in data_list.items():
    ctr_list = []
    mctr_list = []
    click_list = []
    for idx, row in df.iterrows():
        for rank, v in ast.literal_eval(row["rank2clickCntAndId"]).items():
            if int(rank) > 50:
                break
            if v['clickCnt'] < 1:
                continue
            doc_ctr = v['clickCnt'] / row["qc"] * 100
            mdoc_ctr = v['clickCnt'] / (row["qc"] + 5) * 100
            click_list.append(v['clickCnt'])
            ctr_list.append(doc_ctr)
            mctr_list.append(mdoc_ctr)
    
    print(f"{service}: avgCTR={np.mean(ctr_list):.2f}, avgmCTR={np.mean(mctr_list):.2f}, maxCTR={np.max(ctr_list)}, avgClick={np.mean(click_list):.2f}, maxClick={np.max(click_list):.2f}")



