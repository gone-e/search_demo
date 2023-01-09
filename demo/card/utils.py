import sys
sys.path.append(".")
import copy
import demo.codes as codes
from demo.ohs_image import get_image_url
from demo.utils import list_to_str
from demo.card.constants import TEXT_TYPE_FIELDS, decode_featureset

    
def decode_code(field, value):
    if field == 'decode_area':
        return codes.decode_user_area(value)
    elif field == 'decode_style':
        return codes.decode_card_style(value)
    elif field == 'decode_residence':
        return codes.decode_card_residence(value)
    return value

def compress_doc(doc):
    """ extract necessary fields for debugging """
    exclude_fields = ['id', 'userable_type', 'created_at', 'type']
    space_fields = ['decode_area', 'decode_style', 'decode_residence', 'color', 'style', 'area', 'residence']
    other_text_fields = ['company', 'reinforcement', 'negatives', 'video_duration']
    new_doc = {}
    for k, v in doc.items():
        if k in exclude_fields:
            continue
        if 'url' in k:
            continue
        if v is None:
            continue
        if k == '_explanation':
            continue
        # code number to text
        v = decode_code(k, v)
        # make shorten
        if isinstance(v, list):
            v = list_to_str(v, delimiter="[::]")
        elif isinstance(v, float):
            v = round(v, 2)

        new_doc[k] = v

    return new_doc

def arrange_ranking_features(features):
    """
      - Text type field 따로 분류
      - Factors
    """
    def _find_field_by_prefix(key, fields):
        # print(key, fields)
        fields = copy.deepcopy(fields)
        for f in fields:
            # print(key.split(".")[0], f.split(".")[0])
            if key.split(".")[0] == f.split(".")[0]:
                return True
        return False

    sorted_features = sorted(features.items(), key=lambda x:x[1], reverse=True)
    text_features = ""
    other_features = ""
    for k, v in sorted_features:
        k = k.replace("f__", "")
        is_text_type = _find_field_by_prefix(k, TEXT_TYPE_FIELDS)
        if is_text_type:
            text_features += f" {decode_featureset(k)}: {v}\n"
        else:
            other_features += f" {decode_featureset(k)}: {v}\n"
    
    out = "[text]\n"
    out += text_features
    out += "[factor]\n"
    out += other_features
    return out