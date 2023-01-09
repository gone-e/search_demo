from typing import Optional

# https://wiki.dailyhou.se/display/API/cards

_doc_field = {
    'id': '사진ID',
    'image_url': '이미지URL',
    'description': 'Body',
    'place': '사진공간정보',
    'style': '스타일',
    'source': '사진출처URL',
    'view_count': '조회수',
    'scrap_count': '스크랩수',
    'reply_count': '댓글수',
    'praise_count': '좋아요수',
    'share_count': '공유수',
    'keyword_list': '사진해시태그',
    'created_at': '등록시각',
    'updated_at': '마지막수정시각',
}

def decode_doc_field(field: str) -> Optional[str]:
    return _doc_field.get(field, field)
