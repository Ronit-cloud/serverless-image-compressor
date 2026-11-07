import io
import os
import re
import urllib.parse

import boto3
from PIL import Image, ImageOps

s3 = boto3.client("s3")
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]

EXT = {"JPEG": "jpg", "WEBP": "webp", "PNG": "png"}
CONTENT_TYPE = {"JPEG": "image/jpeg", "WEBP": "image/webp", "PNG": "image/png"}
KEY_PATTERN = re.compile(r"^(?P<id>.+?)__(?P<w>\d+)__(?P<q>\d+)__(?P<f>[A-Za-z]+)$")


def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        stem = os.path.splitext(os.path.basename(key))[0]

        # Defaults are used for files uploaded by hand (e.g. from the S3 console)
        file_id, width, quality, fmt = stem, 1280, 75, "JPEG"
        m = KEY_PATTERN.match(stem)
        if m:
            file_id = m.group("id")
            width = max(100, min(8000, int(m.group("w"))))
            quality = max(1, min(100, int(m.group("q"))))
            fmt = m.group("f").upper()
            if fmt not in EXT:
                fmt = "JPEG"

        raw = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))

        if img.width > width:
            img = img.resize((width, int(img.height * width / img.width)), Image.LANCZOS)
        if fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        args = {"optimize": True}
        if fmt in ("JPEG", "WEBP"):
            args["quality"] = quality
        img.save(buf, format=fmt, **args)

        out_key = f"{file_id}.{EXT[fmt]}"
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=out_key,
            Body=buf.getvalue(),
            ContentType=CONTENT_TYPE[fmt],
        )
        print(f"{key} ({len(raw)} B) -> {out_key} ({buf.tell()} B)")
    return {"ok": True}
