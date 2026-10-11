import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    print("\n--- Testing GET /health ---")
    response = client.get("/health")
    print("Status Code:", response.status_code)
    print("Response   :", response.json())
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["supported_grades"] == ["9", "10", "11", "12"]
    print("--> Health check passed!")


def test_validation_empty_message():
    print("\n--- Testing Input Validation (Empty Message) ---")
    payload = {
        "student_id": "std_101",
        "student_name": "Aarav",
        "message": "   ",  # only whitespace
    }
    response = client.post("/chat", json=payload)
    print("Status Code:", response.status_code)
    print("Response   :", response.json())
    assert response.status_code == 422  # Unprocessable Entity
    print("--> Empty message rejection passed!")


def test_validation_too_long_message():
    print("\n--- Testing Input Validation (Excessive Length > 1000 chars) ---")
    payload = {
        "student_id": "std_101",
        "student_name": "Aarav",
        "message": "A" * 1050,  # exceeds 1000 chars
    }
    response = client.post("/chat", json=payload)
    print("Status Code:", response.status_code)
    print("Response   :", response.json())
    assert response.status_code == 422
    print("--> Long message rejection passed!")


def test_validation_invalid_grade():
    print("\n--- Testing Grade Validation (Reject Grade Outside 9th-12th) ---")
    payload = {
        "student_id": "std_101",
        "student_name": "Aarav",
        "grade": "8",
        "message": "Explain Newton's laws.",
    }
    response = client.post("/chat", json=payload)
    print("Status Code:", response.status_code)
    assert response.status_code == 422
    print("--> Out-of-range grade rejection passed!")


def test_cors_headers():
    print("\n--- Testing CORS Headers ---")
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/chat", headers=headers)
    print("Status Code:", response.status_code)
    print("Access-Control-Allow-Origin:", response.headers.get("access-control-allow-origin"))
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin in ("*", "http://localhost:3000")
    print(f"--> CORS setup passed! (Origin returned: {allow_origin})")


def test_chat_across_grades():
    print("\n--- Testing POST /chat with Grade Selection (e.g. 12th Grade) ---")
    payload = {
        "student_id": "std_101",
        "student_name": "Aarav",
        "grade": "12th",
        "mode": "socratic",
        "message": "Can you help me understand Faraday's law of electromagnetic induction?",
    }
    response = client.post("/chat", json=payload)
    print("Status Code:", response.status_code)
    data = response.json()
    print("Response   :", data)
    assert response.status_code == 200
    assert "reply" in data
    assert data["grade"] == "12"
    assert data["mode"] == "socratic"
    print("--> Grade-aware chat completion passed!")


if __name__ == "__main__":
    print("=" * 70)
    print("FASTAPI CHAT API AUTOMATED TEST SUITE (GRADES 9TH TO 12TH)")
    print("=" * 70)
    try:
        test_health()
        test_validation_empty_message()
        test_validation_too_long_message()
        test_validation_invalid_grade()
        test_cors_headers()
        test_chat_across_grades()
        print("\n" + "=" * 70)
        print("ALL API TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n[X] Test failed: {e}")
        sys.exit(1)
