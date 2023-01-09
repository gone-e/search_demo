import json
import sys
sys.path.append('.')

FEATURESET_LIST = [
    "description.bm25",
    "keyword_list.korean.bm25",
    "nickname.bm25",
    "company.bm25",
    "prod_name.bm25",
    "prod_brand_name.bm25",
    "prod_categories.bm25",
    "decode_style.bm25",
    "decode_area.bm25",
    "decode_residence.bm25",
    "reinforcement.bm25",
    "click_keywords.bm25",
    "description.ngram.ngram",
    "keyword_list.ngram.ngram",
    "nickname.ngram.ngram",
    "company.ngram.ngram",
    "prod_name.ngram.ngram",
    "prod_brand_name.ngram.ngram",
    "prod_categories.ngram.ngram",
    "decode_style.ngram.ngram",
    "decode_area.ngram.ngram",
    "decode_residence.ngram.ngram",
    "reinforcement.ngram.ngram",
    "click_keywords.ngram.ngram",
    "description.proximity",
    "keyword_list.korean.proximity",
    "nickname.proximity",
    "company.proximity",
    "prod_name.proximity",
    "prod_brand_name.proximity",
    "prod_categories.proximity",
    "decode_style.proximity",
    "decode_area.proximity",
    "decode_residence.proximity",
    "reinforcement.proximity",
    "click_keywords.proximity",
    # "follower_count",
    # "praise_count",
    # "reply_count",
    # "scrap_count",
    # "share_count",
    # "view_count",
    # "user_card_count",
    # "created_at",
    # "has_tag",
    "is_project",
    "description.has",
    "keyword_list.korean.has",
    "nickname.has",
    "company.has",
    "prod_name.has",
    "prod_brand_name.has",
    "prod_categories.has",
    "decode_style.has",
    "decode_area.has",
    "decode_residence.has",
    "reinforcement.has",
    # "click_keywords.has",
]


def generate(query, ltr_model, top_k=300):
    request_body = {
        "from": 0,
        "query": {
            "sltr": {
                    "params": {
                        "query": query,
                    },
                    "model": ltr_model,
                    "active_features": FEATURESET_LIST,
                }
        },
        "size": top_k,
        "sort": [
          {
            "_score": "desc"
          },
          {
            "rank_value": "desc"
          }
        ],
        "track_total_hits": True,
    }

    # print(json.dumps(request_body, indent=4, ensure_ascii=False))
    return request_body
    

if __name__ == '__main__':
    # for i in get_query_info('붉은색 푸른색 커버'):
    #     print(i)
    generate(query='러그', ltr_model="card.test.v1.model-xgb")