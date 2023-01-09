import json
import sys
#sys.path.append('../../')
sys.path.append('.')

from services import card_dev



def generate(query, top_k=500):
    return {
        "from": 0,
        "query": {
            "match_phrase": {
                "description": {
                    # "analyzer": "korean",
                    "analyzer": "korean_syn",
                    "boost": 1,
                    "query": query,
                    "slop": 0
                }
            }
        },
        "size": top_k,
        "track_total_hits": True
    }
    

if __name__ == '__main__':
    generate(query='러그')