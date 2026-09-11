"""
One-off backfill: enqueue the certificates that were never created for the 21
Dangerous Goods Group E (DGGE) students hit by the course_key case-mismatch bug.

Background
----------
These students passed DGGE and submitted feedback, but the feedback was stored
with course_key='DGGE' while register_assessment stores the attempt key as
'dgge'. The certificate trigger compared the two exactly, found no passing
attempt, and silently skipped enqueueing the certificate. The code fix makes all
those lookups case-insensitive, but it cannot retro-enqueue the certificates for
students who already submitted their feedback (they won't submit it again), so
this script does that once.

Safe to run:
  * Idempotent — skips any student who already has a certificate_queue row for
    the course (checked by student_id + course_id, any status).
  * Only enqueues for students who actually have a PASSING attempt.
  * Sets passed_at + score from the real passing attempt (not "now"), so cert
    dates stay honest.
  * Creates rows with status='pending' — they then flow through the normal admin
    certificate queue exactly like a fresh pass would.

Run on the server AFTER deploying the fixed app.py:
    python backfill_dgge_certificates.py            # dry run, prints what it would do
    python backfill_dgge_certificates.py --commit   # actually writes
"""
import sys
from app import app, db, Student, Course, AssessmentAttempt, CertificateQueue, CourseFeedback

COMMIT = "--commit" in sys.argv


def latest_passing_attempt(student, ck_lower):
    """Most recent passing AssessmentAttempt for this student + course_key."""
    from sqlalchemy import func
    return (
        AssessmentAttempt.query
        .filter(
            AssessmentAttempt.student_id == str(student.student_id),
            func.lower(AssessmentAttempt.course_key) == ck_lower,
            AssessmentAttempt.passed == True,  # noqa: E712
        )
        .order_by(AssessmentAttempt.created_at.desc())
        .first()
    )


def main():
    from sqlalchemy import func
    with app.app_context():
        course = Course.query.filter(
            func.lower(Course.final_assessment_key) == "dgge"
        ).first()
        if not course:
            print("ERROR: no course with final_assessment_key ~ 'dgge' found.")
            return
        print(f"Course: id={course.id} title={course.title!r} key={course.final_assessment_key!r}")

        # All students who submitted DGGE feedback (course_key matched case-insensitively).
        fb_rows = CourseFeedback.query.filter(
            func.lower(CourseFeedback.course_key) == "dgge"
        ).all()
        print(f"DGGE feedback rows: {len(fb_rows)}")

        enqueued, skipped_existing, skipped_no_pass, skipped_no_student = 0, 0, 0, 0

        for fb in fb_rows:
            student = Student.query.get(fb.student_id)
            if not student:
                skipped_no_student += 1
                continue

            # Already in the queue? (any status) -> idempotent skip
            existing = CertificateQueue.query.filter_by(
                student_id=student.id, course_id=course.id
            ).first()
            if existing:
                skipped_existing += 1
                continue

            att = latest_passing_attempt(student, "dgge")
            if not att or (att.score is None or att.score < 80):
                skipped_no_pass += 1
                print(f"  SKIP (no passing attempt): {student.student_id} {student.name} {student.surname}")
                continue

            company = student.company or (
                student.created_by_company.name if getattr(student, "created_by_company", None) else None)
            passed_at = getattr(att, "finished_at", None) or getattr(att, "created_at", None)

            print(f"  ENQUEUE: {student.student_id} {student.name} {student.surname} "
                  f"score={att.score} passed_at={passed_at}")

            if COMMIT:
                entry = CertificateQueue(
                    student_id=student.id,
                    course_id=course.id,
                    course_title=course.title,
                    student_name=f"{student.name} {student.surname}",
                    student_email=student.email,
                    national_id=student.national_id,
                    company=company,
                    score=att.score,
                    passed_at=passed_at,
                    status="pending",
                )
                db.session.add(entry)
            enqueued += 1

        if COMMIT:
            db.session.commit()

        print()
        print(f"{'COMMITTED' if COMMIT else 'DRY RUN'} — would enqueue: {enqueued}")
        print(f"  skipped (already queued): {skipped_existing}")
        print(f"  skipped (no passing attempt): {skipped_no_pass}")
        print(f"  skipped (student missing): {skipped_no_student}")
        if not COMMIT:
            print("\nRe-run with --commit to apply.")


if __name__ == "__main__":
    main()
