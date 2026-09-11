#!/usr/bin/env python3
"""
fix_qfile.py
Update assessments.json to point a course key to the correct questions JSON,
then verify that the bank loads via get_runtime_for_course.

Usage examples:
  python fix_qfile.py --key dggf1 --qfile dggf1_final_questions.json
  python fix_qfile.py --key dggf1 --qfile /var/enroll/questions/dggf1_final_questions.json --dir /var/enroll/questions
"""

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Fix qfile mapping for a final assessment key.")
    parser.add_argument("--key", required=True, help="Assessment key, e.g. dggf1")
    parser.add_argument("--qfile", required=True, help="Questions JSON (filename or absolute path)")
    parser.add_argument("--dir", default="/var/enroll/questions",
                        help="Directory where question JSON files live (default: /var/enroll/questions)")
    args = parser.parse_args()

    # Import app bits after args (so this script can live anywhere)
    try:
        from app import load_assessments_cfg, save_assessments_cfg, get_runtime_for_course
    except Exception as e:
        print(f"❌ Could not import from app.py: {e}")
        print("   Run this script from the project root (same folder as app.py) with your venv active.")
        sys.exit(1)

    key = args.key.strip()
    # Always store ONLY the filename in config (the loader joins it with the questions dir)
    qfile_name = os.path.basename(args.qfile.strip())

    # Verify the file actually exists in the questions dir
    candidate = os.path.join(args.dir, qfile_name)
    if not os.path.exists(candidate):
        print(f"❌ Not found: {candidate}")
        print("   Place the JSON there or pass a different --dir / --qfile.")
        sys.exit(2)

    # Load, modify, save
    items = load_assessments_cfg()
    found = False
    for x in items:
        if (x.get("key") or "").lower() == key.lower():
            old = x.get("qfile")
            x["qfile"] = qfile_name
            found = True
            print(f"🔧 Updating '{key}' qfile: {old!r} → {qfile_name!r}")
            break

    if not found:
        print(f"❌ Key '{key}' not found in assessments config.")
        print("   Existing keys:", [i.get("key") for i in items])
        sys.exit(3)

    try:
        save_assessments_cfg(items)
        print("💾 Configuration saved.")
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        sys.exit(4)

    # Verify by loading the bank
    try:
        cfg, questions = get_runtime_for_course(key)
        qcount = len(questions or [])
        title = getattr(cfg, "title", None) if cfg else None
        print(f"✅ Verified load for key '{key}': title={title!r}, questions={qcount}")
        if qcount == 0:
            print("⚠ Loaded 0 questions. Ensure the JSON has an array of questions and correct schema.")
    except Exception as e:
        print(f"❌ Verification failed via get_runtime_for_course('{key}'): {e}")
        sys.exit(5)

if __name__ == "__main__":
    main()