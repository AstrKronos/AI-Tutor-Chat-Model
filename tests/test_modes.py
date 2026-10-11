import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.ai import generate_tutor_reply

TEST_QUESTION = "Why is respiration considered an exothermic reaction in Science?"
MODES = [
    ("socratic", "1. Socratic Method"),
    ("detailed_explanation", "2. Detailed Explanation"),
    ("exam_ready", "3. Exam Ready (CBSE Board Format)"),
]

print("=" * 80)
print("TESTING 3 FUNCTION MODES ON THE SAME QUESTION")
print(f"Question: \"{TEST_QUESTION}\"")
print("=" * 80)

for mode_key, mode_name in MODES:
    print(f"\n>>> [MODE: {mode_name}] <<<")
    try:
        reply = generate_tutor_reply(TEST_QUESTION, mode=mode_key)
        print(reply)
    except Exception as e:
        print(f"[Error]: {e}")
    print("-" * 80)

print("\nMode verification complete!")
