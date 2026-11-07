import json
import os
import uuid

import boto3
from botocore.config import Config

REGION = os.environ["AWS_REGION"]
INPUT_BUCKET = os.environ["INPUT_BUCKET"]
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]

s3 = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)

EXT = {"JPEG": "jpg", "WEBP": "webp", "PNG": "png"}


def _resp(status, payload):
    # CORS is configured on the Function URL, not here.
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def lambda_handler(event, context):
    try:
        data = json.loads(event.get("body") or "{}")
        width = max(100, min(8000, int(data.get("max_width", 1280))))
        quality = max(1, min(100, int(data.get("quality", 75))))
        fmt = str(data.get("format", "JPEG")).upper()
        if fmt not in EXT:
            fmt = "JPEG"

        file_id = uuid.uuid4().hex
        # Settings travel inside the key: <id>__<width>__<quality>__<format>
        input_key = f"{file_id}__{width}__{quality}__{fmt}"
        output_key = f"{file_id}.{EXT[fmt]}"

        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": INPUT_BUCKET, "Key": input_key},
            ExpiresIn=300,
        )
        download_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": OUTPUT_BUCKET, "Key": output_key},
            ExpiresIn=900,
        )
        return _resp(200, {
            "upload_url": upload_url,
            "download_url": download_url,
            "format": fmt.lower(),
        })
    except Exception as e:
        return _resp(500, {"error": str(e)})
