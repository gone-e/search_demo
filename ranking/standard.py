import json
from pprint import pprint
import sys
from tkinter import W
# 상위 디렉토리 인식
sys.path.append('.')
from myelasticsearch.query import ESQuery, delete_none
from myelasticsearch.function import ESFunction


def get_query_features(query):
    pass

def generate(query):
    """ Structure
    rank_score = function_score(
    	qds(field, query, weight=0.2),
    	qds(field, query, weight=0.1),
      ...
    	feature_func(field, weight=0.05, "sigmoid")
    	feature_func(field, weight=0.05, "sigmoid")
    	...
    	negative_filter(field),
    	positive_filter(field),
    	mode="sum"
    )
    """

    boost_functions = [
        {
            "filter": {
                "bool": {
                    "minimum_should_match": 1,
                    "should": [
                        {
                            "match": {"click_keywords": query}
                        }
                    ]
                }
            },
            "weight": 2.56
        },
        {
            "filter": {
                "bool": {
                    "minimum_should_match": 1,
                    "should": [
                        {
                            "term": {"is_project": True}
                        }
                    ]
                }
            },
            "weight": 1.2
        }
    ]

    bool_query = {
        "bool": {
            "filter": [
                {
                    "terms": {
                        "userable_type": [
                            "SalesUser",
                            "ExpertUser",
                            "NormalUser"
                        ]
                    }
                }
            ],
            "must_not": {
              "multi_match": {
                "fields": [
                  "negatives",
                  "negatives.standard"
                ],
                "operator": "and",
                "query": query,
                "type": "cross_fields"
              }
            }
        }
    }

    main_query = ESQuery._function_score(
        query=ESQuery._bool(
            must=ESQuery._multi_match(
                query=query,
                fields=[
                    "description",
                    "keyword_list.korean^1.2",
                    "nickname^0.9",
                    "company",
                    "prod_name^0.43",
                    "prod_name.standard^0.43",
                    "prod_name.no_syn^0.43",
                    "prod_brand_name^0.45",
                    "prod_brand_name.standard^0.45",
                    "prod_brand_name.no_syn^0.45",
                    "prod_categories",
                    "decode_style",
                    "decode_area^1.15",
                    "decode_residence^1.25",
                    "reinforcement",
                    "reinforcement.keyword^1.2"
                ]
            )
            # TODO: 여러개 match query로 분절
            # must=[
            #     ESQuery._match(field="description", query=query),
            # ]
        ),
        functions=[
            ESFunction._field_value_factor(field="created_at_score"),
            ESFunction._field_value_factor(field="video_duration_score"),
            ESFunction._field_value_factor(field="follower_score"),
            ESFunction._field_value_factor(field="user_card_count_score"),
            ESFunction._field_value_factor(field="scrap_score"),
            ESFunction._field_value_factor(field="view_count_score"),
        ]

    )

    request_body = {
        "from": 0,
        "query": main_query,
        # "rescore": rescore_query,
        "size": 20,
        "sort": [
          {
            "_score": "desc"
          },
          {
            "rank_value": "desc"
          }
        ],
        "track_total_hits": True,
    }

    pprint(request_body)
    return request_body

if __name__ == '__main__':
    generate(query="러그")