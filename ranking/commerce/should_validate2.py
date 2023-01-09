import json
import sys
sys.path.append('.')


def generate(query, top_k=500):
    return {
        "from": 0,
        "query": {
            "bool": {
                # NOTE: should query 들은 summation 방식이다.
                "should": [
                    # {
                    #     "multi_match": {
                    #         "fields": [
                    #             "brand_name^3",
                    #             "name^5",
                    #             "search_keywords^2",
                    #         ],
                    #         "minimum_should_match": "1%",
                    #         "query": query,
                    #         "type": "best_fields"  # same as max
                    #         # "type": "cross_fields"
                    #     }
                    # }
                    {
                        "match": {
                            "name": {
                                "query": query,
                                "_name": "name",
                            }
                        }
                    },
                    {
                        "match": {
                            "brand_name": {
                                "query": query,
                                "_name": "brand_name",
                            }
                        }
                    },
                    {
                        "match": {
                            "search_admin_categories": {
                                "query": query,
                                "_name": "search_admin_categories",
                            }
                        }
                    },
                    {
                        "match": {
                            "category_keywords": {
                                "query": query,
                                "_name": "category_keywords",
                            }
                        }
                    }
                ]
            }
        },
        "size": top_k,
        "track_total_hits": True
    }
    

if __name__ == '__main__':
    generate(query='러그')