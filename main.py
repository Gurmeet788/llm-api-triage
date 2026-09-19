from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from openai import APITimeoutError, RateLimitError, APIStatusError
import os
from dotenv import load_dotenv
from src.llm.client import ask_llm, repair_llm_response
from src.llm.parser import parse_llm_response

load_dotenv()

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

    print(os.getenv("LLM_ENABLED"))
    if os.getenv("LLM_ENABLED", "true").lower() != "true":
        raise HTTPException(
            status_code=503,
            detail="LLM service is currently disabled"
        )

    try:
        llm_response = ask_llm(prompt)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="LLM request timed out after 3 retry")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="LLM rate limit exceeded after 3 retry")
    except APIStatusError as e:
        raise HTTPException(status_code=e.status_code, detail=f"LLM request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM request failed: {str(e)}")

    try:
        parsed_response = parse_llm_response(llm_response)
        validated_response = TriageResponse(**parsed_response)
    except ValueError as e:
        
        try:
            repaired_response = repair_llm_response(llm_response, str(e))
            parsed_response = parse_llm_response(repaired_response)
            validated_response = TriageResponse(**parsed_response)
        except APITimeoutError:
            raise HTTPException(status_code=504, detail="LLM repair request timed out")
        except RateLimitError:
            raise HTTPException(status_code=429, detail="LLM repair rate limit exceeded")
        except APIStatusError as e:
            raise HTTPException(status_code=e.status_code, detail=f"LLM repair request failed: {str(e)}")
        except ValueError:
            raise HTTPException(status_code=422, detail="LLM output could not be parsed or validated after one repair attempt")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM repair request failed: {str(e)}")

    return {
        "validated_llm_response": validated_response
    }