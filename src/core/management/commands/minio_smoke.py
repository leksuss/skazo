import uuid

import boto3
from botocore.client import Config
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "DEPRECATED: use `s3_smoke` instead."

    def add_arguments(self, parser):
        parser.add_argument("--bucket", default=getattr(settings, "S3_BUCKET", "skazo"))

    def handle(self, *args, **options):
        endpoint_url = getattr(settings, "S3_ENDPOINT_URL", "http://localhost:8333")
        access_key_id = getattr(settings, "S3_ACCESS_KEY_ID", "seaweed")
        secret_access_key = getattr(settings, "S3_SECRET_ACCESS_KEY", "seaweed123456")
        bucket = options["bucket"]

        s3 = boto3.resource(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

        try:
            s3.meta.client.head_bucket(Bucket=bucket)
        except Exception:
            s3.create_bucket(Bucket=bucket)

        key = f"smoke/{uuid.uuid4().hex}.txt"
        data = b"ok"

        s3.Object(bucket, key).put(Body=data, ContentType="text/plain")
        res = s3.Object(bucket, key).get()
        body = res["Body"].read()

        if body != data:
            raise RuntimeError(f"S3 smoke failed: body mismatch ({body!r} != {data!r})")

        self.stdout.write(self.style.SUCCESS(f"S3 smoke OK: s3://{bucket}/{key}"))
