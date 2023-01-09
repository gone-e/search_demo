from typing import Optional

# https://wiki.dailyhou.se/display/API/cards

TOP_K = 300                     # 최대 검색결과 수
SHOW_K = 100                    # 데모에서 보여질 검색결과 수
ELEM_DELIMITER = " <> "         # 리스트 원소 구분자
DESC_MAX_LEN = 40

TEXT_TYPE_FIELDS = set([
    "description",
    "keyword_list",
    "keyword_list.korean",
    "prod_name",
    "prod_name.standard",
    "prod_name.no_syn",
    "prod_brand_name",
    "prod_brand_name.standard",
    "prod_brand_name.no_syn",
    "prod_categories",
    "nickname",
    "company",
    "decode_style",
    "decode_area",
    "decode_residence",
    "reinforcement",
    "negatives",
    "negatives.standard",
    "click_keywords",
])

FIELDS = {
    # doc info
    "id": "사진ID",
    "image_url": "ImgURL",

    # text, keyword type fields
    "description": "설명",
    "keyword_list": "해시태그(키워드)",
    "keyword_list.korean": "해시태그",
    "prod_name": "태그상품명",
    "prod_name.standard": "태그상품명(std)",
    "prod_name.no_syn": "태그상품명(noSyn)",
    "prod_brand_name": "태그상품브랜드명",
    "prod_brand_name.standard": "태그상품브랜드명(std)",
    "prod_brand_name.no_syn": "태그상품브랜드명(noSyn)",
    "prod_categories": "태그상품카테고리",
    "nickname": "닉네임",
    "company": "회사명",
    "decode_style": "스타일",
    "decode_area": "평형",
    "decode_residence": "공간",
    "reinforcement": "보강어",
    "reinforcement.keyword": "보강어(키워드)",
    "negatives": "제외어",
    "negatives.standard": "제외어(std)",
    "click_keywords": "클릭키워드",

    # factors
    "place": "공간정보",
    "style": "스타일",
    "source": "출처",
    "user_id": "유저아이디",
    "userable_type": "유저타입",
    "view_count": "조회수",
    "scrap_count": "스크랩수",
    "reply_count": "댓글수",
    "praise_count": "좋아요수",
    "share_count": "공유수",
    "created_at": "등록시각",
    "updated_at": "마지막수정시각",
    "is_project": "집들이여부",

    # some scores
    "created_at_score": "등록시각점수",
    "video_duration_score": "비디오시간점수",
    "follwer_score": "팔로워점수",
    "user_card_count_score": "유저카드수점수",
    "scrap_score": "스크랩점수",
    "view_count_score": "조회수점수",
    "best_value": "best_value",
    "rank_value": "rank_value",

    # featureset fields
}

FEATURES = {
    # text, keyword type fields
    "description.bm25": "설명(bm25)",
    "description.proximity": "설명(prox)",
    "keyword_list.korean.bm25": "해시태그(bm25)",
    "keyword_list.korean.proximity": "해시태그(prox)",
    "prod_name.bm25": "태그상품명(bm25)",
    "prod_name.proximity": "태그상품명(prox)",
    "prod_brand_name.bm25": "상품브랜드명(bm25)",
    "prod_brand_name.proximity": "상품브랜드명(prox)",
    "prod_categories.bm25": "상품카테고리(bm25)",
    "prod_categories.proximity": "상품카테고리(prox)",
    "click_keywords.bm25": "클릭키워드(bm25)",
    "click_keywords.proximity": "클릭키워드(prox)",

    # factors
    "view_count": "조회수",
    "scrap_count": "스크랩수",
    "reply_count": "댓글수",
    "praise_count": "좋아요수",
    "share_count": "공유수",
    "created_at": "등록시각",
    "updated_at": "마지막수정시각",
    "is_project": "집들이여부",
    "has_tag": "태그여부",
}


def decode_doc_field(field):
    return FIELDS.get(field, field)

def decode_featureset(field):
    return FEATURES.get(field, field)
