from collections import OrderedDict

SERVICE_LIST = OrderedDict({
    "card": "사진",
    "commerce": "스토어",
    "project": "집들이",
    "advice": "노하우",
    "question": "질문과답변",
})
SERVICE_LIST_REV = {v:k for k, v in SERVICE_LIST.items()}

MYELASTICSEARCH_RESOURCE_DIR = "../myelasticsearch/resources"