from typing import Optional

# https://wiki.dailyhou.se/display/API/cards

TOP_K = 300                     # 최대 검색결과 수
SHOW_K = 100                    # 데모에서 보여질 검색결과 수
ELEM_DELIMITER = " <> "         # 리스트 원소 구분자
DESC_MAX_LEN = 40

TEXT_TYPE_FIELDS = set([
    # must
    "title",
    "title.standard",
    "title.no_syn",
    "description",
    "description.standard",
    "description.no_syn",
    "keywords",
    "keywords.standard",
    "keywords.no_syn",
    "comments",
    "comments.standard",
    "comments.no_syn",
    "nickname",
    "nickname.standard",
    "nickname.no_syn",
    "reinforcement",
    "reinforcement.keyword",
    # must not
    "negatives",
    "negatives.standard",
])

# https://wiki.dailyhou.se/pages/viewpage.action?pageId=100179009
FIELDS = {
    # doc info
    "id": "문서ID",
    "first_image": "질문내사진",
    "userable_type": "유저타입",
    "user_id": "유저ID",

    # matching similarity
    "title": "질문타이틀",
    "title.standard": "질문타이틀(std)",
    "title.no_syn": "질문타이틀(noSyn)",
    "description": "질문",
    "keywords": "해시태그",
    "comments": "코멘트",  # 콤마 구분
    "nickname": "닉네임",
    "negatives": "불용어",
    "reinforcement": "보강어",

    # factors
    "created_at": "등록시각",
    "created_at_score": "등록시각(점수)",
    "commented_at": "코멘트시각",
    "bookmark_count": "북마크수",
    "reply_count": "댓글수",
    "reply_count_score": "댓글수(점수)",
    "view_count": "조회수",
    "view_count_score": "조회수(점수)",
}

FEATURES = {}


def decode_doc_field(field):
    return FIELDS.get(field, field)

def decode_featureset(field):
    return FEATURES.get(field, field)
