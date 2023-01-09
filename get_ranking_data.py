import sys
sys.path.append(".")
import os
import json
import ast
import pandas as pd
from aws.athena.transparent_select_rows import TransparentSelectRows
from jinja2 import Template

# 개별문서별 CTR 정보를 볼 수 있도록 개선한다.
# 다만 로깅 문제로 인해 앱 플랫폼 로그만 활용한다.
"""
select 
    object_type, object_section, count(*)
from log.analyst_log_table
where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
  and category = 'CLICK'
  and url_path in ('https://ohou.se/cards/[0-9]/detail', 'https://ohou.se/cards/[0-9]/detail/pinch')
  and platform in ('IOS', 'ANDRIOD')
group by 1,2
limit 100

#	object_type	    object_section	_col2
1	CARD	        비슷한 공간	18824
2	COLLECTIONS	    재생시작	5916
3	TAG	            상품태그	68932
4		            재생정지	454
5		            재생시작	478
6	PRODUCTION	    상품태그	3832
7	TAG	            상품태그 썸네일	21640
8	CARD_COLLECTION	재생정지	6808
9	CARD_COLLECTION	재생시작	6623
10	COLLECTIONS	    재생정지	5794

아래 순서대로 사진 디테일 페이지 정보가 많음
https://ohou.se/contents/card_collections
https://ohou.se/cards/[0-9]/detail


3	TAG	            상품태그	68932
7	TAG	            상품태그 썸네일	21640
6	PRODUCTION	    상품태그	3832

"""

