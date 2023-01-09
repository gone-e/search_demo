import json


def generate(query='러그'):

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
                    "reinforcement.keyword^1.2",
                    # shingle
                    "description.korean_shingle_22",
                    "keyword_list.korean_shingle_22",
                    "prod_name.korean_shingle_22",
                    "prod_brand_name.korean_shingle_22",
                    # "description.korean_shingle_23",
                    # "keyword_list.korean_shingle_23",
                    # "prod_name.korean_shingle_23",
                    # "prod_brand_name.korean_shingle_23",
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

    request_body = {
        "from": 0,
        "query": function_score,
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

    # print(json.dumps(request_body, indent=4, ensure_ascii=False))
    return request_body
    

if __name__ == '__main__':
    generate()