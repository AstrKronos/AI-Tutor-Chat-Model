# Class 10 CBSE AI Tutor — Backend API

A lightweight, guardrailed Python backend for a Class 10 CBSE AI Tutor supporting **3 Function Modes** (`socratic`, `detailed_explanation`, and `exam_ready`), built with **FastAPI** and **NVIDIA NIM / Google Gemini / OpenCode Zen**.

---

## Project Structure

```text
C:\Pysustain\
├── main.py                    # FastAPI app (/chat and /health endpoints)
├── chat_cli.py                # Interactive CLI tool to test the 3 modes & guardrails in terminal
├── prompts/
│   └── tutor_prompt.txt       # System prompt with Socratic & CBSE Class 10 guardrails
├── services/
│   └── ai.py                  # Multi-provider AI router supporting 3 function modes
├── tests/
│   ├── test_prompt.py         # 10-question Socratic & guardrail test suite
│   ├── test_modes.py          # Automated 3-mode verification suite
│   └── test_api.py            # Automated FastAPI endpoint, validation & fallback tests
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # Setup & Frontend Integration Guide
```

---

## 1. Function Modes

| Mode Value | Display Label | Behavior |
| :--- | :--- | :--- |
| **`socratic`** | **Socratic Method** | Interactive hint + 1 guiding question (2–4 sentences), never reveals final answers directly. |
| **`detailed_explanation`** | **Detailed Explanation** | Full conceptual breakdown with real-world analogies, step-by-step mechanisms, and key takeaways. |
| **`exam_ready`** | **Exam Ready** | Complete CBSE Board Exam model answer with **bold** keywords, formulas/equations, point-wise breakdown, NCERT examples, and Examiner Tips. |

---

## 2. Local Setup & Running the Server

```powershell
cd C:\Pysustain
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* **Server Base URL**: `http://localhost:8000`
* **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 3. Frontend Developer Integration Snippet

CORS is enabled for **all origins (`*`)**.

```javascript
const API_BASE = "http://localhost:8000";

// Student Chat with 3 Function Modes ('socratic' | 'detailed_explanation' | 'exam_ready')
export async function sendChatMessage(studentId, studentName, message, history = [], mode = "socratic") {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      student_id: studentId,
      student_name: studentName,
      message,
      history,
      mode, // "socratic" | "detailed_explanation" | "exam_ready"
    }),
  });
  return await res.json();
  // Returns: { reply, status, mode }
}
```

---

## 4. Running Automated Tests

```powershell
# 1. Test API endpoints, validation, CORS, and fallback circuit-breaker
.\.venv\Scripts\python.exe tests/test_api.py

# 2. Test all 3 Function Modes live
.\.venv\Scripts\python.exe tests/test_modes.py
```
