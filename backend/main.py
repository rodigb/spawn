from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from backend.email_client import EmailConnection, get_latest_messages
from backend.security import (
    delete_email_password,
    get_email_password,
    save_email_password,
)

app = FastAPI(
    title="Spawn API",
    version="0.1.0"
)

class EmailAccountCreate(BaseModel):
    email_address: EmailStr
    password: str = Field(min_length=1)
    imap_host: str = Field(min_length=1)
    imap_port: int = Field(default=993, ge=1, le=65535)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/email-account")
async def create_email_account(
    account: EmailAccountCreate,
) -> dict[str, str | int]:
    save_email_password(
        account.email_address,
        account.password,
    )

    return {
        "status": "saved",
        "email_address": account.email_address,
        "imap_host": account.imap_host,
        "imap_port": account.imap_port,
    }


@app.get("/emails")
async def read_recent_emails(
    email_address: EmailStr,
    imap_host: str,
    imap_port: int = 993,
    limit: int = 5,
) -> list[dict[str, str]]:
    if limit < 1 or limit > 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20.",
        )

    try:
        password = get_email_password(str(email_address))

        connection = EmailConnection(
            email_address=str(email_address),
            password=password,
            imap_host=imap_host,
            imap_port=imap_port,
        )

        messages = get_latest_messages(
            connection=connection,
            limit=limit,
        )

        return [
            {
                "uid": message.uid,
                "subject": message.subject,
                "sender": message.sender,
                "date": message.date,
                "text": message.text,
            }
            for message in messages
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to the email account: {exc}",
        ) from exc


@app.delete("/email-account/{email_address}")
async def remove_email_account(
    email_address: str,
) -> dict[str, str]:
    delete_email_password(email_address)
    return {"status": "removed"}