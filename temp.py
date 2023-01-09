import pandas as pd
import datetime
import os

# df = pd.read_csv("./temp.csv")
# df = pd.read_csv("./ios.qc10.50.csv")
# df = pd.read_csv("./card.similar_id.csv")
# df.to_excel("./card.similar_id.xlsx")
# q = df.search_keyword.values.tolist()
# print(q)
def _extract_datetime_from_index(index: str):
    return datetime.datetime.strptime(re.findall(r"_([0-9-]*)t", index)[0], "%Y-%m-%d")

runner = os.getenv('RUNNER')
print(f"[{runner}] {type(runner)}")
print(datetime.datetime.now().strftime("%Y-%m-%dt%H%M%s"))

temp = "commerce_search_2022-05-17t16341652772860"
temp = "2022-05-15t16341652772860"
temp = "commerce_search_2022-05-15t20031652785415"
import re
print(re.findall(r"_([0-9-]*)t", temp))
# temp.split("t")
# # format = "%Y-%m-%d"
# created_at = datetime.datetime.strptime(temp, '%Y-%m-%dt%H%M%s')
# print( - created_at)
print(type((datetime.datetime.today() - _extract_datetime_from_index(temp)).days))
