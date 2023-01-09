""" card_search
사진 검색 문서 랜덤샘플 데이터 가져오기

* 방법 1. Elasticsearch engine에 검색
    Elasticsearch 에서 _uid(type + id)값을 이용하여 
    모든 문서에 random score를 부여하고 K개의 문서를 추출
    참고: https://www.elastic.co/guide/en/elasticsearch/reference/5.4/query-dsl-function-score-query.html#function-random

* 방법 2. 원본 데이터 테이블에서 랜덤 표본 추출
    ```sql
    select *
    from search.card_search_index
    limit 10
    ```
    주의: 인덱스 데이터를 최종적으로 emr코드에서 가공하기 때문에 실제 문서와는 일부 빠진 것이 있다던가 차이가 있다.

"""
from typing import Generator
from aws.athena.transparent_select_rows import TransparentSelectRows


def get_top_query_generator(search_type: str) -> Generator:
    athena = TransparentSelectRows()
    query = f"""
    SELECT DISTINCT keyword
    FROM log_firehose.popular_search_trend
    WHERE search_type IN ('{search_type}', 'total')
    """
    return athena.run("log_firehose", query)


def get_random_query_generator(size=200) -> Generator:
    athena = TransparentSelectRows()
    query = f"""
    SELECT distinct search_keyword as keyword
    FROM log.analyst_log_table
    WHERE date = cast(current_date - interval '2' day AS varchar)
    LIMIT {size}
    """
    return athena.run("log", query)


a = get_random_query_generator()
print(a)



# import sys
# import pyspark.sql.functions as F

# from datetime import datetime, timedelta
# from pyspark.sql import SparkSession
# from pyspark.ml.recommendation import ALS


# spark = SparkSession.builder.enableHiveSupport().getOrCreate()


# def import_data(date):
#     rank_ctr_df = spark.sql(f"""
#         SELECT
#             object_idx,
#             COUNT(DISTINCT IF(category='IMPRESSION', visitor_id, null)) AS rank_qc,
#             COUNT(DISTINCT IF(category='CLICK', visitor_id, null)) AS rank_cc
#         FROM
#             log.analyst_log_table
#         WHERE
#             date = '{date}'
#             AND search_keyword != ''
#             AND object_section = '스토어 검색 결과'
#             AND CAST(object_idx AS INTEGER) < 400
#         GROUP BY
#             object_idx
#         ORDER BY
#             CAST(object_idx AS INTEGER)
#         """)

#     query_rank_ctr_df = spark.sql(f"""
#         SELECT
#             *
#         FROM
#             (
#                 SELECT
#                     LOWER(REPLACE(REPLACE(search_keyword, ' ', ''), '	', '')) AS search_keyword,
#                     object_idx,
#                     object_id,
#                     COUNT(DISTINCT IF(category='IMPRESSION', visitor_id, null)) AS qc,
#                     COUNT(DISTINCT IF(category='CLICK', visitor_id, null)) AS cc
#                 FROM
#                     log.analyst_log_table
#                 WHERE
#                     date = '{date}'
#                     AND search_keyword != ''
#                     AND object_section = '스토어 검색 결과'
#                     AND CAST(object_idx AS INTEGER) < 400
#                 GROUP BY
#                     LOWER(REPLACE(REPLACE(search_keyword, ' ', ''), '	', '')), object_idx, object_id
#             )
#         WHERE
#             qc > 5
#         """)

#     return rank_ctr_df, query_rank_ctr_df


# def main(date, hive_db):
#     d_date = datetime.strptime(date, '%Y-%m-%d')
#     past_date = (d_date - timedelta(days=112)).strftime('%Y-%m-%d') # 오래된 db data 삭제용

#     rank_ctr_df, query_rank_ctr_df = import_data(date)

#     rank_ctr_d_df = rank_ctr_df.withColumn("date", F.lit(date))
#     query_rank_ctr_d_df = query_rank_ctr_df.withColumn("date", F.lit(date))

#     # 테이블이 없으면 동작하지 않음. 최초 1번은 없이 실행해야 함
#     # 테이블 있는지 체크 하여 분기하면 더 좋음

#     # 과거 사용하지 않는 테이블 삭제
#     # 하루라도 실행되지 않으면 데이터가 계속 지워지지 않을텐데 '<=' 조건으로 지울 방법은 없을까? 넉넉한 기간으로 loop?
#     spark.sql(f"alter table {hive_db}.feedback_ctr_model_rank_ctr_daily drop if exists partition (date='{past_date}')")
#     spark.sql(f"alter table {hive_db}.feedback_ctr_model_query_rank_ctr_daily drop if exists partition (date='{past_date}')")
#     # 추출할 테이블 삭제
#     spark.sql(f"alter table {hive_db}.feedback_ctr_model_rank_ctr_daily drop if exists partition (date='{date}')")
#     spark.sql(f"alter table {hive_db}.feedback_ctr_model_query_rank_ctr_daily drop if exists partition (date='{date}')")

#     # save as table
#     rank_ctr_d_df.write.mode('append').partitionBy('date').saveAsTable(f'{hive_db}.feedback_ctr_model_rank_ctr_daily')
#     query_rank_ctr_d_df.write.mode('append').partitionBy('date').saveAsTable(f'{hive_db}.feedback_ctr_model_query_rank_ctr_daily')


# if __name__ == '__main__':
#     today = sys.argv[1]
#     hive_db = sys.argv[2]

#     main(today, hive_db)
