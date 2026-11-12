from app.psadt.generator import args


def test_plain_args_stay_literal():
    assert args("/S /D=$x") == "'/S /D=$x'"


def test_files_placeholder_expands_and_escapes():
    out = args('--msix-path "{Files}\\app.msix" --cost $5')
    assert out == '"--msix-path `"$($adtSession.DirFiles)\\app.msix`" --cost `$5"'
