from fastapi import FastAPI

app = FastAPI(title="Local AI Agent")

@app.get("/health")
async def health():
    return {"status": "ok"}