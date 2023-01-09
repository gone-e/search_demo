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
                                    "expert_name.tobe",
                                    "copyright.tobe",
                                    "description.tobe^1.05",
                                    "description.tobe_standard^1.05",
                                    "description.tobe_no_syn^1.05",
                                    "title.tobe^1.8",
                                    "title.tobe_standard^1.8",
                                    "title.tobe_no_syn^1.8",
                                    "reinforcement.tobe",
                                    "reinforcement.tobe_keyword^1.8",
                                    "nickname.tobe",
                                    "card_description.tobe^1.05",
                                    "card_description.tobe_standard^1.05",
                                    "card_description.tobe_no_syn^1.05",
                                    "decode_style.tobe",
                                    "decode_residence.tobe^1.1",
                                    "decode_area.tobe",
                                    "decode_expertise.tobe",
                                    "decode_family.tobe^1.3",
                                    "decode_family.tobe_standard^1.3",
                                    "decode_family.tobe_no_syn^1.3",
                                    "decode_agent.tobe",
                                    "company.tobe",
                                    "prod_tobe",
                                    "prod_tobe.name^1.1",
                                    "prod_tobe.name.standard^1.1",
                                    "prod_tobe.name.no_syn^1.1",
                                    "prod_tobe.search_keywords",
                                    "prod_tobe.brand"
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