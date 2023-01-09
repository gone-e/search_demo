import json
import sys
sys.path.append('.')


def generate(query, top_k=500):
    return {
        "from": 0,
        "size": top_k,
        "explain": True,
        "query": {
            "boosting": {
                "negative": {
                    "bool": {

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
                                "weight": 0.18875269
                            },
                            {
                                "field_value_factor": {
                                    "field": "sell_cnt_1_day_score"
                                },
                                "weight": 0.08964386
                            },
                            {
                                "field_value_factor": {
                                    "field": "sell_cnt_7_day_score"
                                },
                                "weight": 0.10486048
                            },
                            {
                                "field_value_factor": {
                                    "field": "sell_cnt_28_day_score"
                                },
                                "weight": 0.13914507
                            },
                            {
                                "field_value_factor": {
                                    "field": "sell_cnt_7_28_day_ratio"
                                },
                                "weight": 0.08511498
                            },
                            {
                                "field_value_factor": {
                                    "field": "wish_count_score"
                                },
                                "weight": 0.18875269
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
                                "weight": 0.01102064
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
                                "weight": 0.03199851
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
                                "weight": 0.00957737
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
                                "weight": 0.10048696
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
                                "weight": 0.02518538
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
                                "weight": 0.00294097
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
                                "weight": 0.00544530
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
                                "weight": 0.01514129
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
                                                "search_keywords_new^2",
                                                "search_keywords_new.standard^2",
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
                                                            "search_keywords_new^2",
                                                            "search_keywords_new.standard^2",
                                                            "reinforcement^2",
                                                            "reinforcement.keyword^2",
                                                            "search_admin_categories^0.1"
                                                        ],
                                                        "minimum_should_match": "1%",
                                                        "query": query,
                                                        "type": "cross_fields"
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
        "track_total_hits": False
    }
    

if __name__ == '__main__':
    generate(query='러그')