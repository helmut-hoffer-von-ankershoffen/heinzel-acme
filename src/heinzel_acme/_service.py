"""The company plugin's logic: its layer, the layer tree, and how its recommended bindings stand."""

from importlib.metadata import PackageNotFoundError, version

from heinzel import Check, Status, __version__
from heinzel.kernel import CapabilityView

from heinzel_acme import layers
from heinzel_acme._bindings import BINDINGS
from heinzel_acme._models import AcmeAbout, BindingView, LayerAbout, LayerList, LayerView

DISTRIBUTION = "heinzel-acme"
COMPANY = "acme"


def installed_version(distribution: str) -> str:
    """The installed version of `distribution`, or 0.0.0 from an uninstalled source tree."""
    try:
        return version(distribution)
    except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled source tree
        return "0.0.0"


def layer_view(name: str) -> LayerView | None:
    """Layer `name` as people read it, or None if its plugin declared none."""
    layer = next((found for found in layers.declared() if found.name == name), None)
    if layer is None:
        return None
    try:
        stack = layers.stack(name)
    except KeyError:
        stack = []
    return LayerView(
        name=layer.name,
        label=layers.label(layer),
        parent=layer.parent,
        site=layer.site,
        roles=list(layer.roles),
        stack=stack,
        native=layer.native,
    )


def about_layer(distribution: str, name: str, brings: list[str]) -> LayerAbout:
    """What an Acme plugin is; each layer's `info` operation returns it."""
    return LayerAbout(
        plugin=distribution,
        version=installed_version(distribution),
        heinzel_version=__version__,
        layer=layer_view(name),
        brings=brings,
    )


class AcmeService:
    """What the company plugin knows: Acme's layer tree and its recommended bindings."""

    def __init__(self, view: CapabilityView) -> None:
        """Create the service; the kernel injects what modules may know about capabilities."""
        self._view = view

    def bindings(self) -> list[BindingView]:
        """Each binding Acme recommends, whether its adapter is installed and what is bound now."""
        return [
            BindingView(
                capability=b.capability,
                setting=b.setting,
                adapter=b.adapter,
                plugin=b.plugin,
                transport=b.transport,
                login=b.login,
                installed=b.adapter in self._view.installed(b.capability),
                bound=self._view.bound(b.capability),
            )
            for b in BINDINGS
        ]

    def about(self) -> AcmeAbout:
        """The company plugin, its layer and its bindings."""
        base = about_layer(
            DISTRIBUTION,
            COMPANY,
            [
                "capability bindings: code host, tracker, documents, calendar, mail, meetings (hz setup acme)",
                "roles: tech-lead, report-owner",
                "hz acme seed: the made-up Acme world for a rehearsal, in your own trial accounts",
            ],
        )
        return AcmeAbout(**base.model_dump(), bindings=self.bindings())

    @staticmethod
    def layers() -> LayerList:
        """The installed Acme layers, root first, and the layers they name that aren't installed."""
        declared = layers.declared()
        names = {layer.name for layer in declared}
        named = {n for layer in declared for n in (layer.parent, layer.site) if n is not None}
        views = [view for layer in declared if (view := layer_view(layer.name)) is not None]
        return LayerList(layers=views, missing=sorted(named - names))

    def checks(self) -> list[Check]:
        """For `hz system doctor`: missing layers, and each recommended binding's adapter and configuration."""
        checks: list[Check] = []
        if missing := self.layers().missing:
            checks.append(
                Check(
                    name="acme layers",
                    status=Status.DEGRADED,
                    detail=f"named but not installed: {', '.join(missing)}",
                    fix="Install the plugin of each, e.g. hz system plugin add <path or git URL of heinzel-<layer>>",
                )
            )
        for binding in self.bindings():
            name = f"acme binding {binding.capability}"
            if not binding.installed:
                checks.append(
                    Check(
                        name=name,
                        status=Status.DEGRADED,
                        detail=f"Acme reads {binding.capability} through {binding.adapter}, which isn't installed",
                        fix=f"hz system plugin add {binding.plugin}, then {binding.login}",
                    )
                )
            elif binding.bound not in {binding.adapter, None}:  # the person's choice wins over the company's
                checks.append(
                    Check(name=name, status=Status.UP, detail=f"you bound {binding.bound}; Acme uses {binding.adapter}")
                )
            elif binding.bound is None:
                checks.append(
                    Check(
                        name=name,
                        status=Status.DEGRADED,
                        detail=f"nothing bound to it; Acme recommends {binding.adapter}",
                        fix=f"hz setup acme, or hz system config set {binding.setting} {binding.adapter}",
                    )
                )
            else:
                checks.append(Check(name=name, status=Status.UP, detail=f"{binding.adapter}: {binding.transport}"))
        return checks
