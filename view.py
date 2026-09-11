# view_safe.py
# Print latest final assessment attempts WITHOUT touching @property fields.
# Works even if Course has @property like `code`.

from datetime import datetime
from typing import Optional

try:
    from app import app, db
except Exception as e:
    print(f"❌ Couldn't import app/db: {e}")
    raise

# Try to import models that likely exist in your app
AssessmentAttempt = None
Student = None
Course = None
for name in ("AssessmentAttempt", "FinalAssessmentAttempt"):
    try:
        AssessmentAttempt = getattr(__import__("app", fromlist=[name]), name)
        break
    except Exception:
        pass

try:
    Student = getattr(__import__("app", fromlist=["Student"]), "Student")
except Exception:
    Student = None

try:
    Course = getattr(__import__("app", fromlist=["Course"]), "Course")
except Exception:
    Course = None


def safe_student_name(student_id) -> Optional[str]:
    """Try to get a printable student name without crashing."""
    if not Student:
        return None
    try:
        # many apps store public id in `student_id`, PK in `id`; try both safely
        s = None
        # try primary key first
        try:
            s = Student.query.get(student_id)
        except Exception:
            s = None
        # try public-id field (common)
        if s is None and hasattr(Student, "student_id"):
            s = Student.query.filter_by(student_id=student_id).first()
        if s is None and hasattr(Student, "student_number"):
            s = Student.query.filter_by(student_number=student_id).first()
        # pick a label
        if s:
            for attr in ("full_name", "name"):
                if getattr(s, attr, None):
                    return getattr(s, attr)
            # fall back to email or something else if present
            if getattr(s, "email", None):
                return s.email
            return f"Student#{getattr(s, 'id', student_id)}"
    except Exception:
        return None
    return None


def safe_course_label(att) -> str:
    """
    Return a course label WITHOUT querying @property columns.
    We avoid any ORM filter on Course.* here to prevent InterfaceError.
    """
    # Prefer explicit id if present
    cid = getattr(att, "course_id", None)
    if cid:
        return f"course_id={cid}"

    # Then a textual key if present on the attempt
    ckey = getattr(att, "course_key", None) or getattr(att, "course_code", None)
    if ckey:
        return f"course_key={ckey}"

    # Last resort: if attempt has a cached title/name
    for attr in ("course_title", "course_name"):
        val = getattr(att, attr, None)
        if val:
            return str(val)

    return "Unknown course"


def fmt_pct(v) -> str:
    try:
        return f"{float(v):6.2f}%"
    except Exception:
        return "   n/a "


def main():
    if AssessmentAttempt is None:
        print("❌ Could not find AssessmentAttempt/FinalAssessmentAttempt in app.py")
        return

    with app.app_context():
        print("====================================================================================================")
        print("📊  Latest Final Assessment Results (safe)")
        print("====================================================================================================")

        try:
            q = AssessmentAttempt.query.order_by(AssessmentAttempt.id.desc()).limit(50)
            attempts = q.all()
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return

        if not attempts:
            print("⚠️  No final assessment attempts found.")
            print("====================================================================================================")
            print("✅ Done.")
            return

        header = f"{'ID':>5}  {'Student':<28} | {'Course':<32} | {'Score':>7} | {'Status':<4} | {'When'}"
        print(header)
        print("-" * len(header))
        shown = 0

        for a in attempts:
            try:
                sid = getattr(a, "student_id", None)
                sname = safe_student_name(sid) or "Unknown"
                course_label = safe_course_label(a)
                score = getattr(a, "score", None)
                passed = getattr(a, "passed", None)
                status = "PASS" if passed else "FAIL"
                ts = getattr(a, "timestamp", None) or getattr(a, "created_at", None) or getattr(a, "updated_at", None)
                when = str(ts) if ts else "?"

                print(f"[{getattr(a,'id','?'):>4}] {sname:<28} | {course_label:<32} | {fmt_pct(score)} | {status:<4} | {when}")
                shown += 1
            except Exception as row_err:
                print(f"[{getattr(a,'id','?'):>4}] <row error: {row_err}>")

        print("====================================================================================================")
        print(f"✅ {shown} attempts shown.")
        print("====================================================================================================")


if __name__ == "__main__":
    main()