import sys
sys.path.append(".")
import os
import pandas as pd
import random
import json
import numpy as np
import datetime
import statistics as stats
import copy
from ltr.judgments import judgments_from_dataframe
from myelasticsearch.ltr_wrapper import LTRWrapper
myltr = LTRWrapper()


class CTRHelper:

    def __init__(self, impression_column, click_column) -> None:
        self.impression_column = impression_column
        self.click_column = click_column
    
    def regularize(self, df):
        df = self.by_modify_factor(df, name="mctr", denom_factor=20, num_factor=1)
        df["mctr"] = df.apply(lambda row: self.lower_weight(row, column="mctr"), axis=1)
        return df

    def lower_weight(self, row, column, max_small_imp=10, weight=0.8):
        """ 너무 낮은 impressions의 문서는 가중치를 낮추기 """
        if row[self.impression_column] < max_small_imp:
            return row[column] * weight
        return row[column]

    def by_modify_factor(self, df, denom_factor=99, num_factor=1, name="mctr"):
        df = df.copy()
        df[name] = (df[self.click_column] + num_factor) / (df[self.impression_column] + denom_factor)
        return df
            
def calculate_percentiles(df, column, percentiles, exclude_zero=False):
    if exclude_zero:
        df = df[df["clicks"] > 0]
    percentile_values = []
    for p in percentiles:
        percentile_values.append(df[column].quantile(p))
    return percentile_values

def calculate_mean(df, column, exclude_zero=False):
    if exclude_zero:
        df = df[df["clicks"] > 0]
    return df[column].mean()

def load_base_data(data_path):
    df = pd.read_csv(data_path)
    # 이상한 로그 제거하기
    abnormal_idx_list = df.loc[(df["impressions"] == 0) & (df["clicks"] > 0)].index
    print("imp=0, click>0 인 이상한 경우:", len(abnormal_idx_list))
    df.drop(abnormal_idx_list, axis=0, inplace=True)
    print(f"data length: {len(df)}")
    return df

def get_grade(ctr, percentiles):
    #print(ctr, np.quantile(ctr_list, 0.95))
    if ctr >= percentiles[0]:
        return "4"
    elif ctr >= percentiles[1]:
        return "3"
    elif ctr >= percentiles[2]:
        return "2"
    elif ctr >= percentiles[3]:
        return "1"
    return "0"

def get_binary_grade(ctr, cutoff):
    if ctr >= cutoff:
        return "1"
    return "0"

def print_grade_distribution(df):
    grade_dist = {
        "0": [],
        "1": [],
        "2": [],
        "3": [],
        "4": [],
    }

    for _, gdf in df.groupby(["search_keyword"]):
        grade_0 = len(gdf[gdf["grade"] == '0'])
        grade_1 = len(gdf[gdf["grade"] == '1'])
        grade_2 = len(gdf[gdf["grade"] == '2'])
        grade_3 = len(gdf[gdf["grade"] == '3'])
        grade_4 = len(gdf[gdf["grade"] == '4'])
        num_row = len(gdf)
        grade_dist["0"].append(grade_0/num_row)
        grade_dist["1"].append(grade_1/num_row)
        grade_dist["2"].append(grade_2/num_row)
        grade_dist["3"].append(grade_3/num_row)
        grade_dist["4"].append(grade_4/num_row)

    for k, v in grade_dist.items():
        print(k, f"{np.mean(v):.6f}")

def dump_ranking_data(df, dump_path, diversity=3):
    def convert_to_judgements(df, diversity):
        print("convert dataframe to judgements")
        judgments, featuremap = judgments_from_dataframe(df, diversity=diversity)
        print("  > number of judgements:", len(judgments))
        return judgments, featuremap
    def dump_feature_map(featuremap, dump_path):
        with open(dump_path, "w+") as writer:
            for idx, feat in enumerate(featuremap):
                data = [
                    idx,
                    feat,
                    "q",
                ]
                writer.write(" ".join(str(x) for x in data) + "\n")

    judgments, featuremap = convert_to_judgements(df, diversity=diversity)
    print(f"... dump ranking data to {dump_path}")
    myltr.dump_ranking_data(judgments, dump_path=dump_path)
    featuremap_path = dump_path.replace(".txt", ".fmap.txt")
    dump_feature_map(featuremap, featuremap_path)

def dump_ranking_data_sample(df, dump_path, n_samples=100):
    ids = df["search_keyword"].unique()
    random.shuffle(ids)
    df = df.set_index("search_keyword").loc[ids[:n_samples]].reset_index()
    df.to_csv(dump_path, index=False)

