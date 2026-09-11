from app import db, CourseEnrollment, AttemptsAdjustment

student_id = 1       # 👈 your test student
course_id = 25       # 👈 your desktop_test course

print("=== 🔍 Checking CourseEnrollment ===")
enr = CourseEnrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
if not enr:
    print("❌ No CourseEnrollment found for that student/course.")
else:
    print(f"✅ Enrollment found: id={enr.id}")
    print(f"allowed_attempts = {getattr(enr, 'allowed_attempts', None)}")

print("\n=== 📋 AttemptsAdjustment records ===")
adjustments = AttemptsAdjustment.query.filter_by(student_id=student_id, course_id=course_id).order_by(AttemptsAdjustment.created_at.desc()).all()
if not adjustments:
    print("❌ No AttemptsAdjustment records yet.")
else:
    for a in adjustments:
        print(f"  id={a.id} | delta={a.delta} | reason='{a.reason}' | created_at={a.created_at}")

print("\n=== ✅ Summary ===")
if enr:
    print(f"Current cap (allowed_attempts): {getattr(enr, 'allowed_attempts', None)}")
    print(f"Total adjustments found: {len(adjustments)}")