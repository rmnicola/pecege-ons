#!/usr/bin/env python3
"""Cria o bucket da aula ETL II no RustFS (S3), se ainda não existir."""

import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET_KEY"],
    region_name="us-east-1",
    config=Config(s3={"addressing_style": "path"}),
)
bucket = os.environ["S3_BUCKET"]
try:
    s3.head_bucket(Bucket=bucket)
    print(f"bucket {bucket} já existe")
except ClientError:
    s3.create_bucket(Bucket=bucket)
    print(f"bucket {bucket} criado")
