from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import VaultBase


class VaultItem(VaultBase):
    __tablename__ = "vault_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    batch_name: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(128), index=True)
    download_url: Mapped[str] = mapped_column(String(1024))
    decryption_key: Mapped[str] = mapped_column(String(255))
    aes_iv: Mapped[Optional[str]] = mapped_column(String(32))
    duration: Mapped[Optional[int]] = mapped_column()
