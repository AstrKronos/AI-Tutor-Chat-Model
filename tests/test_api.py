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


def test_fallback_on_missing_or_failed_ai():
    print("\n--- Testing Fallback Handling (POST /chat without valid key) ---")
    payload = {
        "student_id": "std_101",
        "student_name": "Aarav",
        "message": "Can you help me understand Newton's third law of motion?",
    }
    response = client.post("/chat", json=payload)
    print("Status Code:", response.status_code)
    data = response.json()
    print("Response   :", data)
    assert response.status_code == 200
    assert "reply" in data
    assert "status" in data
    print("--> Fallback handling passed! Server did not crash.")


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 2 - FASTAPI CHAT API AUTOMATED TEST SUITE")
    print("=" * 70)
    try:
        test_health()
        test_validation_empty_message()
        test_validation_too_long_message()
        test_cors_headers()
        test_fallback_on_missing_or_failed_ai()
        print("\n" + "=" * 70)
        print("ALL PHASE 2 API TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n[X] Test failed: {e}")
        sys.exit(1)
