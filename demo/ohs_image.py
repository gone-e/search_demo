import math
import re
from typing import Optional


IMAGE_SIZES = [
    36,
    72,
    144,
    180,
    256,
    360,
    480,
    512,
    640,
    720,
    850,
    960,
    1024,
    1280,
    1360,
    1440,
    1536,
    1700,
    1920,
    2048,
    2560,
]

IMAGE_OHOUSE_LEGACY_PATTERN = re.compile(
    r"^https?://image.ohou.se/image/(?:central_crop|resize)/([^/]+)/([^/]+)/.+/.*$"
)
IMAGE_OHOUSE_PATTERN = re.compile(
    r"^https?://image.ohou.se/i/([^/]+)/([^?]+)(?:\?.*)?$"
)
S3_LOCAL_PATTERN = re.compile(
    r"^https?://s3-[a-zA-Z0-9-]+.amazonaws.com/([^/]+)/([^?]+)(?:\?.*)?$"
)
S3_GLOBAL_PATTERN = re.compile(
    r"^https?://([^.]+).(?:s3.(?:[a-zA-Z0-9-]+.)?amazonaws.com|cloudfront.net)/([^?]+)(?:\?.*)?$"
)

IMAGE_PREFIX = "https://image.ohou.se"


def get_nearest_width(width: int) -> int:
    """
    Returns nearest image resize width for the given width.
    :param width: The given width.
    :type width: int
    :return: The image width.
    """
    for size in IMAGE_SIZES:
        if size >= width:
            break
    return size


def get_image_url(
    src: str,
    width: int,
    aspect: Optional[int]=None,
    quality: Optional[int]=None,
    height: Optional[int]=None
) -> str:
    """
    Returns the resized image URL for the given image. It can convert server-
    converted image URL, or raw S3 image URL
    Wiki Documentation:
        * https://wiki.dailyhou.se/display/ohouseSystem/Image+Server
    :param src: The original image URL
    :type src: str
    :param width: The image width to use
    :type width: int
    :param aspect: The aspect ratio for height - provide null to retain
        original width
    :type aspect: Optional[int]
    :param quality: The quality of the image
    :type  quality: Optional[int]
    :return: The resized image URL
    """
    align_width = get_nearest_width(width)

    legacy_match = IMAGE_OHOUSE_LEGACY_PATTERN.findall(src)
    ohouse_match = IMAGE_OHOUSE_PATTERN.findall(src)
    s3_local_match = S3_LOCAL_PATTERN.findall(src)
    s3_global_match = S3_GLOBAL_PATTERN.findall(src)

    if len(legacy_match) > 0:
        path = f"{legacy_match[0][0]}/{legacy_match[0][1].replace('-', '/')}"

    elif len(ohouse_match) > 0:
        path = f"{ohouse_match[0][0]}/{ohouse_match[0][1]}"

    elif len(s3_local_match) > 0:
        path = f"{s3_local_match[0][0]}/{s3_local_match[0][1]}"

    elif len(s3_global_match) > 0:
        bucketName = s3_global_match[0][0]
        if bucketName == "d224jl0o7z9gbn" or bucketName == "d12gkpu9h0k5iq":
            bucketName = "bucketplace-v2-development"

        path = f"{bucketName}/{s3_global_match[0][1]}"
    else:
        return src

    if aspect is not None:
        height = math.ceil(align_width * aspect)
        url = f"{IMAGE_PREFIX}/i/{path}?w={align_width}&h={height}&c=c"
    elif height is not None:
        url = f"{IMAGE_PREFIX}/i/{path}?w={align_width}&h={height}&c=c"
    else:
        url = f"{IMAGE_PREFIX}/i/{path}?w={align_width}"

    if quality is not None:
        url += f"&q={quality}"
    # src: https://bucketplace-v2-development.s3.amazonaws.com/uploads/cards/snapshots/164257227434592134.jpeg
    # url: https://image.ohou.se/i/bucketplace-v2-development/uploads/cards/snapshots/164257227434592134.jpeg?w=180&h=234&c=c0
    # print(src)
    # print(url)
    return url
