from typing import Optional

# https://wiki.dailyhou.se/pages/viewpage.action?pageId=29601040

_card_residence_code = {
    "meta": "사진공간정보",
    0: "원룸",
    1: "거실",
    2: "침실",
    3: "키친",
    4: "욕실",
    5: "아이방",
    6: "드레스룸",
    7: "서재&작업실",
    8: "베란다",
    9: "사무공간",
    10: "상업공간",
    11: "가구&소품",
    12: "현관",
    13: "외관&기타",
    14: "제품후기",
    15: "자기소개",
    16: "비포사진",
    17: "복도",
    18: "전문가리뷰",
    19: "전문가소개",
    20: "도면 및 가구배치도",
    21: "시공 리뷰",
    22: "디자인 이미지",
}

_card_style_code = {
    "meta": "사진스타일",
    0: "모던",
    1: "북유럽",
    2: "빈티지",
    3: "내츄럴",
    4: "프로방스&로맨틱",
    5: "클래식&앤틱",
    6: "한국&아시아",
    7: "유니크",
    8: "기타",
}

_user_area = {
    "meta": "유저 주거평수",
    0: "10평 미만",
    1: "10평대",
    2: "20평대",
    3: "30평대",
    4: "40평대",
    5: "50평 이상",
}

_advice_category = {
    "meta": "",
    0: "시공정보",
    1: "수납",
    2: "꾸미기팁",
    3: "청소",
    4: "DIY&리폼",
    5: "이거어때",
    6: "생활정보",
    7: "건축&주택",
    8: "상업공간",
    9: "지식백과",
}

_project_agent = {
    "meta": "집들이 작업종류",
    0: "전문가",
    1: "셀프•DIY",
    2: "반셀프"
}

_project_residence_code = {
    "meta": "집들이주거형태",
    0: "원룸&오피스텔",
    1: "아파트",
    2: "빌라&연립",
    3: "단독주택",
    4: "사무공간",
    5: "상업공간",
    6: "기타",
}

_project_style_code = {
    "meta": "집들이 스타일",
    0: "모던",
    1: "미니멀&심플",
    2: "내추럴",
    3: "북유럽",
    4: "빈티지&레트로",
    5: "클래식&앤틱",
    6: "프렌치&프로방스",
    7: "러블리&로맨틱",
    8: "인더스트리얼",
    9: "한국&아시아",
    10: "유니크&믹스매치",
}

_project_expertise = {
    "meta": "집들이 분야",
    0: "리모델링",
    1: "홈스타일링",
    2: "부분공사",
    3: "청소",
    4: "건축"
}

_project_family = {
    "meta": "집들이 가족형태",
    0: "싱글라이프",
    1: "신혼부부",
    2: "아기가 있는 집",
    3: "취학 자녀가 있는 집",
    4: "부모님과 함께 사는 집",
    5: "기타",
}


def decode_card_residence(code: int) -> Optional[str]:
    return _card_residence_code.get(code, code)

def decode_card_style(code: int) -> Optional[str]:
    return _card_style_code.get(code, code)

def decode_project_residence(code: int) -> Optional[str]:
    return _project_residence_code.get(code, code)

def decode_project_style(code: int) -> Optional[str]:
    return _project_style_code.get(code, code)

def decode_user_area(code: int) -> Optional[str]:
    return _user_area.get(code, code)

def decode_advice_category(code: int) -> Optional[str]:
    return _advice_category.get(code, code)

def decode_project_agent(code: int) -> Optional[str]:
    return _project_agent.get(code, code)

def decode_project_expertise(code: int) -> Optional[str]:
    return _project_expertise.get(code, code)

def decode_project_family(code: int) -> Optional[str]:
    return _project_family.get(code, code)
