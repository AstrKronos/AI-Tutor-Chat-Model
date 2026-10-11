import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

from services.ai import PLACEHOLDERS, generate_tutor_reply, get_active_provider

MODE_LABELS = {
    "socratic": "Socratic Method",
    "detailed_explanation": "Detailed Explanation",
    "exam_ready": "Exam Ready (CBSE Board Format)",
}


def ensure_api_key():
    provider = get_active_provider()
    env_file = PROJECT_ROOT / ".env"

    if provider == "opencode":
        key = (os.getenv("OPENCODE_API_KEY") or "").strip()
        if key in PLACEHOLDERS:
            print("\n" + "=" * 70)
            print("  OPENCODE API KEY REQUIRED")
            print("=" * 70)
            user_key = input("Please paste your OpenCode API key here: ").strip()
            if not user_key:
                print("No key entered. Exiting.")
                sys.exit(1)
            os.environ["OPENCODE_API_KEY"] = user_key
            if env_file.exists():
                text = env_file.read_text(encoding="utf-8")
                text = text.replace("OPENCODE_API_KEY=PASTE_YOUR_OPENCODE_KEY_HERE", f"OPENCODE_API_KEY={user_key}")
                text = text.replace("OPENCODE_API_KEY=your_opencode_api_key_here", f"OPENCODE_API_KEY={user_key}")
                env_file.write_text(text, encoding="utf-8")
                print("Saved OPENCODE_API_KEY to .env for future runs!")

    elif provider == "nvidia":
        key = (os.getenv("NVIDIA_API_KEY") or "").strip()
        if key in PLACEHOLDERS:
            print("\n" + "=" * 70)
            print("  NVIDIA API KEY REQUIRED")
            print("=" * 70)
            user_key = input("Please paste your NVIDIA API key here (nvapi-...): ").strip()
            if not user_key:
                print("No key entered. Exiting.")
                sys.exit(1)
            os.environ["NVIDIA_API_KEY"] = user_key
            if env_file.exists():
                text = env_file.read_text(encoding="utf-8")
                text = text.replace("NVIDIA_API_KEY=PASTE_YOUR_NVIDIA_KEY_HERE", f"NVIDIA_API_KEY={user_key}")
                text = text.replace("NVIDIA_API_KEY=your_nvidia_api_key_here", f"NVIDIA_API_KEY={user_key}")
                env_file.write_text(text, encoding="utf-8")
                print("Saved NVIDIA_API_KEY to .env for future runs!")

    else:
        key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if key in PLACEHOLDERS:
            print("\n" + "=" * 70)
            print("  GEMINI API KEY REQUIRED")
            print("=" * 70)
            user_key = input("Please paste your Gemini API key here: ").strip()
            if not user_key:
                print("No key entered. Exiting.")
                sys.exit(1)
            os.environ["GEMINI_API_KEY"] = user_key


def interactive_chat():
    ensure_api_key()
    provider = get_active_provider().upper()

    print("\n" + "=" * 75)
    print(f"  CLASS 10 CBSE AI TUTOR - INTERACTIVE 3-MODE TESTER ({provider})")
    print("=" * 75)
    print("Select a Function Mode:")
    print("  1. Socratic Method      (Hints + 1 question, no direct answers)")
    print("  2. Detailed Explanation (Deep conceptual clarity, analogies & mechanisms)")
    print("  3. Exam Ready           (CBSE Board format: keywords, formulas, examiner traps)")
    print("-" * 75)
    choice = input("Enter choice [1/2/3, default=1]: ").strip()

    mode_map = {"1": "socratic", "2": "detailed_explanation", "3": "exam_ready"}
    current_mode = mode_map.get(choice, "socratic")

    print(f"\n[Active Mode: {MODE_LABELS[current_mode]}]")
    print("Mode Switch Commands anytime in chat:")
    print("  - Type '/socratic' to switch to Socratic Method")
    print("  - Type '/detailed' to switch to Detailed Explanation")
    print("  - Type '/exam'     to switch to Exam Ready")
    print("  - Type 'clear' to reset history | 'exit' to quit\n" + "=" * 75)

    history = []

    while True:
        try:
            user_input = input(f"\nYou [{MODE_LABELS[current_mode]}] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat. Happy studying!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Exiting chat. Goodbye!")
            break

        if user_input.lower() == "clear":
            history = []
            print("[History cleared. Starting fresh!]")
            continue

        # Mode switching shortcuts
        if user_input.lower() in ("/socratic", "/mode 1", "mode 1"):
            current_mode = "socratic"
            print(f"[Switched to: {MODE_LABELS[current_mode]}]")
            continue
        if user_input.lower() in ("/detailed", "/mode 2", "mode 2"):
            current_mode = "detailed_explanation"
            print(f"[Switched to: {MODE_LABELS[current_mode]}]")
            continue
        if user_input.lower() in ("/exam", "/mode 3", "mode 3"):
            current_mode = "exam_ready"
            print(f"[Switched to: {MODE_LABELS[current_mode]}]")
            continue

        print("\nTutor is thinking...")
        try:
            reply = generate_tutor_reply(
                student_message=user_input,
                history=history,
                mode=current_mode,
            )
            print(f"\nTutor [{MODE_LABELS[current_mode]}] >\n{reply}\n")
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"\n[Error]: {e}\n")


if __name__ == "__main__":
    interactive_chat()
