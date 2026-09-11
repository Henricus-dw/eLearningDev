#!/usr/bin/env python3
"""
Simple CLI tool to inspect and reset final assessment attempts.

Usage:
    source venv/bin/activate
    python reset_attempts_cli.py
"""

from app import app, db, Student, FinalAssessmentAttempt, CourseEnrollment

def search_students(term: str):
    q = Student.query
    like = f"%{term}%"
    if term.isdigit():
        q = q.filter(Student.student_id.like(like))
    else:
        q = q.filter(
            (Student.name.ilike(like)) |
            (Student.surname.ilike(like)) |
            (Student.student_id.like(like))
        )
    return q.order_by(Student.student_id).all()


def choose_student():
    while True:
        term = input("\nSearch student by ID or name (or blank to quit): ").strip()
        if not term:
            return None
        matches = search_students(term)
        if not matches:
            print("  No students found, try again.")
            continue

        print("\nMatches:")
        for idx, s in enumerate(matches, start=1):
            print(f"  {idx}) {s.student_id}  {s.name} {s.surname}  <{s.email or 'no-email'}>")

        choice = input("Select student number (or 0 to search again): ").strip()
        if not choice.isdigit():
            print("  Invalid choice.")
            continue
        choice = int(choice)
        if choice == 0:
            continue
        if 1 <= choice <= len(matches):
            return matches[choice - 1]
        print("  Out of range.")


def show_attempts_for_student(stu: Student):
    print(f"\n=== Attempts for {stu.student_id}  {stu.name} {stu.surname} ===")

    # JSON / course_key-based finals
    key_attempts = {}
    rows = (FinalAssessmentAttempt.query
            .filter_by(student_number=stu.student_id)
            .order_by(FinalAssessmentAttempt.course_key, FinalAssessmentAttempt.attempt_no)
            .all())
    for r in rows:
        key_attempts.setdefault(r.course_key, []).append(r)

    if key_attempts:
        print("\n[FinalAssessmentAttempt / course_key finals]")
        for k, arr in key_attempts.items():
            max_no = max((a.attempt_no or 0) for a in arr)
            print(f"  - {k}: {len(arr)} row(s), highest attempt_no = {max_no}")
    else:
        print("\n[FinalAssessmentAttempt] No JSON/key-based finals found.")

    # CourseEnrollment-based attempts_used (new /final_assessment/<course_id> route)
    enrollments = CourseEnrollment.query.filter_by(student_id=stu.id).all()
    if enrollments:
        print("\n[CourseEnrollment / attempts_used]")
        for e in enrollments:
            print(
                f"  - course_id={e.course_id}  "
                f"attempts_used={getattr(e, 'attempts_used', None)}  "
                f"allowed_attempts={getattr(e, 'allowed_attempts', None)}"
            )
    else:
        print("\n[CourseEnrollment] No enrollments found.")

    return key_attempts, enrollments


def reset_key_attempts(stu: Student, key_attempts: dict):
    if not key_attempts:
        print("No key-based attempts to reset.")
        return

    print("\nWhich course_key attempts do you want to reset?")
    keys = sorted(key_attempts.keys())
    for idx, k in enumerate(keys, start=1):
        print(f"  {idx}) {k}  ({len(key_attempts[k])} row(s))")
    print("  A) ALL course_keys for this student")
    print("  0) Cancel")

    choice = input("Choice: ").strip().lower()
    if choice == "0" or choice == "":
        return

    if choice == "a":
        confirm = input("Confirm delete ALL FinalAssessmentAttempt rows for this student? [y/N]: ").strip().lower()
        if confirm != "y":
            print("  Aborted.")
            return
        deleted = (FinalAssessmentAttempt.query
                   .filter_by(student_number=stu.student_id)
                   .delete(synchronize_session=False))
        db.session.commit()
        print(f"  Deleted {deleted} FinalAssessmentAttempt row(s).")
        return

    if not choice.isdigit():
        print("  Invalid choice.")
        return
    idx = int(choice)
    if not (1 <= idx <= len(keys)):
        print("  Out of range.")
        return

    course_key = keys[idx - 1]
    confirm = input(f"Confirm delete ALL attempts for course_key='{course_key}'? [y/N]: ").strip().lower()
    if confirm != "y":
        print("  Aborted.")
        return

    deleted = (FinalAssessmentAttempt.query
               .filter_by(student_number=stu.student_id, course_key=course_key)
               .delete(synchronize_session=False))
    db.session.commit()
    print(f"  Deleted {deleted} row(s) for course_key='{course_key}'.")


def reset_enrollment_attempts(enrollments):
    if not enrollments:
        print("No CourseEnrollment rows to reset.")
        return

    print("\nWhich CourseEnrollment attempts_used do you want to reset?")
    for idx, e in enumerate(enrollments, start=1):
        au = getattr(e, "attempts_used", None)
        aa = getattr(e, "allowed_attempts", None)
        print(f"  {idx}) course_id={e.course_id}  attempts_used={au}  allowed_attempts={aa}")
    print("  A) ALL enrollments (set attempts_used=0 for each)")
    print("  0) Cancel")

    choice = input("Choice: ").strip().lower()
    if choice == "0" or choice == "":
        return

    if choice == "a":
        confirm = input("Confirm set attempts_used=0 for ALL these enrollments? [y/N]: ").strip().lower()
        if confirm != "y":
            print("  Aborted.")
            return
        for e in enrollments:
            if hasattr(e, "attempts_used"):
                e.attempts_used = 0
        db.session.commit()
        print("  attempts_used reset to 0 for all listed enrollments.")
        return

    if not choice.isdigit():
        print("  Invalid choice.")
        return
    idx = int(choice)
    if not (1 <= idx <= len(enrollments)):
        print("  Out of range.")
        return

    e = enrollments[idx - 1]
    confirm = input(f"Confirm set attempts_used=0 for course_id={e.course_id}? [y/N]: ").strip().lower()
    if confirm != "y":
        print("  Aborted.")
        return

    if hasattr(e, "attempts_used"):
        e.attempts_used = 0
        db.session.commit()
        print(f"  attempts_used reset to 0 for course_id={e.course_id}.")
    else:
        print("  Enrollment has no attempts_used column on this model.")


def main():
    print("=== Enroll Attempt Reset Tool ===")
    print("This will NOT touch anything unless you explicitly confirm.\n")

    with app.app_context():
        while True:
            stu = choose_student()
            if not stu:
                print("Exiting.")
                break

            key_attempts, enrollments = show_attempts_for_student(stu)

            while True:
                print("\nActions:")
                print("  1) Reset FinalAssessmentAttempt rows (JSON / course_key finals)")
                print("  2) Reset CourseEnrollment.attempts_used (numeric course_id finals)")
                print("  3) Refresh view for this student")
                print("  0) Choose another student / exit")

                choice = input("Select action: ").strip()
                if choice == "1":
                    reset_key_attempts(stu, key_attempts)
                elif choice == "2":
                    reset_enrollment_attempts(enrollments)
                elif choice == "3":
                    key_attempts, enrollments = show_attempts_for_student(stu)
                elif choice == "0":
                    break
                else:
                    print("  Invalid choice.")


if __name__ == "__main__":
    main()