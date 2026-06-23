from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from anthropic import Anthropic
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PETER AI v4.0 Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
BRIDGE_URL = "http://localhost:9000"

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "PETER AI Backend Running"}

@app.post("/api/chat")
async def chat(request: dict):
    """Chat with PETER AI using Anthropic"""
    message = request.get("message")
    
    if not message:
        raise HTTPException(400, "message required")
    
    response = anthropic_client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=1024,
        messages=[{"role": "user", "content": message}]
    )
    
    return {
        "response": response.content[0].text,
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens
    }

@app.post("/v1/chat")
async def gateway_chat(request: dict):
    """Gateway → Bridge → Backend → Anthropic"""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{BRIDGE_URL}/v1/chat",
            json=request,
            headers=request.get("headers", {})
        )
    return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
