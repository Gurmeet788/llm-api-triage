import json
import requests

API_URL = "http://127.0.0.1:8000/triage"


with open("evals/cases.json", "r", encoding="utf-8") as file:
    cases = json.load(file)


total = len(cases)
passed = 0


for case in cases:

    response = requests.post(
        API_URL,
        json={
            "text": case["text"]
        }
    )

    result = response.json()

    if "validated_llm_response" not in result:
        print("FAIL")
        print(f"Text: {case['text']}")
        print(f"API Error: {result}")
        continue

    actual_category = result["validated_llm_response"]["category"]
    actual_urgency = result["validated_llm_response"]["urgency"]

    expected_category = case["expected_category"]
    expected_urgency = case["expected_urgency"]

    category_match = actual_category == expected_category
    urgency_match = actual_urgency == expected_urgency

    if category_match and urgency_match:
        passed += 1
        status = "PASS"
    else:
        status = "FAIL"

    print(f"\n{status}")
    print(f"Text: {case['text']}")
    print(f"Expected: {expected_category}, {expected_urgency}")
    print(f"Actual:   {actual_category}, {actual_urgency}")


print("\n--------------------")
print(f"Passed: {passed}/{total}")
print(f"Match rate: {(passed / total) * 100:.1f}%")