from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from src.llm.client import ask_llm, repair_llm_response
from src.llm.parser import parse_llm_response

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

    llm_response = "I cannot classify this message."

    try:
        parsed_response = parse_llm_response(llm_response)
        validated_response = TriageResponse(**parsed_response)
    except ValueError as e:
        
        try:
            repaired_response = repair_llm_response(llm_response, str(e))
            parsed_response = parse_llm_response(repaired_response)
            validated_response = TriageResponse(**parsed_response)
        except ValueError:
            raise HTTPException(status_code=422, detail="LLM output failed validation after one repair attempt")
            

    return {
        "validated_llm_response": validated_response,
        "parsed_llm_response": parsed_response,
        "repaired_llm_response": repaired_response
    }