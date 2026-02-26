import os
import uuid
import boto3

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")
R2_PUBLIC_BASE = os.getenv("R2_PUBLIC_BASE")

if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET, R2_PUBLIC_BASE]):
    raise RuntimeError("Variáveis R2 não configuradas corretamente")

s3 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto",
)

def upload_to_r2(file, folder="uploads"):

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    key = f"{folder}/{filename}"

    s3.upload_fileobj(
        file.file,
        R2_BUCKET,
        key,
        ExtraArgs={"ContentType": file.content_type}
    )

    return f"{R2_PUBLIC_BASE}/{key}"

def delete_from_r2(file_url: str):
    if not file_url:
        return

    # extrai key
    key = file_url.replace(R2_PUBLIC_BASE + "/", "")

    s3.delete_object(
        Bucket=R2_BUCKET,
        Key=key
    )
