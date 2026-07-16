from dataclasses import dataclass
from email.message import EmailMessage
import smtplib
import ssl

from imap_tools import MailBox


@dataclass
class EmailConnection:
    email_address: str
    password: str
    imap_host: str
    imap_port: int = 993
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465


@dataclass
class InboxMessage:
    uid: str
    subject: str
    sender: str
    date: str
    text: str


def get_latest_messages(
    connection: EmailConnection,
    limit: int = 5,
) -> list[InboxMessage]:
    messages: list[InboxMessage] = []

    with MailBox(
        connection.imap_host,
        port=connection.imap_port,
    ).login(
        connection.email_address,
        connection.password,
        initial_folder="INBOX",
    ) as mailbox:
        fetched_messages = mailbox.fetch(
            criteria="ALL",
            reverse=True,
            limit=limit,
            mark_seen=False,
        )

        for message in fetched_messages:
            message_date = (
                message.date.isoformat()
                if message.date is not None
                else ""
            )

            body = message.text or ""

            messages.append(
                InboxMessage(
                    uid=str(message.uid or ""),
                    subject=message.subject or "(No subject)",
                    sender=message.from_ or "(Unknown sender)",
                    date=message_date,
                    text=body[:5000],
                )
            )

    return messages


def get_message_by_uid(
    connection: EmailConnection,
    uid: str,
) -> InboxMessage:
    with MailBox(
        connection.imap_host,
        port=connection.imap_port,
    ).login(
        connection.email_address,
        connection.password,
        initial_folder="INBOX",
    ) as mailbox:
        fetched_messages = mailbox.fetch(
            criteria=f"UID {uid}",
            mark_seen=False,
            limit=1,
        )

        message = next(fetched_messages, None)

        if message is None:
            raise ValueError(f"Email with UID {uid} was not found.")

        message_date = (
            message.date.isoformat()
            if message.date is not None
            else ""
        )

        return InboxMessage(
            uid=str(message.uid or ""),
            subject=message.subject or "(No subject)",
            sender=message.from_ or "(Unknown sender)",
            date=message_date,
            text=(message.text or "")[:20000],
        )
    
def send_email(
    connection: EmailConnection,
    recipient: str,
    subject: str,
    body: str,
) -> None:
    message = EmailMessage()
    message["From"] = connection.email_address
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        connection.smtp_host,
        connection.smtp_port,
        context=context,
    ) as smtp:
        smtp.login(
            connection.email_address,
            connection.password,
        )

        smtp.send_message(message)