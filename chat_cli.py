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

from services.ai import generate_tutor_reply, normalize_grade

MODE_LABELS = {
    "socratic": "Socratic Method",
    "detailed_explanation": "Detailed Explanation",
    "exam_ready": "Exam Ready (CBSE Board Format)",
}


def prompt_for_grade() -> str:
    """Prompt the user to choose their grade from 9th to 12th."""
    print("Select your Class / Grade (9th to 12th):")
    print("  [9]  Class 9th  CBSE")
    print("  [10] Class 10th CBSE")
    print("  [11] Class 11th CBSE")
    print("  [12] Class 12th CBSE")
    while True:
        raw = input("Enter grade [9/10/11/12, default=10]: ").strip()
        if not raw:
            return "10"
        try:
            return normalize_grade(raw)
        except ValueError as err:
            print(f"  [!] {err}")


def interactive_chat():
    local_model = os.getenv("LOCAL_MODEL", "qwen2.5:7b")

    print("\n" + "=" * 75)
    print(f"  CBSE AI TUTOR (CLASSES 9TH TO 12TH) - LOCAL OFFLINE ({local_model.upper()})")
    print("=" * 75)

    current_grade = prompt_for_grade()
    print("-" * 75)
    print("Select a Function Mode:")
    print("  1. Socratic Method      (Hints + 1 question, no direct answers)")
    print("  2. Detailed Explanation (Deep conceptual clarity, analogies & mechanisms)")
    print("  3. Exam Ready           (CBSE Exam format: keywords, formulas, examiner traps)")
    print("-" * 75)
    choice = input("Enter choice [1/2/3, default=1]: ").strip()

    mode_map = {"1": "socratic", "2": "detailed_explanation", "3": "exam_ready"}
    current_mode = mode_map.get(choice, "socratic")

    print(f"\n[Active Setup: Class {current_grade}th CBSE | Mode: {MODE_LABELS[current_mode]} | Model: {local_model}]")
    print("Quick Commands anytime in chat:")
    print("  - Mode switch : '/socratic', '/detailed', or '/exam'")
    print("  - Grade switch: '/9', '/10', '/11', '/12' (or '/grade')")
    print("  - Session     : 'clear' to reset history | 'exit' to quit\n" + "=" * 75)

    history = []

    while True:
        try:
            user_input = input(f"\nYou [Class {current_grade}th | {MODE_LABELS[current_mode]}] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat. Happy studying!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("exit", "quit"):
            print("Exiting chat. Goodbye!")
            break

        if cmd == "clear":
            history = []
            print("[History cleared. Starting fresh!]")
            continue

        # Grade switching shortcuts
        if cmd in ("/9", "/9th", "/grade 9", "grade 9"):
            current_grade = "9"
            print(f"[Switched Grade to: Class {current_grade}th CBSE]")
            continue
        if cmd in ("/10", "/10th", "/grade 10", "grade 10"):
            current_grade = "10"
            print(f"[Switched Grade to: Class {current_grade}th CBSE]")
            continue
        if cmd in ("/11", "/11th", "/grade 11", "grade 11"):
            current_grade = "11"
            print(f"[Switched Grade to: Class {current_grade}th CBSE]")
            continue
        if cmd in ("/12", "/12th", "/grade 12", "grade 12"):
            current_grade = "12"
            print(f"[Switched Grade to: Class {current_grade}th CBSE]")
            continue
        if cmd == "/grade":
            current_grade = prompt_for_grade()
            print(f"[Switched Grade to: Class {current_grade}th CBSE]")
            continue

        # Mode switching shortcuts
        if cmd in ("/socratic", "/mode 1", "mode 1"):
            current_mode = "socratic"
            print(f"[Switched Mode to: {MODE_LABELS[current_mode]}]")
            continue
        if cmd in ("/detailed", "/mode 2", "mode 2"):
            current_mode = "detailed_explanation"
            print(f"[Switched Mode to: {MODE_LABELS[current_mode]}]")
            continue
        if cmd in ("/exam", "/mode 3", "mode 3"):
            current_mode = "exam_ready"
            print(f"[Switched Mode to: {MODE_LABELS[current_mode]}]")
            continue

        print("\nTutor is thinking (running locally on GPU)...")
        try:
            reply = generate_tutor_reply(
                student_message=user_input,
                history=history,
                mode=current_mode,
                grade=current_grade,
            )
            print(f"\nTutor [Class {current_grade}th | {MODE_LABELS[current_mode]}] >\n{reply}\n")
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"\n[Error]: {e}\n")


if __name__ == "__main__":
    interactive_chat()
