from re import U
import sys
sys.path.append(".")
from jinja2 import Template
from aws.athena.transparent_select_rows import TransparentSelectRows
import os
import datetime
import json
import pandas as pd
import ast


SQL = Template("""
with 
    -- Query Info Table: qc, cc, uqc, ucc, uctr
    qinfo_t as (
        select
            search_keyword,
            count(if(category = 'PAGEVIEW', visitor_id, null)) as qc,
            count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as cc,
            100 * count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(if(category = 'PAGEVIEW', visitor_id, null)) as double) as ctr,
            count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as uqc,
            count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as ucc,
            100 * count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as double) as uctr

        from log.analyst_log_table as l

        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}

          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and trim(search_keyword) != ''
          -- platform 앱으로 제한
          and platform in ('IOS', 'ANDRIOD')
        group by search_keyword
    )
    
select *
from qinfo_t
-- qc 제한
where qc >= {{ minimum_qc}}
order by rand()
limit 1000
""")

SERVICE_OBJECT_TYPE = {
    "card": "CARD",
    "commerce": "PRODUCTION",
    "project": "PROJECT",
    "advice": "ADVICE",
    "question": "QUESTION",
}

SERVICE_URL_PATH = {
    "card": "https://ohou.se/cards/feed",
    "commerce": "https://ohou.se/productions/feed",
    "project": "https://ohou.se/projects",
    "advice": "https://ohou.se/advices",
    "question": "https://ohou.se/questions",
}

def main(service=None, period=None):
    # FIXME
    SERVICE = "commerce"
    PERIOD = "1w"
    if service is not None:
        SERVICE = service
    if period is not None:
        PERIOD = period

    MINIMUM_QC = 10
    DATA_CREATED_AT = datetime.datetime.today().strftime("%Y%m%d")

    base_sql = SQL.render(
        period=PERIOD,
        object_type=SERVICE_OBJECT_TYPE[SERVICE],
        service_url_path=SERVICE_URL_PATH[SERVICE],
        minimum_qc=MINIMUM_QC
    )
    print(base_sql)

    # run query
    athena = TransparentSelectRows()
    res = athena.run("log", base_sql)
    
    df = pd.DataFrame([row for chunk in res for row in chunk])

    mydir = f"./dataset/{SERVICE}"
    if not os.path.isdir(mydir):
        os.mkdir(mydir)
    save_file = f"./dataset/{SERVICE}/search_keywords.qc{MINIMUM_QC}.{PERIOD}.1K.{DATA_CREATED_AT}.csv"
    print(f"... save as {save_file}\n")
    df.to_csv(save_file, index=False)
    
def run_all():
    for period in ["1w"]:
        for service in SERVICE_OBJECT_TYPE.keys():
            if service == "card":
                continue
            main(service, period)

if __name__ == "__main__":
    # main()
    run_all()