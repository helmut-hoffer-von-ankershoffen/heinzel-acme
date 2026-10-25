"""Acme, a made-up company: the root layer of the reference company.

A Heinzelmännchen plugin, discovered through the `heinzel.modules` entry point in pyproject.toml. Every package
below it that declares `module = Module(...)` becomes a submodule (see `hello/`). Acme's look for the web app is
data in `themes/` (`hz system theme use acme`).
"""

from pathlib import Path

from heinzel import ConfigEditor, Module, Prompter

from heinzel_acme._models import AcmeAbout, AcmeSettings
from heinzel_acme._service import AcmeService

module = Module("acme", "Acme, a made-up company: the root layer of the reference company.")
module.settings(AcmeSettings)
module.service(AcmeService)
module.theme(Path(__file__).parent / "themes")  # read and checked now; `hz system theme list` shows it
module.soundscape(Path(__file__).parent / "soundscapes")


@module.operation
def info(service: AcmeService) -> AcmeAbout:
    """Show this plugin's version, the Heinzelmännchen it runs on and the modules it brings."""
    return service.about()


@module.info
def system_info(service: AcmeService) -> AcmeAbout:
    """Contribute this plugin's details to `hz system info`."""
    return service.about()


@module.setup(required=False)  # optional: `hz setup` offers to skip it; `hz setup acme` runs it alone
def setup(settings: AcmeSettings, prompter: Prompter, editor: ConfigEditor) -> None:
    """Choose how `hello` greets."""
    greeting = prompter.text("How should `hello` greet?", default=settings.greeting)
    path = editor.write("acme.greeting", greeting)  # validated like `hz system config set`, user scope
    prompter.say(f"Saved to {path}.")


__all__ = ["AcmeAbout", "AcmeService", "AcmeSettings", "module"]
