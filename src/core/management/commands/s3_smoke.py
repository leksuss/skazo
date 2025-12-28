import time
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ConnectionClosedError, EndpointConnectionError
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Smoke-test: put/get object to S3-compatible storage (SeaweedFS in dev)."

    def add_arguments(self, parser):
        parser.add_argument("--bucket", default=getattr(settings, "S3_BUCKET", "skazo"))
        parser.add_argument(
            "--wait-seconds",
            type=int,
            default=20,
            help="How long to wait for S3 endpoint readiness.",
        )

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
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
            region_name="us-east-1",
        )

        deadline = time.time() + int(options["wait_seconds"])
        last_exc: Exception | None = None
        while time.time() < deadline:
            try:
                try:
                    s3.meta.client.head_bucket(Bucket=bucket)
                except Exception:
                    s3.create_bucket(Bucket=bucket)
                break
            except (ConnectionClosedError, EndpointConnectionError) as exc:
                last_exc = exc
                time.sleep(0.5)
        else:
            msg = f"S3 endpoint not ready at {endpoint_url!r}"
            if last_exc:
                msg += f": {last_exc}"
            raise RuntimeError(msg) from last_exc

        key = f"smoke/{uuid.uuid4().hex}.txt"
        data = b"ok"

        s3.Object(bucket, key).put(Body=data, ContentType="text/plain")
        res = s3.Object(bucket, key).get()
        body = res["Body"].read()

        if body != data:
            raise RuntimeError(f"S3 smoke failed: body mismatch ({body!r} != {data!r})")

        self.stdout.write(self.style.SUCCESS(f"S3 smoke OK: s3://{bucket}/{key}"))
