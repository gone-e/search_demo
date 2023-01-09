import json
import sys
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
                        "boost_mode": "replace",
                        # NOTE: 매칭유사도 반영을 위해 임시로 풀어본다.
                        # "boost_mode": "sum",
                        "functions": [
                            {
                                "field_value_factor": {
                                    "field": "selling_score"
                                },
                                "weight": 1
                            },
                            {
                                "field_value_factor": {
                                    "field": "wish_count_score"
                                },
                                "weight": 0.1
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "brand_name",
                                                        "processed_brand_name",
                                                        "brand_name.standard",
                                                        "brand_name.no_syn"
                                                    ],
                                                    "operator": "or",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.01068615
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "name",
                                                        "name.standard",
                                                        "name.no_syn"
                                                    ],
                                                    "operator": "and",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.01396124
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "reinforcement"
                                                    ],
                                                    "operator": "and",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.00923405
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "reinforcement.keyword"
                                                    ],
                                                    "operator": "and",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.10923405
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "search_admin_categories"
                                                    ],
                                                    "operator": "and",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.03322062
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 2,
                                        "should": [
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "brand_name",
                                                        "processed_brand_name",
                                                        "brand_name.standard",
                                                        "brand_name.no_syn"
                                                    ],
                                                    "operator": "or",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            },
                                            {
                                                "multi_match": {
                                                    "fields": [
                                                        "name",
                                                        "name.standard",
                                                        "name.no_syn"
                                                    ],
                                                    "operator": "and",
                                                    "query": query,
                                                    "type": "cross_fields"
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.00140854
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "term": {
                                                    "sold_out": True
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "match": {
                                                    "processed_brand_name": query
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.00617219
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
                                "weight": 0.126830275
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "match": {
                                                    "click_keywords2": query
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.126830275
                            },
                            {
                                "filter": {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "match": {
                                                    "category_keywords": query
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.03322062
                            },
                            {
                                "filter": {
                                    "bool": {
                                        # "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "match_phrase": {
                                                    "name": {
                                                        "analyzer": "korean_syn",
                                                        "boost": 1.0,
                                                        "query": query,
                                                        "slop": 1
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                "weight": 0.03322062
                                # "weight": 0.1
                            }
                        ],
                        "query": {
                            "bool": {
                                "filter": [
                                    {
                                        "term": {
                                            "hide_on_feed": False
                                        }
                                    },
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
                                                "search_admin_categories^0.1",
                                                "options^0.1"
                                            ],
                                            "operator": "and",
                                            "query": query,
                                            "type": "cross_fields"
                                        }
                                    },
                                    {
                                        "bool": {
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
                                                            "search_admin_categories^0.1"
                                                        ],
                                                        "minimum_should_match": "1%",
                                                        "query": query,
                                                        "type": "cross_fields"
                                                        # 너무 적은 검색결과수(예: 파라핀 치료)
                                                        # "operator": "or",
                                                        # term centric method -> 그나마 검색결과수 문제를 보완하기 위한 것인가?
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ],
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
                        "score_mode": "sum"
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