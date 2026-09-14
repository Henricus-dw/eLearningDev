"""Run the eLearning app on your own machine with fake data.

    python local_dev.py setup    # build instance/students.db and seed fake data
    python local_dev.py run      # serve on http://127.0.0.1:8008

Local only. It never talks to the dev or production servers, all outgoing
email is blocked (via run_dev.py), and it refuses to seed a database that
already holds students or admins, so it cannot be pointed at a real copy of the
data by mistake. See README.md.
"""
import argparse
import math
import os
import struct
import sys
import wave
import zlib

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

ADMIN_EMAIL = "admin@local.test"
STUDENT_NUMBER = "10000001"
PASSWORD = "localdev"

# The seeded voiceline is a generated track, 12 seconds long, with a short beep
# where each subtitle starts so the timing can be checked by ear.
VOICELINE_MS = 12000
# Several sentences per block, so the bar can be checked with text that wraps
# onto multiple lines the way real narration does.
SUBTITLES = [
    (0, 2800, {
        "en": "Welcome to the local test course. This slide is narrated by the "
              "course guide, and the subtitles follow along underneath. Use the "
              "menu under the guide to switch language or turn subtitles off.",
        "af": "Welkom by die plaaslike toetskursus. Hierdie skyfie word deur die "
              "kursusgids vertel, en die onderskrifte volg onderaan. Gebruik die "
              "keuselys onder die gids om van taal te verander of onderskrifte "
              "af te skakel."}),
    (3000, 5800, {
        "en": "This narration is a generated test tone, not a real voice. Each "
              "block of text is timed once against the English recording, and "
              "every other language reuses the same timing.",
        "af": "Hierdie vertelling is 'n gegenereerde toetstoon, nie 'n regte stem "
              "nie. Elke teksblok word een keer met die Engelse opname "
              "gesinchroniseer, en elke ander taal gebruik dieselfde tye."}),
    (6000, 8800, {
        "en": "Each beep marks the start of a new subtitle. Longer blocks like "
              "this one wrap onto several lines, which is useful for checking "
              "how the bar grows and whether it ever covers the buttons on the "
              "page. Real narration often runs to three or four sentences."}),
    (9000, 11800, {
        "en": "Tick the box below once the narration ends. Until then the "
              "checkbox and the Next button stay locked, and the server checks "
              "that the whole narration was actually heard."}),
]
GESTURES = [("wave", (199, 164, 52), "left"),
            ("point", (23, 48, 107), "right"),
            ("think", (4, 120, 87), None)]
GESTURE_CUES_MS = (0, 4000, 8000)


def _prepare_env():
    if REPO_DIR.startswith(("/var/devprof", "/var/enroll")):
        sys.exit("local_dev.py is for local machines only, not the servers.")
    # app.py puts its database at <cwd>/instance/students.db.
    os.chdir(REPO_DIR)
    sys.path.insert(0, REPO_DIR)
    # app.py reads these at import. The real values live only in the server .env.
    os.environ.setdefault("FLASK_SECRET_KEY", "local-dev-only")
    os.environ.setdefault("URLSAFE_SERIALIZER_KEY", "local-dev-only")


def _install_schema_hook():
    """Let app.py import against an empty database.

    app.py never calls db.create_all(). Its startup migrations (the _ensure_*
    helpers) inspect tables they assume already exist, so a fresh database
    fails at import. When one of them asks for the columns of a missing table,
    create every table defined so far from the models, then answer it.
    """
    from sqlalchemy import exc
    from sqlalchemy.engine import reflection

    original = reflection.Inspector.get_columns

    def get_columns(self, table_name, schema=None, **kw):
        try:
            return original(self, table_name, schema, **kw)
        except exc.NoSuchTableError:
            db = getattr(sys.modules.get("app"), "db", None)
            if db is None or table_name not in db.metadata.tables:
                raise
            db.metadata.create_all(bind=self.bind)
            self.info_cache.clear()
            return original(self, table_name, schema, **kw)

    reflection.Inspector.get_columns = get_columns


def _serve_uploads_like_nginx(app):
    """Serve files under uploads/ the way nginx does on the servers.

    There, nginx answers /uploads/ straight off disk before Flask sees the
    request (see _mascot_media_url in app.py). Flask's own /uploads routes only
    handle student files one folder deep, so without this, mascot audio and
    gesture images return 404 locally.
    """
    from flask import request, send_from_directory

    root = app.config["UPLOAD_FOLDER"]

    @app.before_request
    def _uploads_from_disk():
        if not request.path.startswith("/uploads/"):
            return None
        rel = request.path[len("/uploads/"):]
        if os.path.isfile(os.path.join(root, rel)):
            # send_from_directory refuses paths outside root; conditional=True
            # gives Range support, which audio seeking needs.
            return send_from_directory(root, rel, conditional=True)
        return None