# TODO: 기간별 추가
RANKING_SQL_V4 = Template("""
with 
    -- Log Table: 사진탭 클릭
    click_t as (
        select
            search_keyword,
            object_id,
            -- 사진 피드에서의 스크랩 횟수
            count(if(category = 'SCRAP', visitor_id, null)) as scrapCnt,
            -- average Rank
            round(avg(cast(object_idx as int)), 2) as avgRank,
            round(stddev_pop(cast(object_idx as double)), 2) as stdevRank,
            -- IMPRESSION은 영역마다 로그를 남긴다.
            count(if(category = 'IMPRESSION', visitor_id, null)) as impressions,
            count(if(category = 'CLICK', visitor_id, null)) as clicks,
            count(if(category = 'IMPRESSION' and date between cast(current_date - interval '3' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as impressions_1d,
            count(if(category = 'CLICK' and date between cast(current_date - interval '3' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as clicks_1d,
            count(if(category = 'IMPRESSION' and date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as impressions_1w,
            count(if(category = 'CLICK' and date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as clicks_1w,
            count(if(category = 'IMPRESSION' and date between cast(current_date - interval '16' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as impressions_2w,
            count(if(category = 'CLICK' and date between cast(current_date - interval '16' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as clicks_2w,
            count(if(category = 'IMPRESSION' and date between cast(current_date - interval '23' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as impressions_3w,
            count(if(category = 'CLICK' and date between cast(current_date - interval '23' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as clicks_3w,
            count(if(category = 'IMPRESSION' and date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as impressions_4w,
            count(if(category = 'CLICK' and date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as clicks_4w,
            -- 문서별 UV 수를 볼 때도 사용할 수 있다.
            count(distinct if(category = 'IMPRESSION', visitor_id, null)) as uimpressions,
            count(distinct if(category = 'CLICK', visitor_id, null)) as uclicks,
            count(distinct if(category = 'IMPRESSION' and date between cast(current_date - interval '3' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as uimpressions_1d,
            count(distinct if(category = 'CLICK' and date between cast(current_date - interval '3' day as varchar) and cast(current_date - interval '2' day as varchar) , visitor_id, null)) as uclicks_1d,
            count(distinct if(category = 'IMPRESSION' and date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as uimpressions_1w,
            count(distinct if(category = 'CLICK' and date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar) , visitor_id, null)) as uclicks_1w,
            count(distinct if(category = 'IMPRESSION' and date between cast(current_date - interval '16' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as uimpressions_2w,
            count(distinct if(category = 'CLICK' and date between cast(current_date - interval '16' day as varchar) and cast(current_date - interval '2' day as varchar) , visitor_id, null)) as uclicks_2w,
            count(distinct if(category = 'IMPRESSION' and date between cast(current_date - interval '23' day as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as uimpressions_3w,
            count(distinct if(category = 'CLICK' and date between cast(current_date - interval '23' day as varchar) and cast(current_date - interval '2' day as varchar) , visitor_id, null)) as uclicks_3w,
            count(distinct if(category = 'IMPRESSION' and date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar), visitor_id, null)) as uimpressions_4w,
            count(distinct if(category = 'CLICK' and date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar) , visitor_id, null)) as uclicks_4w
        from log.analyst_log_table
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '2m' %}
        where date between cast(current_date - interval '2' day - interval '2' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '3m' %}
        where date between cast(current_date - interval '2' day - interval '3' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '6m' %}
        where date between cast(current_date - interval '2' day - interval '6' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
          and object_type = '{{ object_type }}'
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and trim(search_keyword) != ''
          -- IMPRESSION 로그는 웹에서 영역별로 찍지 않고 있는 문제가 있다.
          and platform in ('IOS', 'ANDRIOD')
        group by search_keyword, object_id
        order by 1
    ),

    -- Query Info Table: qc, cc, uqc, ucc, uctr
    qinfo_t as (
        select
            search_keyword,
            count(if(category = 'PAGEVIEW', visitor_id, null)) as qc,
            count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as cc,
            100 * count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(if(category = 'PAGEVIEW', visitor_id, null)) as double) as CTR,
            -- 해당 검색을 사용한 UV를 볼 때도 사용할 수 있다.
            count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as uqc,
            count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as ucc,
            100 * count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as double) as uCTR
        from log.analyst_log_table as l
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '2m' %}
        where date between cast(current_date - interval '2' day - interval '2' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '3m' %}
        where date between cast(current_date - interval '2' day - interval '3' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '6m' %}
        where date between cast(current_date - interval '2' day - interval '6' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and trim(search_keyword) != ''
          -- platform 앱으로 제한
          and platform in ('IOS', 'ANDRIOD')
        group by search_keyword
    )

-- select count(*)
-- from (
-- select search_keyword, count(*)
-- from (
select
    click_t.search_keyword, 
    click_t.object_id as docid,
    click_t.avgRank,
    click_t.stdevRank,
    click_t.impressions,
    click_t.clicks,
    click_t.uimpressions,
    click_t.uclicks,
    array_join(array[
        cast(click_t.impressions_1w as varchar), 
        cast(click_t.impressions_2w as varchar), 
        cast(click_t.impressions_3w as varchar),
        cast(click_t.impressions_4w as varchar)
    ], ',') as impressionsList,
    array_join(array[
        cast(click_t.clicks_1w as varchar), 
        cast(click_t.clicks_2w as varchar), 
        cast(click_t.clicks_3w as varchar),
        cast(click_t.clicks_4w as varchar)
    ], ',') as clicksList,
    array_join(array[
        cast(click_t.uimpressions_1w as varchar), 
        cast(click_t.uimpressions_2w as varchar), 
        cast(click_t.uimpressions_3w as varchar),
        cast(click_t.uimpressions_4w as varchar)
    ], ',') as uimpressionsList,
    array_join(array[
        cast(click_t.uclicks_1w as varchar), 
        cast(click_t.uclicks_2w as varchar), 
        cast(click_t.uclicks_3w as varchar),
        cast(click_t.uclicks_4w as varchar)
    ], ',') as uclicksList,
    click_t.scrapCnt,
    qinfo_t.qc,
    qinfo_t.cc,
    qinfo_t.uqc,
    qinfo_t.ucc
from click_t
    left join qinfo_t on click_t.search_keyword = qinfo_t.search_keyword
-- 클릭에 참여(검색보다는)한 사용자 수가 어느정도 되는 데이터로 한정한다.
-- 표본이 어느정도 있어야 신뢰할 수 있을 것이다.
-- where qinfo_t.ucc >= 5
where qinfo_t.ucc >= {{ minimum_ucc }}
-- random sampling
order by click_t.search_keyword, click_t.uclicks desc
-- )
-- group by search_keyword
-- )


-- === 1d ===
-- qinfo_t.ucc >= 1: 813238(6502 query)
-- qinfo_t.ucc >= 5: (327 query)
-- qinfo_t.ucc >= 10: 84327(121 query)
-- === 1m ===
-- qinfo_t.ucc >= 1: (9355 query)
-- qinfo_t.ucc >= 5: (5034 query)
-- qinfo_t.ucc >= 10: (3561 query)
""")

