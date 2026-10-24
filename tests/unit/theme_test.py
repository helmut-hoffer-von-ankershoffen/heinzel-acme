"""Acme's theme: valid as Heinzelmännchen checks it, and offered by the company module."""

import tomllib
from pathlib import Path

import pytest
from heinzel import Theme, ThemeLet

import heinzel_acme

pytestmark = pytest.mark.unit

THEME = Path(heinzel_acme.__file__).parent / "themes" / "acme.toml"


def test_the_acme_theme_is_valid_with_a_teal_primary_and_a_larger_radius():
    theme = Theme.model_validate(tomllib.loads(THEME.read_text(encoding="utf-8")))
    assert (theme.name, theme.title, theme.radius) == ("acme", "Acme", "0.75rem")
    assert (theme.light.primary, theme.dark.background) == ("#0f766e", "#0f172a")
    assert theme.font_sans.endswith("sans-serif")
    assert theme.font_mono.endswith("monospace")


def test_the_company_module_offers_it():
    offered = [let.theme for let in heinzel_acme.module.lets if isinstance(let, ThemeLet)]
    assert [theme.name for theme in offered] == ["acme"]
    assert offered[0].light.primary == "#0f766e"
