import json
import sys
sys.path.append('.')

def generate(query, top_k=500):
    return {
        "from": 0,
        "query": {
            "bool": {
                "filter": None,
                "must": {
                    "multi_match": {
                        "fields": [
                            "title.tobe^5",
                            "title.tobe_standard^5",
                            "title.tobe_no_syn^5",
                            "reinforcement.tobe",
                            "reinforcement.tobe_keyword^5",
                            "description.tobe^2",
                            "description.tobe_standard^2",
                            "description.tobe_no_syn^2",
                            "keywords.tobe^1.1",
                            "keywords.tobe_standard^1.1",
                            "keywords.tobe_no_syn^1.1",
                            "comments.tobe^0.9",
                            "comments.tobe_standard^0.9",
                            "comments.tobe_no_syn^0.9",
                            "nickname.tobe^0.5",
                            "nickname.tobe_standard^0.5",
                            "nickname.tobe_no_syn^0.5"
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