import pytest
from heinzel import Kernel, __version__

from heinzel_acme import AcmeService, AcmeSettings

pytestmark = pytest.mark.unit


def test_about_describes_plugin_without_modules_in_an_empty_kernel():
    about = AcmeService(Kernel(), AcmeSettings()).about()
    assert about.plugin == "heinzel-acme"
    assert about.heinzel_version == __version__
    assert about.modules == []


def test_greet_uses_the_configured_greeting():
    service = AcmeService(Kernel(), AcmeSettings(greeting="Hi"))
    assert service.greet("Ada").text == "Hi, Ada!"
