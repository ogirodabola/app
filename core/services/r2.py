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

def upload_to_r2(file, folder="uploads"):
    extension = file.filename.split(".")[-1]
    filename = f"{uuid4()}.{extension}"
    key = f"{folder}/{filename}"

    s3.upload_fileobj(
        file.file,
        R2_BUCKET,
        key,
        ExtraArgs={"ContentType": file.content_type}
    )

    public_url = f"https://{R2_BUCKET}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{key}"
    return public_url
