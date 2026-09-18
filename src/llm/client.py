import os
from openai import OpenAI,APITimeoutError, RateLimitError, APIStatusError
from dotenv import load_dotenv
import time
import random
import logging


load_dotenv()

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger=logging.getLogger(__name__)

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    max_retries=0
)


def ask_llm(prompt: str):

    start=time.perf_counter()
    logger.info(f"Starting LLM request")

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

            latency_ms = round((time.perf_counter() - start) * 1000)
            logger.info(f"LLM request completed in {latency_ms:.2f}ms")

            return response.choices[0].message.content

        except APITimeoutError as e:

            log_llm_failure(attempt, start, e)

            if attempt < 2:

                delay= 2 ** attempt
                jitter=random.uniform(0,0.5)
                time.sleep(delay+jitter)

                continue

            raise

        except RateLimitError as e:
            
            log_llm_failure(attempt, start, e)

            if attempt < 2:
                retry_after = e.response.headers.get("retry-after")
                if retry_after:
                    time.sleep(int(retry_after))
                else:
                    delay = 2 ** attempt
                    jitter = random.uniform(0, 0.5)
                    time.sleep(delay + jitter)

                continue

            raise
        
        except APIStatusError as e:

            log_llm_failure(attempt, start, e)

            if 500 <= e.status_code < 600:

                if attempt < 2:

                    delay= 2 ** attempt
                    jitter=random.uniform(0,0.5)
                    time.sleep(delay+jitter)

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
    start=time.perf_counter()
    logger.info(f"Starting LLM repair request")

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

            latency_ms = round((time.perf_counter() - start) * 1000)
            logger.info(f"LLM repair request completed in {latency_ms:.2f}ms")

            return response.choices[0].message.content

        except APITimeoutError as e:

            log_llm_failure(attempt, start, e)

            if attempt < 2:

                delay= 2 ** attempt
                jitter=random.uniform(0,0.5)
                time.sleep(delay+jitter)

                continue

            raise APITimeoutError("LLM request failed after 3 attempts")

        except RateLimitError as e:
            
            log_llm_failure(attempt, start, e)

            if attempt < 2:
                retry_after = e.response.headers.get("retry-after")
                if retry_after:
                    time.sleep(int(retry_after))
                else:
                    delay = 2 ** attempt
                    jitter = random.uniform(0, 0.5)
                    time.sleep(delay + jitter)
                continue

            raise 

        except APIStatusError as e:

            log_llm_failure(attempt, start, e)

            if 500 <= e.status_code < 600:

                if attempt < 2:

                    delay= 2 ** attempt
                    jitter=random.uniform(0,0.5)
                    time.sleep(delay+jitter)

                    continue
            raise


def log_llm_failure(attempt, start_time, error):

    latency_ms = round((time.perf_counter() - start_time) * 1000)

    logger.error(
        "LLM call failed",
        extra={
            "model": os.environ["LLM_MODEL"],
            "latency_ms": latency_ms,
            "success": False,
            "retry_count": attempt,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
    )