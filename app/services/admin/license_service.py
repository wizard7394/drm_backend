import string
import secrets


class AdminLicenseService:
    @staticmethod
    def generate_complex_license_key(blocks: int = 6, chars_per_block: int = 6) -> str:
        chars = string.ascii_letters + string.digits
        return "-".join(
            "".join(secrets.choice(chars) for _ in range(chars_per_block))
            for _ in range(blocks)
        )

    @staticmethod
    def generate_hex_license_key() -> str:
        return secrets.token_hex(32)