RANKING_SQL_V3 = Template("""
with 
    -- Log Table: 사진탭 클릭
    click_t as (
        select
            search_keyword,
            object_id,
            -- 사진 피드에서의 스크랩 횟수
            count(if(category = 'SCRAP', visitor_id, null)) as scrapCnt,
            -- average Rank
            round(avg(cast(object_idx as int)), 2) as avgRank,
            round(stddev_pop(cast(object_idx as double)), 2) as stdevRank,
            -- IMPRESSION은 영역마다 로그를 남긴다.
            count(if(category = 'IMPRESSION', visitor_id, null)) as impressions,
            count(if(category = 'CLICK', visitor_id, null)) as clicks,
            100 * count(if(category = 'CLICK', visitor_id, null)) / cast(count(if(category = 'IMPRESSION', visitor_id, null)) as double) as docCTR,
            -- 문서별 UV 수를 볼 때도 사용할 수 있다.
            count(distinct if(category = 'IMPRESSION', visitor_id, null)) as uimpressions,
            count(distinct if(category = 'CLICK', visitor_id, null)) as uclicks,
            100 * count(distinct if(category = 'CLICK', visitor_id, null)) / cast(count(distinct if(category = 'IMPRESSION', visitor_id, null)) as double) as udocCTR
        from log.analyst_log_table
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '2m' %}
        where date between cast(current_date - interval '2' day - interval '2' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '3m' %}
        where date between cast(current_date - interval '2' day - interval '3' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '6m' %}
        where date between cast(current_date - interval '2' day - interval '6' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
          and object_type = '{{ object_type }}'
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and trim(search_keyword) != ''
          -- IMPRESSION 로그는 웹에서 영역별로 찍지 않고 있는 문제가 있다.
          and platform in ('IOS', 'ANDRIOD')
        group by search_keyword, object_id
        order by 1
    ),

    -- Query Info Table: qc, cc, uqc, ucc, uctr
    qinfo_t as (
        select
            search_keyword,
            count(if(category = 'PAGEVIEW', visitor_id, null)) as qc,
            count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as cc,
            100 * count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(if(category = 'PAGEVIEW', visitor_id, null)) as double) as CTR,
            -- 해당 검색을 사용한 UV를 볼 때도 사용할 수 있다.
            count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as uqc,
            count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as ucc,
            100 * count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as double) as uCTR
        from log.analyst_log_table as l
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '2m' %}
        where date between cast(current_date - interval '2' day - interval '2' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '3m' %}
        where date between cast(current_date - interval '2' day - interval '3' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '6m' %}
        where date between cast(current_date - interval '2' day - interval '6' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and trim(search_keyword) != ''
          -- platform 앱으로 제한
          and platform in ('IOS', 'ANDRIOD')
        group by search_keyword
    )

-- select count(*)
-- from (
-- select search_keyword, count(*)
-- from (
select
    click_t.search_keyword, 
    click_t.object_id as docid,
    click_t.avgRank,
    click_t.stdevRank,
    click_t.impressions,
    click_t.clicks,
    click_t.uimpressions,
    click_t.uclicks,
    click_t.scrapCnt,
    qinfo_t.qc,
    qinfo_t.cc,
    qinfo_t.uqc,
    qinfo_t.ucc
from click_t
    left join qinfo_t on click_t.search_keyword = qinfo_t.search_keyword
-- 클릭에 참여(검색보다는)한 사용자 수가 어느정도 되는 데이터로 한정한다.
-- 표본이 어느정도 있어야 신뢰할 수 있을 것이다.
-- where qinfo_t.ucc >= 5
where qinfo_t.ucc >= {{ minimum_ucc }}
-- random sampling
order by click_t.search_keyword, click_t.uclicks desc
-- )
-- group by search_keyword
-- )


-- === 1d ===
-- qinfo_t.ucc >= 1: 813238(6502 query)
-- qinfo_t.ucc >= 5: (327 query)
-- qinfo_t.ucc >= 10: 84327(121 query)
-- === 1m ===
-- qinfo_t.ucc >= 1: (9355 query)
-- qinfo_t.ucc >= 5: (5034 query)
-- qinfo_t.ucc >= 10: (3561 query)
""")