def _add_missing_columns(m):
    """Add model columns that an existing local database does not have yet.

    On the servers a new column arrives through a migration or an _ensure_*
    helper in app.py. A local database built by an earlier `setup` gets
    neither, so a model that later gains a column (for example
    AssessmentAttempt.questions_json) fails with "no such column". Columns that
    can be added in place (nullable, or with a server default) are added; any
    other gap is reported. Nothing is ever dropped or altered.
    """
    from sqlalchemy import inspect as sa_inspect, text

    engine = m.db.engine
    insp = sa_inspect(engine)
    existing = set(insp.get_table_names())
    for table in m.db.metadata.tables.values():
        if table.name not in existing:
            continue
        have = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in have:
                continue
            if not col.nullable and col.server_default is None:
                print(f"  ! Local database is missing {table.name}.{col.name}, which "
                      f"cannot be added in place. Delete instance/students.db and "
                      f"uploads/, then run setup again.")
                continue
            ddl = (f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" '
                   f"{col.type.compile(dialect=engine.dialect)}")
            if col.server_default is not None:
                arg = col.server_default.arg
                ddl += " DEFAULT " + (arg.text if hasattr(arg, "text") else f"'{arg}'")
            with engine.begin() as conn:
                conn.execute(text(ddl))
            print(f"  + Added {table.name}.{col.name} to the local database")


def _load_app():
    _prepare_env()
    _install_schema_hook()
    import run_dev  # blocks all outgoing email, then imports app.py
    m = run_dev.app_module
    with m.app.app_context():
        # Tables for any model the startup migrations never touched, then
        # columns that models gained after this database was built.
        m.db.create_all()
        _add_missing_columns(m)
    _serve_uploads_like_nginx(m.app)
    return m


# ── Generated media (standard library only) ────────────────────────────────

def _png(width, height, pixel):
    """Encode an RGBA PNG; pixel(x, y) returns an (r, g, b, a) tuple."""
    raw = b"".join(
        b"\x00" + bytes(c for x in range(width) for c in pixel(x, y))
        for y in range(height))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def _figure_png(colour, arm):
    """A 1:2 placeholder figure. Each gesture differs by colour and raised arm."""
    fill = tuple(colour) + (255,)

    def pixel(x, y):
        body = ((x - 60) / 38) ** 2 + ((y - 165) / 68) ** 2 <= 1
        head = (x - 60) ** 2 + (y - 62) ** 2 <= 30 ** 2
        raised = ((arm == "left" and 14 <= x <= 26 and 40 <= y <= 140)
                  or (arm == "right" and 94 <= x <= 106 and 40 <= y <= 140))
        return fill if (body or head or raised) else (0, 0, 0, 0)

    return _png(120, 240, pixel)


def _face_png():
    def pixel(x, y):
        head = (x - 80) ** 2 + (y - 90) ** 2 <= 45 ** 2
        return (120, 130, 150, 255) if head else (226, 232, 240, 255)
    return _png(160, 200, pixel)


