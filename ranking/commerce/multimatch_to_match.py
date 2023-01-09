import json
import sys
sys.path.append('.')


def generate(query, top_k=500):
    return {
        "from": 0,
        "query": {
            "dis_max": {
                "queries": [
                    {
                        "match": {
                            "brand_name": {
                                "query": query,
                                "minimum_should_match": "1%",
                                "boost": 3,
                            }
                        },
                        "match": {
                            "name": {
                                "query": query,
                                "minimum_should_match": "1%",
                                "boost": 5,
                            }
                        },
                        "match": {
                            "search_keywords": {
                                "query": query,
                                "minimum_should_match": "1%",
                                "boost": 2,
                            }
                        },
                    }
                ],
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