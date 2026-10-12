# Socra — Offline CBSE AI Tutor (Classes 9th to 12th | Qwen 2.5 7B)

A 100% offline, local Python backend for a CBSE AI Tutor running natively on **Qwen 2.5 7B (`qwen2.5:7b`)** via **Ollama**, supporting **Classes 9th to 12th** and **3 Function Modes** (`socratic`, `detailed_explanation`, and `exam_ready`). Requires **zero API keys** and **zero internet connection**.

---

## Project Structure

```text
C:\Socra\
├── main.py                    # FastAPI app (/chat and /health endpoints)
├── chat_cli.py                # Interactive CLI tool (prompts for Grade 9th–12th & Function Mode)
├── prompts/
│   └── tutor_prompt.txt       # System prompt with Socratic & CBSE 9th-12th guardrails
├── services/
│   └── ai.py                  # Local Qwen 2.5 7B AI service supporting Grades 9–12 & 3 function modes
├── tests/
│   ├── test_prompt.py         # Socratic & guardrail test suite
│   ├── test_modes.py          # Automated 3-mode verification suite
│   └── test_api.py            # Automated FastAPI endpoint & grade validation tests
├── requirements.txt           # Python dependencies
├── .env.example               # Local configuration template
└── README.md                  # Offline Setup & Frontend Integration Guide
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

## 2. One-Time Local Setup (100% Offline After Setup)

### Step 1: Install Ollama & Pull Qwen 2.5 7B
```powershell
winget install -e --id Ollama.Ollama
ollama pull qwen2.5:7b
```

### Step 2: Install Python Dependencies
```powershell
cd C:\Socra
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

---

## 3. Running Offline

### Interactive Terminal Chat (Prompts for Grade 9th–12th & Mode)
```powershell
cd C:\Socra
.\.venv\Scripts\python.exe chat_cli.py
```

### FastAPI Server
```powershell
cd C:\Socra
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* **Server Base URL**: `http://localhost:8000`
* **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 4. Frontend Developer Integration Snippet

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
