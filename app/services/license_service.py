import string
import secrets


def generate_license_key() -> str:
    chars = string.ascii_uppercase + string.digits
    return "-".join("".join(secrets.choice(chars) for _ in range(5)) for _ in range(4))
