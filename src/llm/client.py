import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)


def ask_llm(prompt: str):
    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    return response.choices[0].message.content


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

    response = client.chat.completions.create(
            model=os.environ["LLM_MODEL"],
            messages=[
                {
                    "role": "user",
                    "content": repair_prompt
                }
            ],
            temperature=0.1
        )

    return response.choices[0].message.content