def _write_wav(path, length_ms, beep_starts_ms, rate=22050):
    total = rate * length_ms // 1000
    beep = [int(8000 * math.sin(2 * math.pi * 880 * i / rate))
            for i in range(rate * 150 // 1000)]
    samples = [0] * total
    for start in beep_starts_ms:
        s = rate * start // 1000
        for i, v in enumerate(beep):
            if s + i < total:
                samples[s + i] = v
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack(f"<{total}h", *samples))


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


# ── Seed data ──────────────────────────────────────────────────────────────

def _seed(m):
    from werkzeug.security import generate_password_hash

    db = m.db
    pw = generate_password_hash(PASSWORD)

    db.session.add(m.User(name="Local", surname="Admin", cell_number="0000000000",
                          email=ADMIN_EMAIL, role="Developer", password_hash=pw))

    # A student who has finished onboarding: verified (no pending OTP), POPIA
    # accepted, and with the selfie and ID files require_popia looks for.
    student = m.Student(student_id=STUDENT_NUMBER, name="Test", surname="Learner",
                        national_id="LOCAL000001", email="student@local.test",
                        cell_number="0000000000", password=pw,
                        selfie_filename=f"{STUDENT_NUMBER}_selfie.jpg")
    db.session.add(student)
    db.session.flush()
    db.session.add(m.PopiaConsent(student_id=student.id,
                                  version=m.app.config["POPIA_VERSION"]))
    db.session.flush()
    student.sync_legacy_popia_fields()
    # Only their existence is checked. PNG bytes under a .jpg name still
    # display in the browser.
    folder = os.path.join(m.app.config["UPLOAD_FOLDER"], STUDENT_NUMBER)
    for name in (f"{STUDENT_NUMBER}_selfie.jpg", f"{STUDENT_NUMBER}_id.jpg"):
        _write(os.path.join(folder, name), _face_png())

    course = m.Course(title="Local Test Course", category="Local",
                      description="Fake course for local development.")
    db.session.add(course)
    db.session.flush()
    slides = [
        ("Narrated slide with subtitles",
         "<h2>Narrated slide with subtitles</h2><p>Press play on the course "
         "guide. English and Afrikaans subtitles are available from the menu "
         "under it; Afrikaans is only partly translated.</p>"),
        ("Narrated slide without subtitles",
         "<h2>Narrated slide without subtitles</h2><p>The same narration, but "
         "no subtitles have been written, so no subtitle menu is offered.</p>"),
        ("Plain slide",
         "<h2>Plain slide</h2><p>No mascot on this slide.</p>"),
    ]
    chapters = []
    for pos, (title, html) in enumerate(slides, start=1):
        ch = m.CourseChapter(course_id=course.id, title=title, position=pos,
                             content=html, chapter_type="text")
        db.session.add(ch)
        chapters.append(ch)
    db.session.add(m.CourseEnrollment(student_id=student.id, course_id=course.id,
                                      approved=True))
    db.session.flush()

    gestures = []
    for pos, (name, colour, arm) in enumerate(GESTURES, start=1):
        fname = f"local_{name}.png"
        _write(os.path.join(m._mascot_abs_dir(m.MASCOT_GESTURE_DIR), fname),
               _figure_png(colour, arm))
        g = m.MascotGesture(name=name, position=pos,
                            image_path=f"{m.MASCOT_GESTURE_DIR}/{fname}")
        db.session.add(g)
        gestures.append(g)
    db.session.flush()

    for ch in chapters[:2]:
        # One file per slide: removing a slide's mascot deletes its audio file.
        fname = f"local_ch{ch.id}_voiceline.wav"
        _write_wav(os.path.join(m._mascot_abs_dir(m.MASCOT_AUDIO_DIR), fname),
                   VOICELINE_MS, [start for start, _, _ in SUBTITLES])
        mascot = m.ChapterMascot(chapter_id=ch.id, duration_ms=VOICELINE_MS,
                                 audio_path=f"{m.MASCOT_AUDIO_DIR}/{fname}",
                                 is_enabled=True, require_video=False)
        db.session.add(mascot)
        db.session.flush()
        for at_ms, g in zip(GESTURE_CUES_MS, gestures):
            db.session.add(m.MascotCue(mascot_id=mascot.id, gesture_id=g.id,
                                       at_ms=at_ms))
        if ch is chapters[0]:
            for seq, (start, end, texts) in enumerate(SUBTITLES):
                block = m.MascotSubtitle(mascot_id=mascot.id, start_ms=start,
                                         end_ms=end, seq=seq)
                db.session.add(block)
                db.session.flush()
                for lang, text in texts.items():
                    db.session.add(m.MascotSubtitleText(
                        subtitle_id=block.id, lang=lang, text=text))

    db.session.commit()
    return course, chapters


def _logins(port=8008):
    return (f"  Student: http://127.0.0.1:{port}/  "
            f"student number {STUDENT_NUMBER}, password {PASSWORD}\n"
            f"  Admin:   http://127.0.0.1:{port}/admin_login  "
            f"{ADMIN_EMAIL}, password {PASSWORD}")


def setup():
    m = _load_app()
    with m.app.app_context():
        if m.User.query.filter_by(email=ADMIN_EMAIL).first():
            print("\nLocal data is already set up.\n" + _logins())
            return
        if m.Student.query.count() or m.User.query.count():
            sys.exit("\ninstance/students.db already holds students or admins, "
                     "so it is not a local test database. local_dev.py only "
                     "seeds an empty one and never deletes anything.")
        course, chapters = _seed(m)
        print(f"\nSeeded '{course.title}' with {len(chapters)} slides.\n"
              + _logins()
              + f"\n  Mascot timeline editor: /admin/chapter/{chapters[0].id}/mascot"
              + "\n\nStart the app with: python local_dev.py run")


def run(port):
    m = _load_app()
    with m.app.app_context():
        if not m.User.query.filter_by(email=ADMIN_EMAIL).first():
            print("\nNo local test data yet. Run: python local_dev.py setup\n")
    print("\n" + _logins(port) + "\n")
    m.app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="create the local database and seed fake data")
    run_p = sub.add_parser("run", help="start the app locally")
    run_p.add_argument("--port", type=int, default=8008)
    args = parser.parse_args()
    if args.command == "setup":
        setup()
    else:
        run(args.port)


if __name__ == "__main__":
    main()
