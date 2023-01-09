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
                        "filter": {
                            "bool": {
                                "minimum_should_match": 1,
                                "should": [
                                    {
                                        "term": {
                                            "userable_type": "ExpertUser"
                                        }
                                    }
                                ]
                            }
                        },
                        "weight": 0.85
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
                            "field": "praise_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "share_count_score"
                        },
                        "weight": 1
                    },
                    {
                        "field_value_factor": {
                            "field": "scrap_count_score"
                        },
                        "weight": 1
                    }
                ],
                "query": {
                    "bool": {
                        "filter": None,
                        "must": {
                            "multi_match": {
                                "fields": [
                                    "expert_name",
                                    "copyright",
                                    "description^1.05",
                                    "description.standard^1.05",
                                    "description.no_syn^1.05",
                                    "title^1.8",
                                    "title.standard^1.8",
                                    "title.no_syn^1.8",
                                    "reinforcement",
                                    "reinforcement.keyword^1.8",
                                    "nickname",
                                    "card_description^1.05",
                                    "card_description.standard^1.05",
                                    "card_description.no_syn^1.05",
                                    "decode_style",
                                    "decode_residence^1.1",
                                    "decode_area",
                                    "decode_expertise",
                                    "decode_family^1.3",
                                    "decode_family.standard^1.3",
                                    "decode_family.no_syn^1.3",
                                    "decode_agent",
                                    "company",
                                    "prod",
                                    "prod.name^1.1",
                                    "prod.name.standard^1.1",
                                    "prod.name.no_syn^1.1",
                                    "prod.search_keywords",
                                    "prod.brand"
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
        "size": top_k,
        "sort": [
            {
                "_score": "desc"
            },
            {
                "rank_value": "desc"
            },
            {
                "prod_count": "desc"
            }
        ],
        "track_total_hits": True
    }

if __name__ == '__main__':
    generate(query='러그')