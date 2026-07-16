import smtplib

from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel, EmailStr, Field
from backend.agent import draft_email_reply, summarize_email
from backend.email_client import (
    EmailConnection,
    get_latest_messages,
    get_message_by_uid,
    send_email,
)
import smtplib

from backend.email_client import (
    EmailConnection,
    get_latest_messages,
    get_message_by_uid,
)

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

class EmailSummaryRequest(BaseModel):
    sender: str = Field(min_length=1)
    subject: str = ""
    body: str = Field(min_length=1, max_length=20000)

class SummarizeStoredEmailRequest(BaseModel):
    email_address: EmailStr
    imap_host: str = Field(min_length=1)
    imap_port: int = Field(default=993, ge=1, le=65535)
    uid: str = Field(min_length=1)
    
class SendEmailRequest(BaseModel):
    email_address: EmailStr
    smtp_host: str = Field(default="smtp.gmail.com", min_length=1)
    smtp_port: int = Field(default=465, ge=1, le=65535)

    recipient: EmailStr
    subject: str = Field(min_length=1, max_length=998)
    body: str = Field(min_length=1, max_length=50000)

    approved: bool

@app.post("/emails/summarize")
async def summarize_email_endpoint(
    email: EmailSummaryRequest,
) -> dict[str, str]:
    try:
        summary = await summarize_email(
            sender=email.sender,
            subject=email.subject,
            body=email.body,
        )

        return {"summary": summary}

    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Ollama. Make sure Ollama is running.",
        ) from exc

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not summarize email: {exc}",
        ) from exc

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

@app.post("/emails/summarize-by-uid")
async def summarize_email_by_uid(
    request: SummarizeStoredEmailRequest,
) -> dict[str, str]:
    try:
        password = get_email_password(str(request.email_address))
        

        connection = EmailConnection(
            email_address=str(request.email_address),
            password=password,
            imap_host=request.imap_host,
            imap_port=request.imap_port,
        )

        message = get_message_by_uid(
            connection=connection,
            uid=request.uid,
        )

        summary = await summarize_email(
            sender=message.sender,
            subject=message.subject,
            body=message.text,
        )

        return {
            "uid": message.uid,
            "subject": message.subject,
            "sender": message.sender,
            "summary": summary,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Ollama. Make sure Ollama is running.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not summarize email: {exc}",
        ) from exc
    
@app.post("/emails/draft-by-uid")
async def draft_reply_by_uid(
    request: SummarizeStoredEmailRequest,
) -> dict[str, str]:
    try:
        password = get_email_password(str(request.email_address))

        connection = EmailConnection(
            email_address=str(request.email_address),
            password=password,
            imap_host=request.imap_host,
            imap_port=request.imap_port,
        )

        message = get_message_by_uid(
            connection=connection,
            uid=request.uid,
        )

        draft = await draft_email_reply(
            sender=message.sender,
            subject=message.subject,
            body=message.text,
        )

        return {
            "uid": message.uid,
            "subject": message.subject,
            "sender": message.sender,
            "draft": draft,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Ollama. Make sure Ollama is running.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not draft reply: {exc}",
        ) from exc
    
@app.post("/emails/send")
async def send_email_endpoint(
    request: SendEmailRequest,
) -> dict[str, str]:
    if not request.approved:
        raise HTTPException(
            status_code=403,
            detail="Email must be explicitly approved before sending.",
        )

    try:
        password = get_email_password(str(request.email_address))

        connection = EmailConnection(
            email_address=str(request.email_address),
            password=password,
            imap_host="imap.gmail.com",
            imap_port=993,
            smtp_host=request.smtp_host,
            smtp_port=request.smtp_port,
        )

        send_email(
            connection=connection,
            recipient=str(request.recipient),
            subject=request.subject,
            body=request.body,
        )

        return {
            "status": "sent",
            "recipient": str(request.recipient),
            "subject": request.subject,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except smtplib.SMTPAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="Gmail rejected the stored app password.",
        ) from exc

    except smtplib.SMTPException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"SMTP error: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not send email: {exc}",
        ) from exc