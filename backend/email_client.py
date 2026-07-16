from dataclasses import dataclass

from imap_tools import MailBox, AND


@dataclass
class EmailConnection:
    email_address: str
    password: str
    imap_host: str
    imap_port: int = 993


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
    """
    Connects to the mailbox and returns the latest emails.
    """

    messages: list[InboxMessage] = []

    with MailBox(
        connection.imap_host,
        port=connection.imap_port,
    ).login(
        connection.email_address,
        connection.password,
        initial_folder="INBOX",
    ) as mailbox:

        fetched = mailbox.fetch(
            criteria=AND(all=True),
            reverse=True,
            limit=limit,
            mark_seen=False,
        )

        for message in fetched:
            messages.append(
                InboxMessage(
                    uid=message.uid,
                    subject=message.subject or "(No Subject)",
                    sender=message.from_ or "(Unknown Sender)",
                    date=message.date.isoformat(),
                    text=message.text or "",
                )
            )

    return messages