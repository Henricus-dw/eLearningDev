# Dev-only launcher. Imports the main app and applies dev overrides:
#   - smtplib neutered           (no real emails go out, by any route)
#   - MAIL_SUPPRESS_SEND = True  (no real emails go out via Flask-Mail)
#   - port 8008                  (matches nginx upstream)
# Survives future uploads of app.py because it lives alongside it.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# MAIL_SUPPRESS_SEND only covers Flask-Mail's mail.send(). app.py also opens raw
# smtplib.SMTP connections directly (search: "smtplib.SMTP(") which ignore it
# entirely, so on dev — which now carries a copy of live student records — those
# paths would email real students. Neuter smtplib at the module level before
# app.py is imported; it binds "import smtplib", so attribute lookup at call
# time resolves to the stub below no matter where the call site lives.
import smtplib


class _BlockedSMTP:
    def __init__(self, *args, **kwargs):
        print(f"[run_dev] BLOCKED outbound SMTP: {args[:2]}", flush=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def _noop(self, *args, **kwargs):
        return {}  # sendmail() contract: dict of per-recipient failures

    def __getattr__(self, name):
        return self._noop


smtplib.SMTP = _BlockedSMTP
smtplib.SMTP_SSL = _BlockedSMTP

import app as app_module
app_module.app.config['MAIL_SUPPRESS_SEND'] = True

# Flask-Mail captures MAIL_SUPPRESS_SEND when `mail = Mail(app)` runs during
# app.py's import, and Mail.send() checks that captured copy — not app.config.
# Setting the config here is therefore ignored on its own, which is why the
# smtplib stub above is the guard that actually stops mail. Force the captured
# flag as well so both layers agree.
for _target in (getattr(app_module, 'mail', None),
                getattr(getattr(app_module, 'mail', None), 'state', None)):
    if _target is not None and hasattr(_target, 'suppress'):
        _target.suppress = True

_suppressed = getattr(getattr(app_module, 'mail', None), 'state', None)
print(f"[run_dev] smtplib blocked; Flask-Mail suppress="
      f"{getattr(_suppressed, 'suppress', 'unknown')} (no emails will be sent)",
      flush=True)

# Guarded so local_dev.py can import this module for its email blocking without
# starting a second server. deploy-dev.sh runs this file directly, so on the dev
# server this block always runs.
if __name__ == "__main__":
    print("[run_dev] Listening on 127.0.0.1:8008", flush=True)
    app_module.app.run(host="127.0.0.1", port=8008, debug=True, use_reloader=False)
