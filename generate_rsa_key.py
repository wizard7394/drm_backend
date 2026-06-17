from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_and_save_key():
    # 1. Generate a 2048-bit RSA Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. Convert to PEM format
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    pem_str = pem.decode("utf-8")

    # 3. Append to .env file safely
    with open(".env", "a", encoding="utf-8") as env_file:
        env_file.write(f'\nRSA_PRIVATE_KEY="{pem_str}"\n')

    print("✅ RSA Private Key successfully generated and appended to .env file!")


if __name__ == "__main__":
    generate_and_save_key()
