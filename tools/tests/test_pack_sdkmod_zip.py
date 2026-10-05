"""SDK packaging must not destroy a previous build on invalid input or write failure."""
import zipfile

import pytest

from pack_sdkmod_zip import pack_sdkmod


@pytest.mark.parametrize("existing_stage", [False, True])
def test_missing_or_empty_stage_preserves_previous_package(tmp_path, existing_stage):
    stage = tmp_path / "stage"
    if existing_stage:
        stage.mkdir()
    output = tmp_path / "test.sdkmod"
    output.write_bytes(b"previous build")
    with pytest.raises(ValueError):
        pack_sdkmod(stage, output)
    assert output.read_bytes() == b"previous build"


def test_output_inside_stage_is_rejected(tmp_path):
    output = tmp_path / "test.sdkmod"
    output.write_bytes(b"previous build")
    with pytest.raises(ValueError):
        pack_sdkmod(tmp_path, output)
    assert output.read_bytes() == b"previous build"


def test_write_failure_preserves_package_and_removes_temporary_file(tmp_path, monkeypatch):
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "module.py").write_text("VALUE = 1", encoding="utf-8")
    output = tmp_path / "test.sdkmod"
    output.write_bytes(b"previous build")

    def fail(*args, **kwargs):
        raise OSError("simulated write failure")

    monkeypatch.setattr(zipfile.ZipFile, "write", fail)
    with pytest.raises(OSError, match="simulated write failure"):
        pack_sdkmod(stage, output)
    assert output.read_bytes() == b"previous build"
    assert not list(tmp_path.glob("*.tmp"))


def test_success_replaces_package_with_relative_archive_members(tmp_path):
    stage = tmp_path / "stage"
    package = stage / "Example"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1", encoding="utf-8")
    output = tmp_path / "test.sdkmod"
    output.write_bytes(b"previous build")
    assert pack_sdkmod(stage, output) == output
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == ["Example/__init__.py"]
        assert archive.read("Example/__init__.py") == b"VALUE = 1"
        assert archive.testzip() is None
    assert not list(tmp_path.glob("*.tmp"))
