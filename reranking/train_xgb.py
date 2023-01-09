import sys
sys.path.append("../../")
import ltr.judgments as judge
import pandas as pd
import xgboost as xgb
import pandas as pd

def read_ranking_data(data_path):
    df = [j for j in judge.judgments_from_file(open(data_path))]
    return judge.judgments_to_dataframe(df)

    
def main():
    SERVICE = "card"
    PERIOD = "1m"
    # DATA_CREATED_AT = "20220429"
    # DATA_CREATED_AT = "20220503"
    DATA_CREATED_AT = "20220504"
    # RANKING_DATA = f"{DATA_CREATED_AT}.{SERVICE}.click.ranking.base.{PERIOD}.features.grade.txt"
    RANKING_DATA = f"{DATA_CREATED_AT}.{SERVICE}.click.ranking.base.{PERIOD}.features.grade.binary.txt"
    RANKING_DATA_PATH = f"../../rdataset/{SERVICE}/{RANKING_DATA}"
    FEATURE_MAP_PATH = RANKING_DATA_PATH.replace(".txt", ".fmap.txt")
    print(f"SERVICE: {SERVICE}\nPERIOD: {PERIOD}\nDATA_CREATED_AT: {DATA_CREATED_AT}")
    print(RANKING_DATA_PATH)

if __name__ == "__main__":
    main()