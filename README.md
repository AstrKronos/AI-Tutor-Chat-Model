# CBSE AI Tutor (Classes 9th to 12th) — Backend API

A lightweight, guardrailed Python backend for a CBSE AI Tutor supporting **Classes 9th to 12th** and **3 Function Modes** (`socratic`, `detailed_explanation`, and `exam_ready`), built with **FastAPI** and **NVIDIA NIM / Google Gemini / OpenCode Zen**.

---

## Project Structure

```text
C:\Pysustain\
├── main.py                    # FastAPI app (/chat and /health endpoints)
├── chat_cli.py                # Interactive CLI tool (asks for Grade 9th–12th & Function Mode)
├── prompts/
│   └── tutor_prompt.txt       # System prompt with Socratic & CBSE 9th-12th guardrails
├── services/
│   └── ai.py                  # Multi-provider AI router supporting Grades 9–12 & 3 function modes
├── tests/
│   ├── test_prompt.py         # Socratic & guardrail test suite
│   ├── test_modes.py          # Automated 3-mode verification suite
│   └── test_api.py            # Automated FastAPI endpoint, grade validation & fallback tests
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # Setup & Frontend Integration Guide
```

---

## 1. Supported Grades & Function Modes

* **Supported Grades**: `9` (9th), `10` (10th), `11` (11th), `12` (12th)
* **Function Modes**:

| Mode Value | Display Label | Behavior |
| :--- | :--- | :--- |
| **`socratic`** | **Socratic Method** | Interactive hint + 1 guiding question (2–4 sentences), never reveals final answers directly. |
| **`detailed_explanation`** | **Detailed Explanation** | Full conceptual breakdown with real-world analogies, step-by-step mechanisms, and key takeaways. |
| **`exam_ready`** | **Exam Ready** | Complete CBSE Exam model answer calibrated to the student's grade (`9`–`12`) with **bold** keywords, formulas/equations, point-wise breakdown, NCERT examples, and Examiner Tips. |

---

## 2. Local Setup & Running

### Interactive Terminal Chat (Prompts for Grade 9th–12th & Mode)
```powershell
cd C:\Pysustain
.\.venv\Scripts\python.exe chat_cli.py
```

### FastAPI Server
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

// Student Chat with Grade ('9' | '10' | '11' | '12') and Mode ('socratic' | 'detailed_explanation' | 'exam_ready')
export async function sendChatMessage(
  studentId,
  studentName,
  message,
  grade = "10",
  mode = "socratic",
  history = []
) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      student_id: studentId,
      student_name: studentName,
      message,
      grade,   // "9" | "10" | "11" | "12" (or "9th", "10th", "11th", "12th")
      mode,    // "socratic" | "detailed_explanation" | "exam_ready"
      history,
    }),
  });
  return await res.json();
  // Returns: { reply, status, mode, grade }
}
```
