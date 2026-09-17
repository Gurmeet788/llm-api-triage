import os
from openai import OpenAI,APITimeoutError, RateLimitError, APIStatusError
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)


def ask_llm(prompt: str):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                messages=[
                    {
                        "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            timeout=30
        )
            return response.choices[0].message.content
        except (APITimeoutError, RateLimitError):
            if attempt < 2:
                time.sleep(2 ** attempt)
                print(f"Retrying LLM request (attempt {attempt + 1})")
                continue
            raise APITimeoutError("LLM request failed after 3 attempts")
        except APIStatusError as e:
            if 500 <= e.status_code < 600:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
            raise



def repair_llm_response(raw_response: str, validation_error: str):
    repair_prompt = f"""
    The previous LLM response was invalid.

    Original response:
    {raw_response}

    Validation error:
    {validation_error}

    Return ONLY corrected JSON.
    Do not add Markdown or explanations.
    """
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                messages=[
                    {
                        "role": "user",
                        "content": repair_prompt
                    }
                ],
                temperature=0.1,
                timeout=30
            )
            return response.choices[0].message.content
        except (APITimeoutError, RateLimitError):
            if attempt < 2:
                time.sleep(2 ** attempt)
                print(f"Retrying LLM request (attempt {attempt + 1})")
                continue
            raise APITimeoutError("LLM request failed after 3 attempts")
        except APIStatusError as e:
            if 500 <= e.status_code < 600:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
            raise