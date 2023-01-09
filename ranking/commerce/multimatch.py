import json
import sys
sys.path.append('.')


def generate(query, top_k=500):
    return {
        "from": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "fields": [
                                "brand_name^3",
                                "name^5",
                                "search_keywords^2",
                            ],
                            "minimum_should_match": "1%",
                            "query": query,
                            "type": "best_fields"  # same as max
                            # "type": "cross_fields"
                        }
                    }
                ]
            }
        },
        "size": top_k,
        # "sort": [
        #     {
        #         "selling": "desc"
        #     },
        #     {
        #         "discontinued": "asc"
        #     },
        #     {
        #         "sold_out": "asc"
        #     },
        #     {
        #         "_score": "desc"
        #     },
        #     {
        #         "weekly_selling_cost": "desc"
        #     },
        #     {
        #         "selling_score": "desc"
        #     },
        #     {
        #         "id": "desc"
        #     }
        # ],
        "track_total_hits": True
    }
    

if __name__ == '__main__':
    generate(query='러그')