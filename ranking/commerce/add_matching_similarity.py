import json
import sys
sys.path.append('.')

from services import commerce_dev

ES = commerce_dev

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
    analyzers_result = ES.get_analyze_result(query, analyzers=analyzers)
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
            "boosting": {
                "negative": {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "multi_match": {
                                    "fields": [
                                        "no_search_name",
                                        "no_search_name.standard",
                                        "no_search_name.no_syn"
                                    ],
                                    "minimum_should_match": "1%",
                                    "query": query,
                                    "type": "cross_fields"
                                }
                            }
                        ]
                    }
                },
                "negative_boost": 0.5,
                "positive": {
                    "function_score": {
                        # "boost_mode": "replace",
                        "boost_mode": "sum",
                        "score_mode": "sum",
                        "functions": [
                            # {
                            #     "field_value_factor": {
                            #         "field": "selling_score"
                            #     },
                            #     "weight": 1
                            # },
                            # {
                            #     "field_value_factor": {
                            #         "field": "wish_count_score"
                            #     },
                            #     "weight": 0.1
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "multi_match": {
                            #                         "fields": [
                            #                             "brand_name",
                            #                             "processed_brand_name",
                            #                             "brand_name.standard",
                            #                             "brand_name.no_syn"
                            #                         ],
                            #                         "operator": "or",
                            #                         "query": query,
                            #                         "type": "cross_fields"
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.01068615
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "multi_match": {
                            #                         "fields": [
                            #                             "name",
                            #                             "name.standard",
                            #                             "name.no_syn"
                            #                         ],
                            #                         "operator": "and",
                            #                         "query": query,
                            #                         "type": "cross_fields"
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.01396124
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "multi_match": {
                            #                         "fields": [
                            #                             "reinforcement"
                            #                         ],
                            #                         "operator": "and",
                            #                         "query": query,
                            #                         "type": "cross_fields"
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.00923405
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "multi_match": {
                            #                         "fields": [
                            #                             "reinforcement.keyword"
                            #                         ],
                            #                         "operator": "and",
                            #                         "query": query,
                            #                         "type": "cross_fields"
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.10923405
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "multi_match": {
                            #                         "fields": [
                            #                             "search_admin_categories"
                            #                         ],
                            #                         "operator": "and",
                            #                         "query": query,
                            #                         "type": "cross_fields"
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.03322062
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 2,
                            #             "should": [
                            #                 {
                            #                     "multi_match": {
                            #                         "fields": [
                            #                             "brand_name",
                            #                             "processed_brand_name",
                            #                             "brand_name.standard",
                            #                             "brand_name.no_syn"
                            #                         ],
                            #                         "operator": "or",
                            #                         "query": query,
                            #                         "type": "cross_fields"
                            #                     }
                            #                 },
                            #                 {
                            #                     "multi_match": {
                            #                         "fields": [
                            #                             "name",
                            #                             "name.standard",
                            #                             "name.no_syn"
                            #                         ],
                            #                         "operator": "and",
                            #                         "query": query,
                            #                         "type": "cross_fields"
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.00140854
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "term": {
                            #                         "sold_out": True
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "match": {
                            #                         "processed_brand_name": query
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.00617219
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "match": {
                            #                         "click_keywords": query
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.126830275
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "match": {
                            #                         "click_keywords2": query
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.126830275
                            # },
                            # {
                            #     "filter": {
                            #         "bool": {
                            #             "minimum_should_match": 1,
                            #             "should": [
                            #                 {
                            #                     "match": {
                            #                         "category_keywords": query
                            #                     }
                            #                 }
                            #             ]
                            #         }
                            #     },
                            #     "weight": 0.03322062
                            # },
                            {
                                "query": {
                                    "function_score": {
                                        "query": {
                                            "match": {
                                                "name": query,
                                            }
                                        },
                                        "script_score": {
                                            "script": {
                                                "lang": "painless",
                                                "source": "_score"
                                            }
                                        },
     			                        "boost_mode": "replace"
                                    }
                                }
                            }
                        ],
                        "query": {
                            # NOTE: 매칭유사도에 weight를 부여하기 위해서 script 쿼리를 활용한다.
                            "function_score": {
                                "boost_mode": "replace",
                                "functions": [
                                    {
                                        "script_score": {
                                            # https://www.elastic.co/guide/en/elasticsearch/reference/8.2/modules-scripting-fields.html#scripting-score
                                            "script": {
                                                "lang": "painless",
                                                "source": """
                                                0.5 * _score / (_score + 0.5)
                                                """
                                            }
                                        },
                                    },
                                ],
                                "query": {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "hide_on_feed": False
                                                }
                                            },
                                            # NOTE: 필터조건 -> 아래 검색필드 전체에서 검색어 텀이 모두 존재해야 한다.
                                            # NOTE: 일단 요 부분은 그래도 완전히 말이 안되는 것은 아니므로 잠시 두는 걸로
                                            # Cons: 검색결과없는 질의들은 대부분 이 필터에 의해 특정 텀이 아무리 봐도 없는 경우에 해당한다. (예: 파라핀 치료)
                                            # https://ohou-se.slack.com/archives/C02D2HA5T61/p1643940570954339?thread_ts=1643940431.087389&cid=C02D2HA5T61
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        # "brand_name^3",
                                                        # "brand_name.standard^3",
                                                        # "brand_name.no_syn^3",
                                                        # "name^5",
                                                        # "name.standard^5",
                                                        # "name.no_syn^5",
                                                        # "search_keywords^2",
                                                        # "search_keywords.standard^2",
                                                        # "reinforcement^2",
                                                        # "reinforcement.keyword^2",
                                                        # "search_admin_categories^0.1",
                                                        # "options^0.1"

                                                        # NOTE: 필터 쿼리 사용으로 사실상 relative weight는 의미가 없음
                                                        "brand_name",
                                                        "brand_name.standard",
                                                        "brand_name.no_syn",
                                                        "name",
                                                        "name.standard",
                                                        "name.no_syn",
                                                        "search_keywords",
                                                        "search_keywords.standard",
                                                        "reinforcement",
                                                        "reinforcement.keyword",
                                                        "search_admin_categories",
                                                        "options"
                                                    ],
                                                    "operator": "and",
                                                    # "operator": "or",
                                                    # "minimum_should_match": "60%",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            },
                                            # options^0.1에 매칭되어 좋지 않은 케이스들(예: 샤프란, 고흐 해바라기)이 있어서,
                                            # 아래와 같이 매칭 필드를 다시 줄여버림;;
                                            # TODO: 쓸데없는 느낌이 좀 있다.
                                            # =============================================================
                                            # ASIS 검색쿼리 느낌
                                            # 1. 검색문서를 "최대한" 제한하여 그나마 보수적으로 적합한 문서들을 가지고
                                            # 2. 판매점수, 클릭 등의 인기를 위주로 랭킹을 하고 있음
                                            # Pros: 편하다
                                            # Cons: 그나마 적합하다고 하는 것도 틀리면 판매 점수로 그냥 치고 올라오기 때문에 제어가 안된다.
                                            #       검색문서수가 적다.

                                            # cross_fields: term-centric
                                            # and: all terms
                                            # =============================================================
                                            # {
                                            #     "bool": {
                                            #         "must": [
                                            #             {
                                            #                 "multi_match": {
                                            #                     "fields": [
                                            #                         "brand_name^3",
                                            #                         "brand_name.standard^3",
                                            #                         "brand_name.no_syn^3",
                                            #                         "name^5",
                                            #                         "name.standard^5",
                                            #                         "name.no_syn^5",
                                            #                         "search_keywords^2",
                                            #                         "search_keywords.standard^2",
                                            #                         "reinforcement^2",
                                            #                         "reinforcement.keyword^2",
                                            #                         "search_admin_categories^0.1",
                                            #                     ],
                                            #                     "minimum_should_match": "1%",
                                            #                     "query": query,
                                            #                     "type": "cross_fields"
                                            #                 }
                                            #             }
                                            #         ]
                                            #     }
                                            # }
                                        ],
                                        # NOTE: 필터 쿼리 대신 이렇게 빼도 똑같다. 매칭 유사도를 활용하기 위해 must 쿼리로 뺀다.
                                        # TODO: 매칭유사도 단순 반영 시 "가구" 질의에 "가구 손잡이" 같은 비적합한 문서가 올라온다.
                                        "must": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "brand_name^3",
                                                        "brand_name.standard^3",
                                                        "brand_name.no_syn^3",
                                                        "name^5",
                                                        "name.standard^5",
                                                        "name.no_syn^5",
                                                        "search_keywords^2",
                                                        "search_keywords.standard^2",
                                                        "reinforcement^2",
                                                        "reinforcement.keyword^2",
                                                        # NOTE: 오류들이 좀 있어보이므로 가중치가 낮은게 맞는 것 같다.
                                                        "search_admin_categories^0.1",
                                                    ],
                                                    "minimum_should_match": "1%",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ],
                                        # NOTE: proximity 추가
                                        "should": {
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
                                                        # TODO: 평균점수 등 aggregate 할 방법없나? 그냥 weight로 조절?
                                                        "should": [
                                                            # {
                                                            #     "match_phrase": {
                                                            #         "name": {
                                                            #             "analyzer": "korean_syn",
                                                            #             "boost": 1.0,
                                                            #             "query": query,
                                                            #             "slop": 1
                                                            #         }
                                                            #     }
                                                            # },
                                                            {
                                                                "match_phrase": {
                                                                    "search_name": {
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1.0,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "brand_name": {
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 1.0,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "search_keywords": {
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 0.8,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                            {
                                                                "match_phrase": {
                                                                    "search_admin_categories": {
                                                                        "analyzer": "korean_syn",
                                                                        "boost": 0.2,
                                                                        "query": query,
                                                                        "slop": 1
                                                                    }
                                                                }
                                                            },
                                                        ]
                                                    }
                                                }
                                            }
                                        },
                                        "must_not": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "negatives.keyword"
                                                    ],
                                                    "operator": "and",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ]
                                    }
                                },
                            }
                        },
                    }
                }
            }
        },
        "size": 100,
        "sort": [
            {
                "selling": "desc"
            },
            {
                "discontinued": "asc"
            },
            {
                "sold_out": "asc"
            },
            {
                "_score": "desc"
            },
            {
                "weekly_selling_cost": "desc"
            },
            {
                "selling_score": "desc"
            },
            {
                "id": "desc"
            }
        ],
        "track_total_hits": True
    }


if __name__ == '__main__':
    generate(query='러그')