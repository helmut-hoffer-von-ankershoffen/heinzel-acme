"""The plugin's logic, independent of any head."""

from importlib.metadata import PackageNotFoundError, version

from heinzel import Kernel, __version__

from heinzel_acme._models import AcmeAbout, AcmeGreeting, AcmeSettings

DISTRIBUTION = "heinzel-acme"


class AcmeService:
    """Everything the acme modules do; operations stay thin and call into it."""

    def __init__(self, kernel: Kernel, settings: AcmeSettings) -> None:
        """Create the service; the kernel and the plugin's settings are injected."""
        self._kernel = kernel
        self._settings = settings

    def about(self) -> AcmeAbout:
        """Describe the plugin and the Heinzelmännchen installation it runs in."""
        try:
            installed = version(DISTRIBUTION)
        except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled source tree
            installed = "0.0.0"
        return AcmeAbout(
            plugin=DISTRIBUTION,
            version=installed,
            heinzel_version=__version__,
            modules=[r.qualname for r in self._kernel.modules if r.origin.distribution == DISTRIBUTION],
        )

    def greet(self, name: str) -> AcmeGreeting:
        """Greet someone by name, the way the settings say."""
        return AcmeGreeting(text=f"{self._settings.greeting}, {name}!")
