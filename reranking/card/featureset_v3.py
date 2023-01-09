import sys
from tkinter import W
sys.path.append(".")
import os
from pathlib import Path
import json
import datetime
import time
import ltr
import ltr.client as client
import ltr.index as index
import ltr.helpers.movies as helpers
from myelasticsearch.featureset import FeaturesetTemplate as FTemplate
# today = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
# UNIX_TIME = int(time.time())
# today

SERVICE_INDEX = "card_search"
# FIMXE: 저장할 피쳐셋 이름 지정({service}.featureset.{version})
SERVICE = "card"
VERSION = "v3"
FEATURE_SET = f"{SERVICE}.featureset.{VERSION}"
print(FEATURE_SET)
WORK_DIR = Path(__file__).parent


client = client.ElasticClient()

TEXT_TYPE_FIELDS = [
    "description", 
    "keyword_list.korean", 
    "nickname", 
    "company",
    "prod_name",
    "prod_brand_name",
    "prod_categories",
    "decode_style",
    "decode_area",
    "decode_residence",
    "reinforcement",
    "click_keywords",
    # "negatives"       # 랭킹쿼리에서 검색문서 제한을 이미 적용
]

NGRAM_TYPE_FIELDS = [
    "description.ngram", 
    "keyword_list.ngram", 
    "nickname.ngram", 
    "company.ngram",
    "prod_name.ngram",
    "prod_brand_name.ngram",
    "prod_categories.ngram",
    "decode_style.ngram",
    "decode_area.ngram",
    "decode_residence.ngram",
    "reinforcement.ngram",
    "click_keywords.ngram",
    # "negatives"       # 랭킹쿼리에서 검색문서 제한을 이미 적용
]

def _get_match_features(suffix=".bm25", analyzer=None):
    features = []
    for field in TEXT_TYPE_FIELDS:
        name = field + suffix
        features.append(
            FTemplate.get_match_feature(name, field=field, analyzer=analyzer)
        )
    return features

def _get_match_ngram_features(suffix=".ngram", analyzer=None):
    features = []
    for field in NGRAM_TYPE_FIELDS:
        name = field + suffix
        features.append(
            FTemplate.get_match_feature(name, field=field, analyzer=analyzer)
        )
    return features

def _get_match_phrase_features(suffix=".proximity", slop=3):
    features = []
    for field in TEXT_TYPE_FIELDS:
        name = field + suffix
        features.append(
            FTemplate.get_match_phrase_feature(name, field=field, slop=slop, analyzer="korean")
        )
    return features

def _get_has_field_features(suffix=""):
    features = []
    for field in TEXT_TYPE_FIELDS:
        name = field + suffix
        features.append(
            FTemplate.get_has_field_feature(name, field=field)
        )
    return features

