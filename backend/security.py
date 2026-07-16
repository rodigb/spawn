import keyring

SERVICE_NAME = "local-ai-agent"


def save_email_password(email_address: str, password: str) -> None:
    keyring.set_password(
        SERVICE_NAME,
        email_address,
        password,
    )


def get_email_password(email_address: str) -> str:
    password = keyring.get_password(
        SERVICE_NAME,
        email_address,
    )

    if password is None:
        raise ValueError("No password stored for this account.")

    return password


def delete_email_password(email_address: str) -> None:
    try:
        keyring.delete_password(
            SERVICE_NAME,
            email_address,
        )
    except keyring.errors.PasswordDeleteError:
        pass