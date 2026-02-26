import boto3
import os
from uuid import uuid4

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")

s3 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto",
)

import os
import uuid
import boto3

R2_PUBLIC_BASE = os.getenv("R2_PUBLIC_BASE")

def upload_to_r2(file, folder="uploads"):

    s3 = boto3.client(
        service_name="s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
        region_name="auto"
    )

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    key = f"{folder}/{filename}"

    s3.upload_fileobj(
        file.file,
        os.getenv("R2_BUCKET_NAME"),
        key,
        ExtraArgs={"ContentType": file.content_type}
    )

    # 👇 AQUI ESTÁ A MUDANÇA IMPORTANTE
    return f"{R2_PUBLIC_BASE}/{key}"
