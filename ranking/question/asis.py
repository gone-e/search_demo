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
                            "title^5",
                            "title.standard^5",
                            "title.no_syn^5",
                            "reinforcement",
                            "reinforcement.keyword^5",
                            "description^2",
                            "description.standard^2",
                            "description.no_syn^2",
                            "keywords^1.1",
                            "keywords.standard^1.1",
                            "keywords.no_syn^1.1",
                            "comments^0.9",
                            "comments.standard^0.9",
                            "comments.no_syn^0.9",
                            "nickname^0.5",
                            "nickname.standard^0.5",
                            "nickname.no_syn^0.5"
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