RANKING_SQL_V2 = Template("""
with 
    -- Log Table: 사진탭 클릭
    click_t as (
        select
            search_keyword,
            object_id,
            -- 사진 피드에서의 스크랩 횟수
            count(if(category = 'SCRAP', visitor_id, null)) as scrapCnt,
            -- Rank Info
            round(avg(cast(object_idx as int)), 2) as avgRank,
            round(stddev_pop(cast(object_idx as double)), 2) as stdRank,
            -- IMPRESSION은 영역마다 로그를 남긴다.
            count(if(category = 'IMPRESSION', visitor_id, null)) as qc,
            count(if(category = 'CLICK', visitor_id, null)) as cc,
            100 * count(if(category = 'CLICK', visitor_id, null)) / cast(count(if(category = 'IMPRESSION', visitor_id, null)) as double) as ctr,
            -- 문서별 UV 수를 볼 때도 사용할 수 있다.
            count(distinct if(category = 'IMPRESSION', visitor_id, null)) as uqc,
            count(distinct if(category = 'CLICK', visitor_id, null)) as ucc,
            100 * count(distinct if(category = 'CLICK', visitor_id, null)) / cast(count(distinct if(category = 'IMPRESSION', visitor_id, null)) as double) as uctr
        from log.analyst_log_table
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '3m' %}
        where date between cast(current_date - interval '2' day - interval '6' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
          and object_type = '{{ object_type }}'
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and trim(search_keyword) != ''
          -- IMPRESSION 로그는 웹에서 영역별로 찍지 않고 있는 문제가 있다.
          and platform in ('IOS', 'ANDRIOD')
        group by search_keyword, object_id
        order by 1
    ),

    -- Query Info Table: qc, cc, uqc, ucc, uctr
    qinfo_t as (
        select
            search_keyword,
            count(if(category = 'PAGEVIEW', visitor_id, null)) as qc,
            count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as cc,
            100 * count(if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(if(category = 'PAGEVIEW', visitor_id, null)) as double) as ctr,
            -- 해당 검색을 사용한 UV를 볼 때도 사용할 수 있다.
            count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as uqc,
            count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) as ucc,
            100 * count(distinct if(category = 'CLICK' and object_type = '{{ object_type }}', visitor_id, null)) / cast(count(distinct if(category = 'PAGEVIEW', visitor_id, null)) as double) as uctr
        from log.analyst_log_table as l
        -- 7 days (1 week)
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '3m' %}
        where date between cast(current_date - interval '2' day - interval '6' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and trim(search_keyword) != ''
          -- platform 앱으로 제한
          and platform in ('IOS', 'ANDRIOD')
        group by search_keyword
    )

select
    click_t.search_keyword as search_keyword,
    cast(avg(qinfo_t.qc) as int) as qc,
    cast(avg(qinfo_t.cc) as int) as cc,
    avg(qinfo_t.ctr) as ctr,
    cast(avg(qinfo_t.uqc) as int) as uqc,
    cast(avg(qinfo_t.ucc) as int) as ucc,
    avg(qinfo_t.uctr) as uctr,
    -- https://prestodb.io/docs/current/functions/aggregate.html#map-aggregate-functions
    count(object_id) as docCnt,
    CAST(map_agg(object_id, ARRAY[
        click_t.qc, 
        click_t.cc, 
        click_t.ctr, 
        click_t.uqc, 
        click_t.ucc, 
        click_t.uctr, 
        click_t.avgRank,
        click_t.stdRank,
        click_t.scrapCnt
    ]) AS json) as docInfo
from click_t
    left join qinfo_t on click_t.search_keyword = qinfo_t.search_keyword
-- 검색에 참여한 사용자 수가 10명 이상으로 한정한다. 
-- 어느정도 표본이 되어야 데이터를 볼 때 신뢰할 수 있다.
where qinfo_t.uqc >= {{ minimum_uqc }}
group by click_t.search_keyword
-- random sampling
order by rand()
limit {{ limit }}
""")

