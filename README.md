# eLearning (Professional Aviation Training)

Flask app for enrolment, course delivery, assessments and the company portal.
Almost everything lives in `app.py`, with pages in `templates/`.

## Running it locally

You need Python 3.13 (3.14 has not been tried yet).

```bash
# Windows
py -3.13 -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3.13 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python local_dev.py setup    # once: creates instance/students.db with fake data
python local_dev.py run      # http://127.0.0.1:8008
```

`setup` prints the logins. They are always the same:

| Who     | Where                                | Login                              |
|---------|--------------------------------------|------------------------------------|
| Student | http://127.0.0.1:8008/               | student number `10000001` / `localdev` |
| Admin   | http://127.0.0.1:8008/admin_login    | `admin@local.test` / `localdev` (Developer role) |

The fake data is one fully onboarded student enrolled on a three-slide "Local
Test Course":
- slide 1 has mascot narration with English and partly translated Afrikaans subtitles
- slide 2 has narration but no subtitles
- slide 3 is a plain slide

The voiceline is a generated track that beeps where each subtitle starts.

Good to know:
- **No email is sent.** `local_dev.py` runs the app through `run_dev.py`,
  which blocks all outgoing mail.
- **Everything local stays out of git.** The database is `instance/students.db`
  and files go in `uploads/`. Both are in `.gitignore`.
- **Starting over.** Delete `instance/students.db` and `uploads/`, then run
  `setup` again. `setup` never deletes anything itself. It refuses to touch a
  database that already has students or admins in it.
- **Missing extras.** Attendance register PDFs need WeasyPrint, which isn't
  installed by default. Word document conversion needs the `pandoc` program.
  Neither is needed for course content work.

## Contributing

- Never copy `instance/`, uploads, student data, backups or the server `.env`
  to your machine or into the repository.
- Work on a branch and open a pull request into `main`:

  ```bash
  git checkout main
  git pull
  git checkout -b your-change
  # make and test the change locally
  git add <the files you changed>
  git commit -m "Describe the change"
  git push -u origin your-change
  ```

- Once a pull request is merged into `main`, GitHub deploys it automatically
  to the **dev** app (port 8008). Production is never deployed from here, and
  repository access does not give server or SSH access.