def main():
    features = []
    # bm25
    features += _get_match_features(suffix=".bm25")
    # TODO: ngram 수정
    # ngram
    features += _get_match_ngram_features(suffix=".ngram")
    # proximity
    features += _get_match_phrase_features(suffix=".proximity", slop=3)

    # multimatch
    # features += [
    #     # 사진설명, 태그제품, 해시태그에 모두 등장하는 경우
    #     FTemplate.get_multimatch_feature(
    #         name="desc.prod.keyword.bm25",
    #         fields=[
    #             "description.bm25_idfmaxnorm",
    #             "keyword_list.bm25_idfmaxnorm",
    #             "prod_name.bm25_idfmaxnorm",
    #             "prod_brand_name.bm25_idfmaxnorm",
    #             "prod_categories.bm25_idfmaxnorm",
    #         ],
    #         operator="and",
    #         type="most_fields"
    #     ),
    #     # 사진설명, 태그제품에 모두 등장하는 경우
    #     FTemplate.get_multimatch_feature(
    #         name="desc.prod.bm25",
    #         fields=[
    #             "description.bm25_idfmaxnorm",
    #             "prod_name.bm25_idfmaxnorm",
    #             "prod_brand_name.bm25_idfmaxnorm",
    #             "prod_categories.bm25_idfmaxnorm",
    #         ],
    #         operator="and",
    #         type="most_fields"
    #     ),
    #     # 사진설명, 해시태그에 모두 등장하는 경우
    #     FTemplate.get_multimatch_feature(
    #         name="desc.keyword.bm25",
    #         fields=[
    #             "description.bm25_idfmaxnorm",
    #             "keyword_list.bm25_idfmaxnorm",
    #         ],
    #         operator="and",
    #         type="most_fields"
    #     ),
    # ]

    # factors
    features += [
        # TODO: 과하게 반영되어 다른 피쳐의 영향력을 너무 낮게 만드는 현상(normalize 필요?)
        # FTemplate.get_field_value_factor_feature("reply_count", field="reply_count", modifier="ln1p", missing=0),
        # FTemplate.get_field_value_factor_feature("follower_count", field="follower_count", modifier="ln1p", missing=0),
        # FTemplate.get_field_value_factor_feature("praise_count", field="praise_count", modifier="ln1p", missing=0),
        # FTemplate.get_field_value_factor_feature("scrap_count", field="scrap_count", modifier="ln1p", missing=0),
        # FTemplate.get_field_value_factor_feature("view_count", field="view_count", modifier="ln1p", missing=0),
        # FTemplate.get_field_value_factor_feature("user_card_count", field="user_card_count", modifier="ln1p", missing=0),
        # FTemplate.get_decay_feature("created_at", field="created_at", decay_func="exp", origin="now", scale="7d", decay=0.8),
        # FTemplate.get_field_value_factor_feature("created_at", field="created_at_score"),

        # Popularity
        FTemplate.get_field_value_factor_feature("follower_count", field="follower_count_log", missing=0),
        FTemplate.get_field_value_factor_feature("praise_count", field="praise_count_log", missing=0),
        FTemplate.get_field_value_factor_feature("reply_count", field="reply_count_log", missing=0),
        FTemplate.get_field_value_factor_feature("scrap_count", field="scrap_count_log", missing=0),
        FTemplate.get_field_value_factor_feature("share_count", field="share_count_log", missing=0),
        FTemplate.get_field_value_factor_feature("view_count", field="view_count_log", missing=0),
        FTemplate.get_field_value_factor_feature("user_card_count", field="user_card_count_log", missing=0),
        FTemplate.get_decay_feature("created_at", field="created_at", decay_func="exp", origin="now", scale="30d", decay=0.95),
        # FTemplate.get_field_value_factor_feature("created_at", field="created_at_score"),

        FTemplate.get_field_value_factor_feature("has_tag", field="has_tag", missing=0),
        FTemplate.get_field_value_factor_feature("is_project", field="is_project", missing=0),
    ]

    # hasFields
    features += _get_has_field_features(suffix=".has")

    # 외부변수
    # features += [
    #     {
    #         "name": "qlen",
    #         "params": [
    #             "query_len"
    #         ],
    #         "template_language": "mustache",
    #         "template": {
    #             "function_score": {
    #                 "script_score": {
    #                     "script": {
    #                         "params": {
    #                             "qlen": "{{query_len}}"
    #                         },
    #                         "source": "params.qlen"
    #                     }
    #                 }
    #             }
    #         }
    #     }
    # ]


    # A feature set as a tuple, which looks a lot like JSON
    feature_set = {
        "validation": {
            "params": {
                "query": "콘센트 정리함"
            },
            "index": SERVICE_INDEX
        },
        "featureset": {
            "features": features
        }
    }

    print(json.dumps(feature_set, ensure_ascii=False, indent=4))

    # pushes the feature set to the tmdb index's LTR store (a hidden index)
    client.create_featureset(
        index=SERVICE_INDEX, 
        name=FEATURE_SET, 
        ftr_config=feature_set
    )


if __name__ == "__main__":
    main()