RANKING_SQL_V1 = Template("""
/*
  <<FIMXE>>
  [ ] 테이블별 기간 일치 시키기 (노출 대비 클릭이 비교 가능하도록)
  
  
  <<참고>>
  사진탭 클릭 카테고리 내 object_type 통계
  
    #	object_type	_col1
    1		19081
    2	CARD	134485
    3	CATEGORY	18 
    4	CARD_COLLECTION	71555
    5	SCRAP_BOOK	4
    6	COLLECTIONS	129374
    7	KEYWORD	1033

  [v] COLLECTIONS나 CARD_COLLECTION은 무엇? 
    - "재생정지", "재생시작" 등이 대부분이다.
    - 추후 비디오 등의 문서를 랭킹에 의미있게 반영하는 방법 고려

*/

with 
    -- Log Table: 사진탭 클릭
    click_t as (
        select *
        from log.analyst_log_table
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
        -- 사진탭 클릭 데이터로 한정
          and category = 'CLICK'
          and object_type = '{{ object_type }}'
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and search_keyword != ''
    ),
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
        -- 7 days (1 week)
        {% if period == '1d' %}
        where date between cast(current_date - interval '2' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1w' %}
        where date between cast(current_date - interval '9' day as varchar) and cast(current_date - interval '2' day as varchar)
        {% elif period == '1m' %}
        where date between cast(current_date - interval '2' day - interval '1' month as varchar) and cast(current_date - interval '2' day as varchar)
        {% endif %}
          and url_path = '{{ service_url_path }}'
          and search_keyword is not null and search_keyword != ''
        group by search_keyword
    )

select *
from (
select
    click_t.search_keyword,
    cast(avg(qinfo_t.qc) as int) as qc,
    cast(avg(qinfo_t.cc) as int) as cc,
    avg(qinfo_t.ctr) as ctr,
    cast(avg(qinfo_t.uqc) as int) as uqc,
    cast(avg(qinfo_t.ucc) as int) as ucc,
    avg(qinfo_t.uctr) as uctr,
    -- 클릭유저다양성
    count(distinct session_id) as numClickUsers,
    -- 문서id:클릭수
    transform_values(
		multimap_from_entries(
			transform(
				array_sort(array_agg(object_id)),
				x->row(x, 1)
			)
		),
		(k, v)->reduce(v, 0, (s, x)->s + x, s->s)
	) as id2clickCnt
from click_t
    left join qinfo_t on click_t.search_keyword = qinfo_t.search_keyword
-- qc > 10 질의로 제한
where qinfo_t.qc > 10
group by click_t.search_keyword
)
-- 클릭 참여자수가 너무 적으면 bias될 수 있으므로 5이상으로 제한
where numClickUsers >= 5
-- random sampling
order by rand()
limit 1000

""")

SERVICE_URL_PATH = {
    "card": "https://ohou.se/cards/feed",
    "commerce": "https://ohou.se/productions/feed",
    "project": "https://ohou.se/projects",
    "advice": "https://ohou.se/advices",
    "question": "https://ohou.se/questions",
}

SERVICE_OBJECT_TYPE = {
    "card": "CARD",
    "commerce": "PRODUCTION",
    "project": "PROJECT",
    "advice": "ADVICE",
    "question": "QUESTION",
}


def main(service, period, limit=1000):

    # SQL = RANKING_SQL_V1
    # SQL = RANKING_SQL_V2
    # SQL = RANKING_SQL_V3
    SQL = RANKING_SQL_V4

    MINIMUM_UCC = 10

    base_sql = SQL.render(
        period=period,
        object_type=SERVICE_OBJECT_TYPE[service],
        service_url_path=SERVICE_URL_PATH[service],
        minimum_ucc=MINIMUM_UCC
    )
    print(base_sql)

    # run query
    athena = TransparentSelectRows()
    res = athena.run("log", base_sql)
    
    # for chunk in res:
    #     for row in chunk:
    #         print(type(row), row)
    df = pd.DataFrame([row for chunk in res for row in chunk])

    import datetime
    DATA_CREATED_AT = datetime.datetime.today().strftime("%Y%m%d")
    mydir = f"./rdataset/{service}/{DATA_CREATED_AT}"
    if not os.path.isdir(mydir):
        os.mkdir(mydir)
    save_file = f"./rdataset/{service}/{DATA_CREATED_AT}/{service}.click.ranking.{period}.csv"
    print(f"... save as {save_file}\n")
    df.to_csv(save_file, index=False)

def run_all():
    for period in ["3m"]:
        for service in SERVICE_OBJECT_TYPE.keys():
            if service != "card":
                continue
            main(service, period)

if __name__ == "__main__":
    # res = athena.run("dump", "SELECT * FROM search.card_search_index limit 10")
    # main("card", "1m")
    run_all()
