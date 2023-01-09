import json
import sys
sys.path.append('.')

def generate(query, top_k=500):
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
                            "field": "view_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "reply_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "scrap_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "praise_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "share_count_score"
                        },
                        "weight": 1
                    }
                ],
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "bool": {
                                    "must_not": [
                                        {
                                            "term": {
                                                "userable_type": "InactiveUser"
                                            }
                                        }
                                    ]
                                }
                            }
                        ],
                        "must": {
                            "multi_match": {
                                "fields": [
                                    "title^5",
                                    "title.standard^5",
                                    "title.no_syn^5",
                                    "reinforcement",
                                    "reinforcement.keyword^5",
                                    "description^1.05",
                                    "description.standard^1.05",
                                    "description.no_syn^1.05",
                                    "keywords^1.5",
                                    "keywords.standard^1.5",
                                    "keywords.no_syn^1.5",
                                    "content^1.1",
                                    "content.standard^1.1",
                                    "content.no_syn^1.1",
                                    "nickname^0.5",
                                    "nickname.standard^0.5",
                                    "nickname.no_syn^0.5",
                                    "decode_category",
                                    "decode_category.standard",
                                    "decode_category.no_syn",
                                    "company"
                                ],
                                "operator": "and",
                                "query": query,
                                "type": "cross_fields"
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
        "size": top_k,
        "sort": [
            {
                "_score": "desc"
            }
        ],
        "track_total_hits": True
    }


if __name__ == '__main__':
    generate(query='러그')