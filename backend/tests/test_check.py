import stat

from app.config import settings


def _fake_pwsh(tmp_path, body):
    f = tmp_path / "pwsh"
    f.write_text("#!/bin/sh\n" + body)
    f.chmod(f.stat().st_mode | stat.S_IEXEC)
    return str(f)


def test_check_reports_server_failure_not_script_error(authed, monkeypatch, tmp_path):
    pid = authed.post("/api/packages", json={"name": "X"}).json()["id"]
    monkeypatch.setattr(settings, "pwsh_path", _fake_pwsh(tmp_path, "echo 'IOException: Read-only file system' >&2; exit 134\n"))
    r = authed.post(f"/api/packages/{pid}/check").json()
    assert r["errors"] == [] and "Read-only" in r["failed"]
    v = authed.get(f"/api/packages/{pid}/validate").json()
    assert not any(i["level"] == "error" for i in v["items"] if "PowerShell" in i["text"])


def test_check_gets_writable_home(authed, monkeypatch, tmp_path):
    pid = authed.post("/api/packages", json={"name": "X"}).json()["id"]
    monkeypatch.setattr(settings, "pwsh_path", _fake_pwsh(tmp_path, 'touch "$HOME/.probe" && echo "3:5 Missing brace"\n'))
    assert authed.post(f"/api/packages/{pid}/check").json()["errors"] == ["3:5 Missing brace"]
