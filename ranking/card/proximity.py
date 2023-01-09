import json
import sys
#sys.path.append('../../')
sys.path.append('.')

from services import card_dev


def get_query_info(query):
    """
    [korean_syn]
    {'token': '붉은', 'start_offset': 0, 'end_offset': 2, 'type': 'word', 'position': 0}
    {'token': '색', 'start_offset': 2, 'end_offset': 3, 'type': 'word', 'position': 1}
    {'token': '푸른', 'start_offset': 4, 'end_offset': 6, 'type': 'word', 'position': 3}
    {'token': '색', 'start_offset': 6, 'end_offset': 7, 'type': 'word', 'position': 4}
    {'token': 'cover', 'start_offset': 8, 'end_offset': 10, 'type': 'SYNONYM', 'position': 6}
    {'token': '커버', 'start_offset': 8, 'end_offset': 10, 'type': 'word', 'position': 6}

    [korean]
    {'token': '붉은색', 'start_offset': 0, 'end_offset': 3, 'type': 'word', 'position': 0, 'positionLength': 2}
    {'token': '붉은', 'start_offset': 0, 'end_offset': 2, 'type': 'word', 'position': 0}
    {'token': '색', 'start_offset': 2, 'end_offset': 3, 'type': 'word', 'position': 1}
    {'token': '푸른색', 'start_offset': 4, 'end_offset': 7, 'type': 'word', 'position': 3, 'positionLength': 2}
    {'token': '푸른', 'start_offset': 4, 'end_offset': 6, 'type': 'word', 'position': 3}
    {'token': '색', 'start_offset': 6, 'end_offset': 7, 'type': 'word', 'position': 4}
    {'token': '커버', 'start_offset': 8, 'end_offset': 10, 'type': 'word', 'position': 6}
    """
    analyzers = ['korean_syn']
    analyzers_result = card_dev.get_analyze_result(query, analyzers=analyzers)
    tokens = analyzers_result['korean_syn']['tokens']
    return tokens

def get_n_tokens(tokens):
    n_tokens = 0
    for tok in tokens:
        if tok["type"] == "word":
            n_tokens += 1
    return n_tokens

def generate(query, top_k=500):
    n_tokens = get_n_tokens(get_query_info(query))
    return {
        "from": 0,
        "query": {
            "function_score": {
                "boost_mode": "multiply",
                "functions": [
                    {
                        "field_value_factor": {
                            "field": "created_at_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "video_duration_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "follower_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "user_card_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "scrap_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "view_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "filter": {
                            "bool": {
                                "minimum_should_match": 1,
                                "should": [
                                    {
                                        "match": {
                                            "click_keywords": query
                                        }
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
                                        "term": {
                                            "is_project": True
                                        }
                                    }
                                ]
                            }
                        },
                        "weight": 1.2
                    }
                ],
                "query": {
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
            }
        },
        "rescore": {
            "query": {
                "query_weight": 1,
                "rescore_query": {
                    "function_score": {
                        "boost_mode": "multiply",
                        "functions": [
                            {
                                "script_score": {
                                    "script": {
                                        "params": {
                                            "n_tokens": n_tokens
                                        },
                                        "source": "\n\t\t\t\t\t\t\t\t\t\t\t\tif (params['n_tokens'] == 1) {\n\t\t\t\t\t\t\t\t\t\t\t\t\treturn 0\n\t\t\t\t\t\t\t\t\t\t\t\t} else {\n\t\t\t\t\t\t\t\t\t\t\t\t\treturn 1\n\t\t\t\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t\t\t\t\t"
                                    }
                                }
                            }
                        ],
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "bool": {
                                            "must": [
                                                {
                                                    "match_phrase": {
                                                        "description": {
                                                            # "analyzer": "korean",
                                                            "analyzer": "korean_syn",
                                                            "boost": 1,
                                                            "query": query,
                                                            "slop": 1
                                                        }
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "match_phrase": {
                                                                    "keyword_list.korean": {
                                                                        # "analyzer": "korean",
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 0.5,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "prod_name": {
                                                                        # "analyzer": "korean",
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "prod_name.standard": {
                                                                        # "analyzer": "korean",
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "prod_name.no_syn": {
                                                                        # "analyzer": "korean",
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "prod_brand_name": {
                                                                        # "analyzer": "korean",
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "prod_brand_name.standard": {
                                                                        # "analyzer": "korean",
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "prod_brand_name.no_syn": {
                                                                        # "analyzer": "korean",
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
                "rescore_query_weight": 1.8,
                "score_mode": "total"
            },
            "window_size": 300
        },
        "size": top_k,
        # "sort": [
        #   {
        #     "_score": "desc"
        #   },
        #   {
        #     "rank_value": "desc"
        #   }
        # ],
        "track_total_hits": True
    }
    

if __name__ == '__main__':
    generate(query='러그')