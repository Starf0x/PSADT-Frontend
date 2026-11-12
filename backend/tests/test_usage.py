from datetime import datetime

from app import db as dbmod
from app import usage


def test_report_once_daily_and_after_update(client, monkeypatch, tmp_path):
    monkeypatch.delenv("PSADT_USAGE_OPTOUT")
    monkeypatch.setattr(usage, "DEFAULT_URL", "https://collector.invalid/webhook")
    monkeypatch.setattr(usage, "DEFAULT_TOKEN", "test")
    sent = []
    with dbmod.SessionLocal() as db:
        now = datetime(2026, 11, 12, 9, 0)
        body = usage.report_once(db, "0.2.66", now, post=lambda u, t, b: sent.append(b))
        assert body["appName"] == "PSADT Frontend" and body["days"] == 1 and len(body["computerName"]) == 36
        assert usage.report_once(db, "0.2.66", now, post=lambda u, t, b: sent.append(b)) is None  # once a day
        assert usage.report_once(db, "0.2.77", now, post=lambda u, t, b: sent.append(b))["version"] == "0.2.77"
        later = usage.report_once(db, "0.2.77", datetime(2026, 11, 14, 9, 0), post=lambda u, t, b: sent.append(b))
        assert later["days"] == 3 and len(sent) == 3


def test_opt_out_env(client, monkeypatch):
    with dbmod.SessionLocal() as db:  # conftest sets PSADT_USAGE_OPTOUT=1
        assert usage.report_once(db, "1", post=lambda *a: (_ for _ in ()).throw(AssertionError())) is None


def test_platform(tmp_path):
    assert usage.platform(str(tmp_path)) == "other"
    (tmp_path / ".dockerenv").write_text("")
    assert usage.platform(str(tmp_path)) == "docker"
