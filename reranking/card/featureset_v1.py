import sys
sys.path.append(".")
import os
from pathlib import Path
import json
import ltr
import ltr.client as client
import ltr.index as index
import ltr.helpers.movies as helpers
from myelasticsearch.featureset import FeaturesetTemplate as FTemplate

SERVICE_INDEX = "card_search"
# FIMXE: 저장할 피쳐셋 이름 지정({service}.{phase}.{version})
FEATURE_SET = "card.test.v1"
WORK_DIR = Path(__file__).parent


client = client.ElasticClient()


# A feature set as a tuple, which looks a lot like JSON
# TODO: 기존 피쳐셋을 기본으로
feature_set = {
    "validation": {
        "params": {
            "query": "콘센트 정리함"
        },
        "index": SERVICE_INDEX
    },
    "featureset": {
        "features": [
            FTemplate.get_match_feature("description.bm25", field="description.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("keyword_list.bm25", field="keyword_list.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("nickname.bm25", field="nickname.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("company.bm25", field="company.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("prod_name.bm25", field="prod_name.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("prod_brand_name.bm25", field="prod_brand_name.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("prod_categories.bm25", field="prod_categories.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("decode_style.bm25", field="decode_style.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("decode_area.bm25", field="decode_area.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("decode_residence.bm25", field="decode_residence.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("reinforcement.bm25", field="reinforcement.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("click_keywords.bm25", field="click_keywords.bm25_idfmaxnorm"),
            FTemplate.get_match_feature("negatives.bm25", field="negatives.bm25_idfmaxnorm"),

            FTemplate.get_field_value_factor_feature("reply_count", field="reply_count", modifier="ln1p"),
            FTemplate.get_field_value_factor_feature("follower_count", field="follower_count", modifier="ln1p"),
            FTemplate.get_field_value_factor_feature("praise_count", field="praise_count", modifier="ln1p"),
            FTemplate.get_field_value_factor_feature("scrap_count", field="scrap_count", modifier="ln1p"),
            FTemplate.get_field_value_factor_feature("view_count", field="view_count", modifier="ln1p"),
            FTemplate.get_field_value_factor_feature("user_card_count", field="user_card_count", modifier="ln1p"),
            # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html#function-decay
            # TODO: decay function
            FTemplate.get_field_value_factor_feature("created_at_score", field="created_at_score"),
            FTemplate.get_field_value_factor_feature("has_tag", field="has_tag"),
            FTemplate.get_field_value_factor_feature("is_project", field="is_project"),

            FTemplate.get_multimatch_feature(
                name="desc.prod.keyword",
                fields=[
                    "description.bm25",
                    "keyword_list.bm25",
                    "prod_name.bm25",
                    "prod_brand_name.bm25",
                    "prod_categories.bm25",
                ],
                operator="and",
                type="most_fields"
            ),
        ]
    }
}


print(json.dumps(feature_set, ensure_ascii=False, indent=4))

# pushes the feature set to the tmdb index's LTR store (a hidden index)
client.create_featureset(
    index=SERVICE_INDEX, 
    name=FEATURE_SET, 
    ftr_config=feature_set
)

# add feature map for ltr model
with open(os.path.join(WORK_DIR, FEATURE_SET + ".fmap.txt"), "w+") as writer:
    for idx, feat in enumerate(feature_set["featureset"]["features"]):
        data = [
            idx,
            feat["name"],
            "q",
        ]
        writer.write(" ".join(str(x) for x in data) + "\n")