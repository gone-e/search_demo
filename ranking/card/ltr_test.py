import json
import sys
sys.path.append('.')


def generate(query, ltr_model, top_k=300):

    boost_functions = [
        {
            "field_value_factor": {"field": "created_at_score"},
            "weight": 1
        },
        {
            "field_value_factor": {"field": "video_duration_score"},
            "weight": 1
        },
        {
            "field_value_factor": {"field": "follower_score"},
            "weight": 1
        },
        {
            "field_value_factor": {"field": "user_card_count_score"},
            "weight": 1
        },
        {
            "field_value_factor": {"field": "scrap_score"},
            "weight": 1
        },
        {
            "field_value_factor": {"field": "view_count_score"},
            "weight": 1
        },
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
            "must": {
              "multi_match": {
                "fields": [
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
                ],
                "operator": "and",
                "query": query,
                "type": "most_fields"
              }
            },
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

    function_score = {
        "function_score": {
            "boost_mode": "multiply",
            "functions": boost_functions,
            "query": bool_query,
        }
    }

    rescore_query = {
        "window_size": 1000,
        "query": {
            # query_weight * `query` + rescore_weight * `rescore`
            # (query_weight * `query` + rescore_weight * `rescore`) / (query_weight + rescore_weight)
            # 0점수.
            # 300개 -> 근접도 매칭 문서() / 아닌 문서(asis -> 점수하락)
            "score_mode": "total",
            "query_weight": 0.5,
            "rescore_query_weight": 2.0,
            # "query_weight": 0.0,
            # "rescore_query_weight": 1.0,
            "rescore_query": {
                "sltr": {
                    "params": {
                        "query": query,
                    },
                    "model": ltr_model,
                }
            }
        }
    }

    request_body = {
        "from": 0,
        "query": function_score,
        # "query": {
        #     "match_all": {}
        # },
        "size": top_k,
        "rescore": rescore_query,
        # "sort": [
        #   {
        #     "_score": "desc"
        #   },
        #   {
        #     "rank_value": "desc"
        #   }
        # ],
        "track_total_hits": True,
    }

    # print(json.dumps(request_body, indent=4, ensure_ascii=False))
    return request_body
    

if __name__ == '__main__':
    # for i in get_query_info('붉은색 푸른색 커버'):
    #     print(i)
    generate(query='러그', ltr_model="card.test.v1.model-xgb")