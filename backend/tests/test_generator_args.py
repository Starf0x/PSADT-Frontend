from app.psadt.generator import args


def test_plain_args_stay_literal():
    assert args("/S /D=$x") == "'/S /D=$x'"


def test_files_placeholder_expands_and_escapes():
    out = args('--msix-path "{Files}\\app.msix" --cost $5')
    assert out == '"--msix-path `"$($adtSession.DirFiles)\\app.msix`" --cost `$5"'


def test_exe_windows_program():
    from app.psadt.generator import _exe
    from app.psadt.schema import ExeStep
    assert "winget.exe" in _exe("windows:winget.exe") and "WindowsApps" in _exe("windows:winget.exe")
    assert _exe("windows:msiexec.exe") == '"$env:SystemRoot\\System32\\msiexec.exe"'
    assert _exe("setup.exe") == '"$($adtSession.DirFiles)\\setup.exe"'
    ExeStep(type="exe", file="windows:winget.exe")
    import pytest
    with pytest.raises(ValueError):
        ExeStep(type="exe", file="windows:evil.exe")
