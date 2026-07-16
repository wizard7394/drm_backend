import base64
import json
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from pydantic import BaseModel
from jose import jwt

from app.core.config import settings

try:
    clean_pem = settings.RSA_PRIVATE_KEY.strip(" \"'")
    clean_pem = clean_pem.replace("\\n", "\n")
    private_key_formatted = clean_pem.encode("utf-8")

    private_key = serialization.load_pem_private_key(
        private_key_formatted,
        password=None,
    )
    public_key = private_key.public_key()
except Exception as e:
    raise ValueError(f"Failed to parse RSA_PRIVATE_KEY: {e}")


def get_public_key_pem() -> str:
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem.decode("utf-8")


def sign_payload(payload: BaseModel) -> str:
    payload_bytes = json.dumps(payload.model_dump()).encode("utf-8")
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.CLIENT_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_admin_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ADMIN_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.ADMIN_SECRET_KEY, algorithm=settings.ALGORITHM
    )
