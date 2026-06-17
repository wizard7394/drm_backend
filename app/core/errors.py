from fastapi import HTTPException, status


class AppErrors:
    TOKEN_EXPIRED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token_has_expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    INVALID_TOKEN = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid_token_format_or_signature",
        headers={"WWW-Authenticate": "Bearer"},
    )

    CREDENTIALS_EXCEPTION = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could_not_validate_credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    USER_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="user_account_not_found"
    )

    ADMIN_NOT_FOUND = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="admin_privileges_required"
    )

    INSUFFICIENT_PERMISSIONS = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_account_permissions"
    )

    HARDWARE_MISMATCH = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="hardware_fingerprint_mismatch"
    )

    DEVICE_BLOCKED = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="device_has_been_blocked_by_admin"
    )

    COURSE_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="requested_course_not_found"
    )

    LICENSE_EXPIRED = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="course_license_has_expired_or_invalid",
    )

    NODE_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="course_node_not_found"
    )

    VAULT_ITEM_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="vault_item_not_found"
    )

    NO_UNUSED_VAULT_ITEMS = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="no_unused_vault_items_found_for_this_batch",
    )

    INVALID_OTP = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_verification_code"
    )

    OTP_EXPIRED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="verification_code_has_expired"
    )

    ADMIN_DISABLED = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="admin_account_is_disabled"
    )

    COURSE_ACCESS_DENIED = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="access_denied_no_active_license_for_course",
    )

    VIDEO_KEYS_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="video_encryption_keys_not_found"
    )

    WEBHOOK_MISSING_SIGNATURE = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing_woocommerce_signature_header",
    )

    WEBHOOK_INVALID_SIGNATURE = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="invalid_woocommerce_digital_signature",
    )

    SERVER_CONFIG_ERROR = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="server_configuration_error_missing_webhook_secret",
    )

    INVALID_CREDENTIALS = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="incorrect_username_or_password",
        headers={"WWW-Authenticate": "Bearer"},
    )
