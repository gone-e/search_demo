from typing import Optional

# https://wiki.dailyhou.se/display/API/cards

TOP_K = 300                     # 최대 검색결과 수
SHOW_K = 100                    # 데모에서 보여질 검색결과 수
ELEM_DELIMITER = " <> "         # 리스트 원소 구분자
DESC_MAX_LEN = 40

TEXT_TYPE_FIELDS = set([
    "name"
    "brand_name",
    "reinforcement",
    "negatives",
    "negatives.standard",
    "click_keywords",
])

# https://wiki.dailyhou.se/pages/viewpage.action?pageId=100179009
FIELDS = {
    # doc info
    "id": "문서ID",
    "brand_id": "브랜드ID",
    "image_url": "ImgURL",
    "discount_rate": "할인율",
    "cost": "원가",
    "selling_cost": "판매가",
    "selling": "판매여부",
    "sold_out": "품절여부",
    "properties": "속성필터",
    "mds_rank": "MD랭크(수동값/높을수록좋다)",
    "display_category_ids": "전시카테고리ID(유저용)",

    # matching similarity
    "name": "상품명",
    "name.standard": "상품명(std)",
    "name.no_syn": "상품명(noSyn)",
    "brand_name": "브랜드명",
    "brand_name.standard": "브랜드명(std)",
    "brand_name.no_syn": "브랜드명(noSyn)",
    "processed_brand_name": "브랜드명(keywordC)",
    "search_name": "상품명(검색용)",
    "no_search_name": "상품명(검색순위하락용)",
    "options": "옵션리스트",
    "reinforcement": "보강어",
    "reinforcement.keyword": "보강어(키워드)",
    "negatives": "제외어",
    "negatives.standard": "제외어(std)",

    "admin_categories": "관리카테고리",
    # admin_categories였으나 일부 겸치는 카테고리 제거함
    "search_admin_categories": "관리카테고리(정제)",
    "search_keywords": "검색어키워드(MD/Seller)",
    "search_keywords.standard": "검색어키워드(MD/Seller)(std)",
    "category_keywords": "카테고리키워드",
    "click_keywords": "클릭키워드",
    "click_keywords2": "클릭키워드2",

    # TODO: PLP 랭킹에서 사용되는 것도 혼합되어있다.
    # factors
    "is_delivery_date_specified": "배송예정일존재여부",
    "is_free_delivery": "무료배송여부",
    "delivery_method": "배송유형",
    "is_deal": "딜상품(기획전)여부",
    "quality": "",
    "quality_new": "",
    "quality_features": "품질계산피쳐",
    # "quality_features": "{'is_deal': False, 'selling_cost': 18900, 'weekly_selling_count': 205.0, 'review_count': 1333, 'card_count': 942, 'selling_score': 0.6995355414115271, 'review_score': 0.7717537894414692, 'card_score': 0.7636277330251764}",
    "sell_cnt_1_day": "최근1일구매자수",
    "sell_cnt_1_day_score": "최근1일구매자수(점수)",
    "sell_cnt_7_day": "최근7일구매자수",
    "sell_cnt_7_day_score": "최근7일구매자수(점수)",
    "sell_cnt_28_day": "최근28일구매자수",
    "sell_cnt_28_day_score": "최근28일구매자수(점수)",
    "sell_cnt_7_28_day_ratio": "최근7일구매자수/최근28일구매자수",
    "view_cnt_1_day": "최근1일조회수",
    "view_cnt_1_day_score": "최근1일조회수(점수)",
    "view_cnt_7_day": "최근7일조회수",
    "view_cnt_7_day_score": "최근7일조회수(점수)",
    "view_cnt_28_day": "최근28일조회수",
    "view_cnt_28_day_score": "최근28일조회수(점수)",
    "view_cnt_7_28_day_ratio": "최근7일조회수/최근28일조회수",
    "daily_selling_cost": "일간판매액",
    "daily_selling_count": "일간판매횟수",
    "weekly_selling_cost": "주간판매액",
    "weekly_selling_count": "주간판매횟수",
    # selling_score: 기존 사용중인 score, is_deal, selling_cost, weekly_selling_count
    "selling_score": "판매점수",
    "selling_score_new": "판매점수(new)",
    "wish_count": "위시수",
    "wish_count_score": "위시수(점수)",
    "review_count": "리뷰수",
    "review_count_score": "리뷰수(점수)",
    "review_avg": "리뷰평점",
    "review_avg_score": "리뷰평점(점수)",
    "share_count": "공유수",
    "share_count_score": "공유수(점수)",
    "card_count": "스타일링샷수",
    "card_count_score": "스타일링샷수(점수)",
}

FEATURES = {}


def decode_doc_field(field):
    return FIELDS.get(field, field)

def decode_featureset(field):
    return FEATURES.get(field, field)
