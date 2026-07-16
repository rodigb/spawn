import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"


async def summarize_email(
    sender: str,
    subject: str,
    body: str,
) -> str:
    prompt = f"""
You are an email assistant.

Summarize the email below in no more than three sentences.

Include:
- what the sender wants,
- any deadline or date,
- whether the user needs to take action.

Do not invent facts.

Sender: {sender}
Subject: {subject}

Email:
{body}
""".strip()

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": DEFAULT_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )

        response.raise_for_status()
        data = response.json()

    summary = data.get("response", "").strip()

    if not summary:
        raise RuntimeError("The local model returned an empty summary.")

    return summary

async def draft_email_reply(
    sender: str,
    subject: str,
    body: str,
) -> str:
    prompt = f"""
You are an email assistant.

Write a concise, professional reply to the email below.

Rules:
- Do not invent facts.
- Do not claim something has been completed unless the email confirms it.
- Do not make financial commitments.
- Do not include a subject line.
- Return only the reply body.

Sender: {sender}
Subject: {subject}

Email:
{body}
""".strip()

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": DEFAULT_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )

        response.raise_for_status()
        data = response.json()

    draft = data.get("response", "").strip()

    if not draft:
        raise RuntimeError("The local model returned an empty draft.")

    return draft