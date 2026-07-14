import os
import base64
import json
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from pydantic import BaseModel
from dotenv import load_dotenv
from jose import jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")

if not SECRET_KEY or not ADMIN_SECRET_KEY:
    raise ValueError(
        "SECURITY CONFIGURATION ERROR: SECRET_KEY or ADMIN_SECRET_KEY is missing."
    )

ALGORITHM = os.getenv("ALGORITHM", "HS256")

CLIENT_TOKEN_EXPIRE_MINUTES = int(os.getenv("CLIENT_TOKEN_EXPIRE_MINUTES", 60))
ADMIN_TOKEN_EXPIRE_MINUTES = int(os.getenv("ADMIN_TOKEN_EXPIRE_MINUTES", 30))

PRIVATE_KEY_PEM = os.getenv("RSA_PRIVATE_KEY")
if not PRIVATE_KEY_PEM:
    raise ValueError(
        "RSA_PRIVATE_KEY is missing. System must not generate runtime keys."
    )

try:
    private_key_formatted = PRIVATE_KEY_PEM.replace("\\n", "\n").encode("utf-8")
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
    expire = datetime.now(timezone.utc) + timedelta(minutes=CLIENT_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_admin_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ADMIN_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, ADMIN_SECRET_KEY, algorithm=ALGORITHM)
