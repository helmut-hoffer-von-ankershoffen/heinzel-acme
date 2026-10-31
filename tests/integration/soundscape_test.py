"""The installed entry point exposes the requested stream, and the built wheel carries its checked data."""

import json
import shutil
import subprocess
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path

import pytest
from heinzel.heads.cli import build
from typer.testing import CliRunner

pytestmark = pytest.mark.integration
ROOT = Path(__file__).parents[2]


def invoke(kernel, *args):
    result = CliRunner().invoke(build(kernel), [*args, "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_list_and_selection_keep_sound_off_until_the_person_chooses(boot):
    kernel = boot()
    listed = invoke(kernel, "system", "sound", "list")
    assert (listed["selected"], listed["effective"], listed["follow_theme"]) == ("off", "off", False)
    (sound,) = [sound for sound in listed["soundscapes"] if sound["name"] == "acme"]
    assert (sound["title"], sound["plugin"], sound["kind"]) == ("ACME", "heinzel-acme", "stream")
    assert sound["stream"]["embed_url"] == "https://www.youtube-nocookie.com/embed/t9PF00M2yDY"
    assert sound["stream"]["watch_url"] == "https://www.youtube.com/watch?v=t9PF00M2yDY"
    assert invoke(kernel, "system", "sound", "use", "acme")["effective"] == "acme"
    assert invoke(kernel, "system", "sound", "use", "off")["effective"] == "off"


def test_follow_theme_uses_the_acme_stream_only_for_the_acme_theme(boot):
    kernel = boot()
    invoke(kernel, "system", "config", "set", "system.sound.follow_theme", "true")
    assert invoke(kernel, "system", "sound", "list")["effective"] == "off"
    invoke(kernel, "system", "theme", "use", "acme")
    listed = invoke(kernel, "system", "sound", "list")
    assert (listed["selected"], listed["effective"]) == ("off", "acme")
    invoke(kernel, "system", "theme", "use", "default")
    assert invoke(kernel, "system", "sound", "list")["effective"] == "off"


def test_the_wheel_contains_the_exact_stream_manifest_and_no_media(tmp_path):
    uv = shutil.which("uv")
    assert uv is not None
    subprocess.run(
        [uv, "build", "--offline", "--wheel", "--out-dir", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    (wheel,) = tmp_path.glob("*.whl")
    member = "heinzel_acme/soundscapes/acme.toml"
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = BytesParser().parsebytes(archive.read(metadata_name))
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
        assert metadata["Version"] == project["version"] != "0.0.0"
        assert "heinzel<1,>=0.7.2" in metadata.get_all("Requires-Dist")
        assert archive.read(member) == (ROOT / "src" / member).read_bytes()
        assert not any(name.endswith((".mp3", ".ogg", ".opus", ".mp4")) for name in archive.namelist())
