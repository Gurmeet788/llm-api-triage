from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

from src.llm.client import ask_llm

app = FastAPI()


class TriageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class TriageResponse(BaseModel):
    category: Literal["billing", "bug", "feature", "other"]
    urgency: Literal["low", "normal", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


@app.post("/triage")
def triage(request: TriageRequest):

    with open("prompts/triage-v1.md", "r", encoding="utf-8") as file:
        prompt = file.read()

    prompt = prompt.replace("{{USER_TEXT}}", request.text)

    llm_response = ask_llm(prompt)

    return {
        "llm_response": llm_response
    }