def main():
    """ main script """
    # FIXME
    SERVICE = "card"
    PERIOD = "3m"
    DATA_CREATED_AT = datetime.datetime.today().strftime("%Y%m%d")
    DATA_CREATED_AT = "20220504"

    RANKING_DATA_DIR = f"./rdataset/{SERVICE}/{DATA_CREATED_AT}"
    BASE_DATA_PATH = os.path.join(RANKING_DATA_DIR, f"{SERVICE}.click.ranking.{PERIOD}.features.csv")
    RANKING_DATA_SAMPLE_PATH = os.path.join(f"./dataset/{SERVICE}", f"{DATA_CREATED_AT}.{SERVICE}.click.ranking.{PERIOD}.features.grade.binary.samples.csv")
    RANKING_DATA_PATH = os.path.join(RANKING_DATA_DIR, f"{SERVICE}.click.ranking.{PERIOD}.features.grade.binary.txt")
    print(f"SERVICE: {SERVICE}\nPERIOD: {PERIOD}\nDATA_CREATED_AT: {DATA_CREATED_AT}")
    print(f"BASE_DATA_PATH: {BASE_DATA_PATH}")
    print(f"RANKING_DATA_PATH: {RANKING_DATA_PATH}")

    # read data
    df = load_base_data(BASE_DATA_PATH)

    # TODO: 좀 비싸긴 하지만 효과가 있을 것으로 보이는 proximity 점수, multifields 점수를 함께 반영하는 것은 어떨까?
    # TODO: CTR로만 하기에는 노이즈가 많아서 어느정도 설명이되는 것들로 들어가면 좋지 않을까? 의존성은 좀 있을지라도
    # regularize CTR globally
    # NOTE: impressions가 너무 왜곡이 많이 되어 있다. (뒤로가기, 새로고침 등) 특히 클릭이 발생한 주변 문서들에 대해서도!
    ctr_helper = CTRHelper(impression_column="uimpressions", click_column="uclicks")
    df = ctr_helper.regularize(df)

    TARGET = "mctr"
    grade_ranges = [0.95, 0.85, 0.65, 0.35]
    percentiles = calculate_percentiles(df, TARGET, grade_ranges, exclude_zero=True)
    cutoff = calculate_percentiles(df, TARGET, [0.5], exclude_zero=True)[0]
    print("... cutoff:", cutoff)

    df_copy = copy.deepcopy(df)
    df = None
    for i, (query, group_df) in enumerate(df_copy.groupby(["search_keyword"])):

        group_df = copy.deepcopy(group_df)
        # NOTE: impression 1 이하는 제거
        group_df = group_df[group_df["uimpressions"] > 1]
        if len(group_df) == 0: 
            print(f"Pass Query: {query}")
            continue
        # NOTE: grade "0" 인 것들은 샘플링하여 50%만 사용
        # group_df = group_df.sample(frac=0.5)
        # generate grade
        # group_df["grade"] = group_df.apply(lambda row: get_grade(row[TARGET], percentiles), axis=1)
        group_df["grade"] = group_df.apply(lambda row: get_binary_grade(row[TARGET], cutoff), axis=1)
        group_df["grade2"] = group_df.apply(lambda row: get_binary_grade(row["uclicks"], 2), axis=1)
        # group_df = group_df.sort_values(["grade"], ascending=False)

        # TODO: grade 통합(3점, 4점 -> 1점), 0점 -> 0점
        # TODO: grade 보정
        # filtering
        # good_case = group_df[(group_df["grade"] == "4") & (group_df["grade"] == "3") & (group_df["uclicks"] > 1)]
        # good_case = group_df[(group_df["grade"] == "4") | (group_df["grade"] == "3") | (group_df["grade"] == "2")]
        # good_case = group_df[group_df["uclicks"] > 1]
        # good_case = good_case.copy()
        # good_case["grade"] = ["1"] * len(good_case)
        # bad_case = group_df[
        #                 (group_df["grade"] == "0") 
        #                 & (group_df["f__description.bm25"] < 0.1) 
        #                 # & (group_df["f__description.proximity"] < 0.1) 
        #                 & (group_df["f__prod_name.bm25"] < 0.1) 
        #                 # & (group_df["f__prod_name.proximity"] < 0.1) 
        #                 & (group_df["f__prod_categories.bm25"] < 0.1) 
        #                 # & (group_df["f__prod_categories.proximity"] < 0.1) 
        #                 & (group_df["f__keyword_list.korean.bm25"] < 0.1) 
        #                 # & (group_df["f__keyword_list.korean.proximity"] < 0.3) 
        #             ]
        # bad_case = bad_case.copy()
        # bad_case["grade"] = ["0"] * len(bad_case)
        # group_df = pd.concat([good_case, bad_case])
        # print(len(good_case), len(group_df))
        # if len(group_df) == 0:
        #     print(f"Pass Query: {query}")
        #     continue

        # 하나의 등급만 가지고 있는 경우(예: 0만 가지고 있는 경우)
        if len(group_df["grade"].unique()) == 1:
            print(f"Pass Query: {query}")
            continue

        if df is None:
            df = group_df
        else:
            df = pd.concat([df, group_df])

    df.insert(0, TARGET, df.pop(TARGET))
    df.insert(0, "grade", df.pop("grade"))
    print(f"Final Dataset's Unique Queries: {len(df['search_keyword'].unique())}")
    print(df.head())

    print_grade_distribution(df)

    # dump ranking data for model training
    # dump_ranking_data(df, RANKING_DATA_PATH, diversity=3)
    dump_ranking_data(df, RANKING_DATA_PATH, diversity=0)

    # dump sample data for demo
    dump_ranking_data_sample(df, RANKING_DATA_SAMPLE_PATH, n_samples=100)


if __name__ == "__main__":
    main()