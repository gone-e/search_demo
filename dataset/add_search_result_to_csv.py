import sys
sys.path.append(".")
import ast
import copy
import pandas as pd

from services import (
    card_dev,
    commerce_dev,
    advice_dev,
    project_dev,
    question_dev,
)

def add_search_result(es, click_ranking_base_data, top_k=300):
    """ (1회성 또는 최신성) 클릭된 문서 id에 현재 기준의 랭킹순서를 붙여준다 """
    def convert_presto_kv_to_json(x):
        kvdict  = {str(k): v for k, v in sorted(ast.literal_eval(x.replace("=", ":")).items())}
        return {k: v for k, v in sorted(kvdict.items(), key=lambda x:x[1], reverse=True)}

    df = pd.read_csv(click_ranking_base_data)
    # df = df.head(10)  # test
    df["id2clickCnt"] = df["id2clickCnt"].apply(convert_presto_kv_to_json)

    new_df = []
    for idx, row in df.iterrows():
        # if idx == 100: break
        # 300개 랭킹
        if idx % 100 == 0:
            print(f'... process {idx}: {row["search_keyword"]}', flush=True)
        try:
            sr = es.get_search_result(row["search_keyword"], top_k=top_k)
            items = sr["hits"]["hits"]
        except:
            print(f"[ERROR] query: {row['search_keyword']}")
            continue
        # rank 순서대로 클릭정보 붙이기
        rank2clickcnt_and_id = {}
        for rank, item in enumerate(items):
            click_cnt = row["id2clickCnt"].get(item["_id"])
            if click_cnt is None:
                click_cnt = 0
            rank2clickcnt_and_id[str(rank+1)] = {"clickCnt": int(click_cnt), "id": item["_id"]}
        row["rank2clickCntAndId"] = rank2clickcnt_and_id
        new_df.append(copy.deepcopy(row))
    
    # add new column
    df = pd.DataFrame(new_df)
    df.to_csv(click_ranking_base_data.replace(".csv", "") + ".sr.csv", index=False)

def add_search_result_v2(es, click_ranking_base_data, top_k=300):
    """ (1회성 또는 최신성) 클릭된 문서 id에 현재 기준의 랭킹순서를 붙여준다 """
    def _to_json(x):
        return ast.literal_eval(x)

    df = pd.read_csv(click_ranking_base_data)
    # df = df.head(10)  # test
    df["docInfo"] = df["docInfo"].apply(_to_json)

    new_df = []
    for idx, row in df.iterrows():
        # if idx == 10: break
        # 300개 랭킹
        if idx % 100 == 0:
            print(f'... process {idx}: {row["search_keyword"]}', flush=True)
        try:
            sr = es.get_search_result(row["search_keyword"], top_k=top_k)
            items = sr["hits"]["hits"]
        except:
            print(f"[ERROR] query: {row['search_keyword']}")
            continue
        row_copy = copy.deepcopy(row)
        # docInfo: object_id -> [qc, cc, ctr, uqc, ucc, uctr]
        # rank 순서대로 클릭정보 붙이기
        rank2docinfo = {}
        for rank, item in enumerate(items):

            if item["_id"] not in row["docInfo"]:
                rank2docinfo[str(rank+1)] = {
                    "id": item["_id" ],
                    "qc": 0,
                    "cc": 0,
                    "ctr": 0,
                    "uqc": 0,
                    "ucc": 0,
                    "uctr": 0,
                    "avgRank": None,
                    "stdRank": None, 
                    "scrapCnt": 0,
                }
            else:
                qc, cc, ctr, uqc, ucc, uctr, avg_rank, std_rank, scrap_cnt = row["docInfo"][item["_id"]]
                rank2docinfo[str(rank+1)] = {
                    "id": item["_id"],
                    "qc": int(qc),
                    "cc": int(cc), 
                    "ctr": round(float(ctr), 2),
                    "uqc": int(uqc), 
                    "ucc": int(ucc), 
                    "uctr": round(float(uctr), 2),
                    "avgRank": round(float(avg_rank), 2),
                    "stdRank": round(float(std_rank), 2), 
                    "scrapCnt": 0,
                }

        row_copy["rank2docinfo"] = rank2docinfo
        row_copy.pop('docInfo')
        new_df.append(row_copy)
    
    # add new column
    df = pd.DataFrame(new_df)
    save_file = click_ranking_base_data.replace(".csv", "") + ".sr.csv"
    print(f"... save as {save_file}")
    df.to_csv(save_file, index=False)

