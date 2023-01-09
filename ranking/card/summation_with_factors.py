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
                # "boost_mode": "multiply",
                # "functions": [
                #     {
                #         "field_value_factor": {
                #             "field": "created_at_score"
                #         },
                #         "weight": 1
                #     },
                #     {
                #         "field_value_factor": {
                #             "field": "video_duration_score"
                #         },
                #         "weight": 1
                #     },
                #     {
                #         "field_value_factor": {
                #             "field": "follower_score"
                #         },
                #         "weight": 1
                #     },
                #     {
                #         "field_value_factor": {
                #             "field": "user_card_count_score"
                #         },
                #         "weight": 1
                #     },
                #     {
                #         "field_value_factor": {
                #             "field": "scrap_score"
                #         },
                #         "weight": 1
                #     },
                #     {
                #         "field_value_factor": {
                #             "field": "view_count_score"
                #         },
                #         "weight": 1
                #     },
                #     {
                #         "filter": {
                #             "bool": {
                #                 "minimum_should_match": 1,
                #                 "should": [
                #                     {
                #                         "match": {
                #                             "click_keywords": query
                #                         }
                #                     }
                #                 ]
                #             }
                #         },
                #         "weight": 2.56
                #     },
                #     {
                #         "filter": {
                #             "bool": {
                #                 "minimum_should_match": 1,
                #                 "should": [
                #                     {
                #                         "term": {
                #                             "is_project": True
                #                         }
                #                     }
                #                 ]
                #             }
                #         },
                #         "weight": 1.2
                #     }
                # ],
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
                                    "reinforcement.keyword^1.2",
                                    # NOTE: click_keywords 추가 (평균점수면 흠)
                                    # 안좋은 케이스: 냉장고
                                    # "click_keywords^2.5"
                                ],
                                "operator": "and",
                                "query": query,
                                "type": "most_fields"
                            }
                        },
                        # NOTE: match_phrase를 rescore 방식이 아닌 랭킹에 직접 반영
                        # NOTE: 동의어 효과를 확인 후, 동의어 매칭도 허용하는 방식으로 반영
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
                                            {
                                                "match_phrase": {
                                                    "description": {
                                                        "analyzer": "korean_syn",
                                                        "boost": 1,
                                                        "query": query,
                                                        "slop": 1
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase": {
                                                    "keyword_list.korean": {
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
                                                        "analyzer": "korean_syn",
                                                        "boost": 1,
                                                        "query": query,
                                                        "slop": 1
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase": {
                                                    "prod_categories": {
                                                        "analyzer": "korean_syn",
                                                        "boost": 0.5,
                                                        "query": query,
                                                        "slop": 1
                                                    }
                                                }
                                            },
                                            # TODO: 부분매칭도 점수 주기(minimum_should_match %, length)
                                            {
                                                "match_phrase": {
                                                    "click_keywords": {
                                                        "analyzer": "korean_syn",
                                                        "boost": 1.5,
                                                        "query": query,
                                                        "slop": 1
                                                    }
                                                }
                                            },

                                            # {
                                            #     "bool": {
                                            #         "must": [
                                            #             {
                                            #                 "match_phrase": {
                                            #                     "description": {
                                            #                         "analyzer": "korean_syn",
                                            #                         "boost": 1,
                                            #                         "query": query,
                                            #                         "slop": 1
                                            #                     }
                                            #                 }
                                            #             },
                                            #             {
                                            #                 "bool": {
                                            #                     "should": [
                                            #                         {
                                            #                             "match_phrase": {
                                            #                                 "keyword_list.korean": {
                                            #                                     "analyzer": "korean_syn",
                                            #                                     "boost": 0.5,
                                            #                                     "query": query,
                                            #                                     "slop": 1
                                            #                                 }
                                            #                             }
                                            #                         },
                                            #                         {
                                            #                             "match_phrase": {
                                            #                                 "prod_name": {
                                            #                                     "analyzer": "korean_syn",
                                            #                                     "boost": 1,
                                            #                                     "query": query,
                                            #                                     "slop": 1
                                            #                                 }
                                            #                             }
                                            #                         },
                                            #                         {
                                            #                             "match_phrase": {
                                            #                                 "prod_brand_name": {
                                            #                                     "analyzer": "korean_syn",
                                            #                                     "boost": 1,
                                            #                                     "query": query,
                                            #                                     "slop": 1
                                            #                                 }
                                            #                             }
                                            #                         },
                                            #                         {
                                            #                             "match_phrase": {
                                            #                                 "prod_categories": {
                                            #                                     "analyzer": "korean_syn",
                                            #                                     "boost": 1,
                                            #                                     "query": query,
                                            #                                     "slop": 1
                                            #                                 }
                                            #                             }
                                            #                         },
                                            #                     ]
                                            #                 }
                                            #             }
                                            #         ]
                                            #     }
                                            # }


                                        ]
                                    }
                                }
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
                },
                # TODO: description 존재여부 없으면 패널티
                # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-exists-query.html
                # TODO: 해시태그 개수가 상품개수나 설명에 비해 너무 많으면 패널티?
                # TODO: view count가 0인 관련성 높은 문서들이 너무 많은 문제?

                # TODO: score의 scale이 좀 왔다갔다인데, scale에 따라 factors의 점수 scale이 조정될 수 있도록 하는방법? ratio?
                # 예: 냉장고 -> 한 단어는 점수가 더 반영되는 느낌이고
                # 여러 단어 + 근접도 점수까지 있는 경우에는 점수가 덜 반영되는 느낌이고 왔다갔다함

                # NOTE: _score + 1.0을 했는데 2.0 이상이 더해지고 하는 동작을 봐서는, 각 매칭 필드에서 나오는 _score를 조작하는 느낌이다...
                # NOTE: _score * 2.0은 또 비슷하네..
                # NOTE: view_count_score를 리턴해도 1인데 1.9로 바뀌는..
                # NOTE: 아래거를 _score로 리턴하고 지우기만해도 1.9121 -> 3.65가 되는 이상 -> replace를 반드시써줘야햔다...!
                # 해결!!!
                "script_score": {
                    # https://www.elastic.co/guide/en/elasticsearch/reference/8.2/modules-scripting-fields.html#scripting-score
                    "script": {
                        "lang": "painless",
                        "source": """
                        0.75 * _score / (_score + 0.5)
                        + 0.04 * Math.log(1 + doc['scrap_count'].value) / (Math.log(1 + doc['scrap_count'].value) + 0.5)
                        + 0.05 * Math.log(1 + doc['view_count'].value) / (Math.log(1 + doc['view_count'].value) + 0.5)
                        + 0.04 * doc['created_at_score'].value / (doc['created_at_score'].value + 0.3)
                        + 0.03 * doc['follower_score'].value / (doc['follower_score'].value + 0.3)
                        + 0.04 * Math.log(1 + doc['reply_count'].value) / (Math.log(1 + doc['reply_count'].value) + 0.5)
                        + 0.04 * Math.log(1 + doc['share_count'].value) / (Math.log(1 + doc['share_count'].value) + 0.5)
                        """
                        # 매칭유사도 -> 0 ~ 1
                        # 나머지 factors -> 0 ~ 1.5
                        # + 0.05 * doc['scrap_score'].value * doc['view_count_score'].value
                        # + 0.08 * doc['created_at_score'].value * doc['view_count_score'].value
                        # + 0.05 * doc['created_at_score'].value * doc['scrap_score'].value

                        # + 0.1 * doc['view_count_score'].value * _score
                        # + 0.1 * doc['video_duration_score']
                        # + 0.1 * doc['user_card_count_score']
                    }
                },
                "boost_mode": "replace"
            }
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