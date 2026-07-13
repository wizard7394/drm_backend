from sqlalchemy import Column, Integer, String
from app.core.database import VaultBase


class VaultItem(VaultBase):
    __tablename__ = "vault_items"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    batch_name = Column(String, index=True, nullable=True)
    original_filename = Column(String, nullable=True)
    file_hash = Column(String, index=True)
    download_url = Column(String)
    decryption_key = Column(String)
    aes_iv = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
