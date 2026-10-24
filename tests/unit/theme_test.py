"""Acme's theme: valid as Heinzelmännchen checks it, and offered by the company module."""

import tomllib
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from heinzel import Theme, ThemeLet

import heinzel_acme

pytestmark = pytest.mark.unit

THEME = Path(heinzel_acme.__file__).parent / "themes" / "acme.toml"


def test_the_acme_theme_is_valid_with_a_teal_primary_and_square_corners():
    theme = Theme.model_validate(tomllib.loads(THEME.read_text(encoding="utf-8")))
    assert (theme.name, theme.title, theme.radius, theme.radius_control) == ("acme", "Acme", "0", "0")
    assert (theme.light.primary, theme.dark.background) == ("#0f766e", "#0f172a")
    assert theme.font_sans.endswith("sans-serif")
    assert theme.font_mono.endswith("monospace")


def test_the_company_module_offers_it():
    offered = [let.theme for let in heinzel_acme.module.lets if isinstance(let, ThemeLet)]
    assert [theme.name for theme in offered] == ["acme"]
    assert offered[0].light.primary == "#0f766e"


LOGO_FILES = ("logo/mark.svg", "logo/wordmark-light.svg", "logo/wordmark-dark.svg")
MAX_LOGO_BYTES = 200 * 1024


@pytest.mark.parametrize("file", LOGO_FILES)
def test_logo_files_are_small_clean_svgs_inside_the_theme_directory(file):
    root = THEME.parent.resolve()
    path = (THEME.parent / file).resolve(strict=True)
    assert path.is_relative_to(root)
    assert path.stat().st_size <= MAX_LOGO_BYTES
    svg = ET.fromstring(path.read_bytes())  # noqa: S314 - our own file, checked for what it may not hold
    assert svg.tag == "{http://www.w3.org/2000/svg}svg"
    for element in svg.iter():
        assert element.tag.rsplit("}", 1)[-1] not in {"script", "foreignObject", "image", "use", "a", "style"}
        for attribute in element.attrib:
            name = attribute.rsplit("}", 1)[-1].lower()
            assert not name.startswith("on"), (file, attribute)
            assert name != "href", (file, attribute)
    assert b"url(" not in path.read_bytes()


def test_the_logo_is_acme_teal_light_and_dark():
    assert 'fill="#0f766e"' in (THEME.parent / "logo" / "wordmark-light.svg").read_text(encoding="utf-8")
    assert 'fill="#2dd4bf"' in (THEME.parent / "logo" / "wordmark-dark.svg").read_text(encoding="utf-8")
    assert 'fill="#0d9488"' in (THEME.parent / "logo" / "mark.svg").read_text(encoding="utf-8")


def test_the_theme_declares_the_logo_and_heinzel_serves_it():
    theme = Theme.model_validate(tomllib.loads(THEME.read_text(encoding="utf-8")))
    assert theme.logo is not None
    assert (theme.logo.light, theme.logo.dark, theme.logo.mark) == LOGO_FILES[1:] + LOGO_FILES[:1]
    assert (theme.logo.alt, theme.logo.height) == ("Acme", "24px")
    (let,) = [let for let in heinzel_acme.module.lets if isinstance(let, ThemeLet)]
    logos = let.logos()
    assert logos is not None
    for name, file in zip(("light", "dark", "mark"), LOGO_FILES[1:] + LOGO_FILES[:1], strict=True):
        assert logos.content(name) == (THEME.parent / file).read_bytes()
        assert logos.url(name).startswith(f"/theme-assets/acme/{name}.svg?v=")
