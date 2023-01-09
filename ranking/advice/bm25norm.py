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
                                    "title.tobe^5",
                                    "title.tobe_standard^5",
                                    "title.tobe_no_syn^5",
                                    "reinforcement.tobe",
                                    "reinforcement.tobe_keyword^5",
                                    "description.tobe^1.05",
                                    "description.tobe_standard^1.05",
                                    "description.tobe_no_syn^1.05",
                                    "keywords.tobe^1.5",
                                    "keywords.tobe_standard^1.5",
                                    "keywords.tobe_no_syn^1.5",
                                    "content.tobe^1.1",
                                    "content.tobe_standard^1.1",
                                    "content.tobe_no_syn^1.1",
                                    "nickname.tobe^0.5",
                                    "nickname.tobe_standard^0.5",
                                    "nickname.tobe_no_syn^0.5",
                                    "decode_category.tobe",
                                    "decode_category.tobe_standard",
                                    "decode_category.tobe_no_syn",
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
                                    "negatives.tobe",
                                    "negatives.tobe_standard"
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