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
                        ],
                        "must": [
                            {
                                "match": {
                                    "search_keywords": query
                                }
                            },
                            {
                                "bool": {
                                    "must_not": [
                                        {
                                            "multi_match": {
                                                "fields": [
                                                    "search_keywords",
                                                    "search_keywords.standard"
                                                ],
                                                "query": query,
                                                "operator": "or"

                                            }
                                        },
                                        {
                                            "multi_match": {
                                                "fields": [
                                                    "name",
                                                    "name.standard",
                                                    "name.no_syn",
                                                    "reinforcement",
                                                    "reinforcement.keyword",
                                                    "search_admin_categories",
                                                    "click_keywords",
                                                    "click_keywords2",
                                                    "category_keywords",
                                                    "options"
                                                ],
                                                "query": query,
                                                "operator": "and"
                                            }
                                        },
                                        {
                                            "match": {
                                                "search_keywords.keyword": {
                                                    "query":query,
                                                    "operator":"and"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                "negative_boost": 0.1,
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
                                "weight": 0.1
                            },
                            {
                                "field_value_factor": {
                                    "field": "delivery_score"
                                },
                                "weight": 0.03
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