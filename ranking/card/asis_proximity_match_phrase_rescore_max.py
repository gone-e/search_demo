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
    analyzers_result = card_dev.get_query_analyze_result(query, analyzers=analyzers)
    tokens = analyzers_result['korean_syn']['tokens']
    return tokens

def get_n_tokens(tokens):
    return len(set([x['position'] for x in tokens]))

def generate(query, top_k=500):

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
                    # 검색 유저는 사진 설명, 평수 등 인테리어, 제품 등을 검색하려는 니즈가 있으므로 해당 부분이 모두 recall로 올라와줘야함
                    # TODO: 다만 prod_name과 같은 것은 형태소, standard, no_syn(검색 시에는 동의어 없이) 이걸 다써야하는지는 잘 모르겠음.
                    "fields": [
                        "description",
                        # "keyword_list.korean^0.8",
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
                        # "reinforcement.keyword^1.2",
                    ],
                    # TODO: 'OR' 검색으로 변경, 단 보강어(컨텐츠 보강어 -> 사진ID 별로)는 ?
                    # TODO: 보강어 키워드 타입은 text 타입으로 검색되면 안됨
                    # 키워드 매칭 -> 점수 추가 상승으로
                    # TODO: 키워드, 닉네임 확인 (이거 부스팅을 해줘도 되는 길이와 다양성인지)
                    # TODO: 이거 미니멈 쓰게 되면 동의어 필드는 더 ratio가 낮아지는 문제가 있다...
                    "operator": "and",
                    # "operator": "or",
                    # "minimum_should_match": "30%",
                    # "minimum_should_match": "60%",
                    "query": query,
                    "type": "most_fields"
                }
            },
            # "should": {
            #     "multi_match": {
            #         "fields": [
            #             "description",
            #             "keyword_list",
            #             "prod_name",
            #             "prod_brand_name",
            #         ],
            #         "query": query,
            #         # same as `match_phrase` with `best_fields(max)`
            #         "type": "phrase"
            #     }
            # },
            # "should": [
            #     # {"match_phrase": {"description": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     # {"match_phrase": {"keyword_list.korean": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     # {"match_phrase": {"prod_name.no_syn": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     # {"match_phrase": {"prod_name_brand_name.no_syn": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     {"match_phrase": {"description": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     {"match_phrase": {"keyword_list.korean": {"query": query, "slop": 1, "analyzer": "korean", "boost": 0.5}}},
            #     {"match_phrase": {"prod_name": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     {"match_phrase": {"prod_name.standard": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     {"match_phrase": {"prod_name.no_syn": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     {"match_phrase": {"prod_brand_name": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     {"match_phrase": {"prod_brand_name.standard": {"query": query, "slop": 1, "analyzer": "korean"}}},
            #     {"match_phrase": {"prod_brand_name.no_syn": {"query": query, "slop": 1, "analyzer": "korean"}}},
            # ],
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
# {
# 	'error': {
# 		'root_cause': [
# 			{
# 				'type': 'parse_exception',
# 				'reason': 'failed to parse [multi_match] query type [crosss_fields]. unknown type.'
# 			}
# 		],
# 		'type': 'x_content_parse_exception',
# 		'reason': '[1:1445] [bool] failed to parse field [must_not]',
# 		'caused_by': {
# 			'type': 'parse_exception',
# 			'reason': 'failed to parse [multi_match] query type [crosss_fields]. unknown type.'
# 		}
# 	},
# 	'status': 400
# }

    # https://www.elastic.co/guide/en/elasticsearch/reference/current/filter-search-results.html#query-rescorer

    tokens = get_query_info(query)
    n_tokens = get_n_tokens(tokens)
    # match를 통해 recall을 높이고
    # -> 근접도와 인기도를 반영
    my_slop = 1 # 보수적으로

    # rescore(
    #     window_size=300, 
    #     score_mode="total"
    #     query_weight=1.0,
    #     rescore_query=functionscore(
    #        boost_mode= 
    #        functions=myfunctions,
    #        query=boolquery(
    #            should=boolquery(
    #               must=[
    #                  matchquery(), 
    #                  matchquery(), 
    #                  matchquery(), 
    #               ]
    #               boolquery(
    #                  hould=[
    #                 ]
    #               )
    #            )
    #        )

    #     )
    # )
    rescore_query = {
        "window_size": 300,
        "query": {
            # query_weight * `query` + rescore_weight * `rescore`
            # (query_weight * `query` + rescore_weight * `rescore`) / (query_weight + rescore_weight)
            # 0점수.
            # 300개 -> 근접도 매칭 문서() / 아닌 문서(asis -> 점수하락)
            "score_mode": "total",
            "query_weight": 1.0,
            "rescore_query_weight": 1.8,
            "rescore_query": {
                "function_score": {
                    "boost_mode": "multiply",
                    "functions": [
                        {
                            # 1term 시 0, 그 외엔 1
                            "script_score" : {
                                "script": {
                                    "params": {
                                            'n_tokens': n_tokens,
                                    },
                                    "source": """
                                    if (params['n_tokens'] == 1) {
                                        return 0
                                    } else {
                                        return 1
                                    }
                                    """
                                }
                            }
                        }
                    ],
                    # relevance = f(qds, prox, query features, doc features)
                    #           = rank(qds, mtr) + rerank(features)  시의성/이슈성/일반 등(recency)/운영성/쿼리 주제,문서주제
                    # similarity <- 색인할때 weight ,정규화된 idf, 텀길이
                    # bm25 정규화 
                    # cutbyqds=4096 -> 다른피쳐조합 (현재는 전체문서를 보고 pruning)
                    # prox
                    # 완전매칭 1.0, 순서바뀜0.7, ... (0,1) 정규화
                    # 사진
                    "query": {
                        "bool": {
                            # e(q, d)
                            # TODO: 이렇게 should 를 하면, 하나도 안맞는 경우에는 boost가 0일까?
                            "should": [
                                {
                                    "bool" : {
                                        "must": [
                                            # substitution 
                                            # TODO: korean_syn? 뭔가 여러개 match_phrase 구성 후에 정규화하는 느낌(예: 침대커버)
                                            {"match_phrase": {"description": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                            {
                                                "bool": {
                                                    "should": [
                                                        {"match_phrase": {"keyword_list.korean": {"query": query, "slop": my_slop, "analyzer": "korean", "boost": 0.5}}},
                                                        {"match_phrase": {"prod_name": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                                        {"match_phrase": {"prod_name.standard": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                                        {"match_phrase": {"prod_name.no_syn": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                                        {"match_phrase": {"prod_brand_name": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                                        {"match_phrase": {"prod_brand_name.standard": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                                        {"match_phrase": {"prod_brand_name.no_syn": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                                    ]
                                                }
                                            }
                                        ]
                                    },
                                },
                                # {
                                #     "bool" : {
                                #         "should": [
                                #             {"match_phrase": {"prod_brand_name": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                #             {"match_phrase": {"prod_brand_name.standard": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                #             {"match_phrase": {"prod_brand_name.no_syn": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
                                #         ]
                                #     },
                                # }
                                # "reinforcement.keyword^1.2",
                            ]
                            # "should": {
                            #     "multi_match": {
                            #         "fields": [
                            #             "description",
                            #             "keyword_list.korean",
                            #             "prod_name",
                            #             "prod_name.standard",
                            #             "prod_name.no_syn",
                            #             "prod_brand_name",
                            #             "prod_brand_name.standard",
                            #             "prod_brand_name.no_syn",
                            #         ],
                            #         "query": query,
                            #         # same as `match_phrase` with `best_fields(max)`
                            #         "type": "best_fields"
                            #     }
                            # }
                        }
                    }
                }
            },
        }
    }

    # my_slop = 1 # 보수적으로
    # # my_slop = 2
    # rescore_query = [
    #     # 상위 K개 문서에 대해서
    #     {
    #         "window_size": 300,
    #         "query": {
    #             # query_weight * `query` + rescore_weight * `rescore`
    #             # TODO: 이 경우 rescore이 0점이면 원점수만 0.5배로 깎인다. 따라서 건들지말자
    #             "score_mode": "total",
    #             "query_weight": 1.0,
    #             "rescore_query_weight": 1.8,
    #             "rescore_query": {
    #                 "bool": {
    #                     "should": [
    #                         {"match_phrase": {"description": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
    #                         {"match_phrase": {"keyword_list.korean": {"query": query, "slop": my_slop, "analyzer": "korean", "boost": 0.5}}},
    #                         {"match_phrase": {"prod_name": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
    #                         {"match_phrase": {"prod_name.standard": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
    #                         {"match_phrase": {"prod_name.no_syn": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
    #                         {"match_phrase": {"prod_brand_name": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
    #                         {"match_phrase": {"prod_brand_name.standard": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
    #                         {"match_phrase": {"prod_brand_name.no_syn": {"query": query, "slop": my_slop, "analyzer": "korean"}}},
    #                         # "reinforcement.keyword^1.2",
    #                     ]
    #                 }
    #             },
    #         }
    #     },
    #     # # 상위 M(<=K)개 문서에 대해서
    #     # {
    #     #     "window_size": 1000,
    #     #     "query": {
    #     #         # query_weight * `query` + rescore_weight * `rescore`
    #     #         "score_mode": "total",
    #     #         "query_weight": 0.5,
    #     #         "rescore_query_weight": 2.0,
    #     #         "rescore_query": {
    #     #             "bool": {
    #     #                 "should": [
    #     #                     {"match_phrase": {"description": {"query": query, "slop": 1, "analyzer": "korean"}}},
    #     #                     {"match_phrase": {"keyword_list.korean": {"query": query, "slop": 1, "analyzer": "korean"}}},
    #     #                     {"match_phrase": {"prod_name.no_syn": {"query": query, "slop": 1, "analyzer": "korean"}}},
    #     #                     {"match_phrase": {"prod_name_brand_name.no_syn": {"query": query, "slop": 1, "analyzer": "korean"}}},
    #     #                     # {"match": {"prod_name_brand_name.no_syn": {"query": query, "slop": 1, "analyzer": "korean"}}},
    #     #                     # "reinforcement.keyword^1.2",
    #     #                 ]
    #     #             }
    #     #         },
    #     #     }
    #     # },
    # ]
    # print(json.dumps(rescore_query))

    # TODO: rank_value는 최근에 좋은 사진 등 최신성,인기도를 반영하려는

    function_score = {
        "function_score": {
            "boost_mode": "multiply",
            "functions": boost_functions,
            "query": bool_query,
        }
    }

    # TODO: 검색결과반환 문서 수 차이
    # TODO: function_score 부분의 인기도는 rescore 에 포함
    # TODO: most_fields, and ->
    request_body = {
        "from": 0,
        "query": function_score,
        # "query": bool_query,
        "rescore": rescore_query,
        "size": top_k,
        # Cannot use [sort] option in conjunction with [rescore]
        # TODO: rank_value로 한번더 sort 하고 싶다면 multiple rescore query를 사용
        # "sort": [
        #     {
        #         "_score": "desc"
        #     },
        #     {
        #         "rank_value": "desc"
        #     }
        # ],
        "track_total_hits": True,
    }

    # print(json.dumps(request_body, indent=4, ensure_ascii=False))
    return request_body
    

if __name__ == '__main__':
    # for i in get_query_info('붉은색 푸른색 커버'):
    #     print(i)
    generate(query='러그')