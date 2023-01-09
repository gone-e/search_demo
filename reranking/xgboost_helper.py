import sys
sys.path.append(".")
import ltr.judgments as judge
import pandas as pd
import xgboost as xgb
from matplotlib.pylab import rcParams
rcParams['figure.figsize'] = 50,150

def import_data(data_path)
    df = [j for j in judge.judgments_from_file(open(data_path))]
    df = judge.judgments_to_dataframe(df)
    print(df.head(10))
    print()
    return df

"../reranking/card/test.add.txt"

import ltr.judgments as judge
df = [j for j in judge.judgments_from_file(open('data/classic-training.txt'))]
df = judge.judgments_to_dataframe(df)
df