def run_all():
    # for period in ["1d", "1w", "1m"]:
    # for period in ["1d", "1w"]:
    # for period in ["1m"]:
    for period in ["6m"]:
        for service in ["card", "commerce", "project", "advice", "question"]:
            if service == "card":
                es = card_dev
            elif service == "commerce":
                es = commerce_dev
            elif service == "project":
                es = project_dev
            elif service == "advice":
                es = advice_dev
            elif service == "question":
                es = question_dev
            # add_search_result(es, f"./dataset/{service}/{service}.click.ranking.base.{period}.rs.1K.csv", top_k=300)
            add_search_result_v2(es, f"./dataset/{service}/{service}.click.ranking.base.{period}.rs.1K.v2.csv", top_k=300)


if __name__ == "__main__":
    run_all()
    # card data
    # add_search_result(card_dev, "./dataset/card/card.click.ranking.base.1d.rs.1K.csv", top_k=300)
    # add_search_result(card_dev, "./dataset/card/card.click.ranking.base.1w.rs.1K.csv", top_k=300)
    # add_search_result(card_dev, "./dataset/card/card.click.ranking.base.1m.rs.1K.csv", top_k=300)
    # add_search_result(card_dev, "./dataset/card/card.click.ranking.base.1w.rs.1K.v2.csv", top_k=300)
    # add_search_result(card_dev, "./dataset/card/card.click.ranking.base.1m.rs.1K.v2.csv", top_k=300)
    # add_search_result_v2(card_dev, "./dataset/card/card.click.ranking.base.1m.rs.1K.v2.csv", top_k=300)

    # commerce data
    # add_search_result(commerce_dev, "./dataset/commerce/commerce.click.ranking.base.1d.rs.1K.csv", top_k=300)
    # add_search_result(commerce_dev, "./dataset/commerce/commerce.click.ranking.base.1w.rs.1K.csv", top_k=300)
    # add_search_result(commerce_dev, "./dataset/commerce/commerce.click.ranking.base.1w.rs.1K.v2.csv", top_k=300)
    # add_search_result(commerce_dev, "./dataset/commerce/commerce.click.ranking.base.1m.rs.1K.v2.csv", top_k=300)

    # project data
    # add_search_result(project_dev, "./dataset/project/project.click.ranking.base.1d.rs.1K.csv", top_k=300)
    # add_search_result(project_dev, "./dataset/project/project.click.ranking.base.1w.rs.1K.csv", top_k=300)
    # add_search_result(project_dev, "./dataset/project/project.click.ranking.base.1m.rs.1K.v2.csv", top_k=300)

    # advice data
    # add_search_result(advice_dev, "./dataset/advice/advice.click.ranking.base.1d.rs.1K.csv", top_k=300)
    # add_search_result(advice_dev, "./dataset/advice/advice.click.ranking.base.1w.rs.1K.csv", top_k=300)
    # add_search_result(advice_dev, "./dataset/advice/advice.click.ranking.base.1m.rs.1K.v2.csv", top_k=300)

    # question data
    # add_search_result(question_dev, "./dataset/question/question.click.ranking.base.1d.rs.1K.csv", top_k=300)
    # add_search_result(question_dev, "./dataset/question/question.click.ranking.base.1w.rs.1K.csv", top_k=300)
    # add_search_result(question_dev, "./dataset/question/question.click.ranking.base.1m.rs.1K.v2.csv", top_k=300)
