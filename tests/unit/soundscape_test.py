"""The Acme theme's sound is a checked stream declaration, with no downloaded media."""

import pytest
from heinzel import SoundscapeLet

import heinzel_acme

pytestmark = pytest.mark.unit


def test_the_module_registers_the_requested_video_paired_only_with_its_theme():
    (let,) = [let for let in heinzel_acme.module.lets if isinstance(let, SoundscapeLet)]
    sound = let.soundscape
    assert (sound.name, sound.title, sound.kind, sound.pairs_with) == ("acme", "Acme", "stream", ("acme",))
    assert (sound.stream.provider, sound.stream.video) == ("youtube", "t9PF00M2yDY")
    assert sound.assets() == {}
