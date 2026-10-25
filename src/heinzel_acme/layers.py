"""Where Acme's layers are declared: the one place that bridges to the core's layer API (Heinzelmännchen ADR 0040).

LAYER API BRIDGE. Every Acme plugin declares its place in the company's tree with `declare(module, parent=...,
site=..., roles=...)`, the same arguments as the core's `Module.layer(...)`. When the installed Heinzelmännchen has
`Module.layer` (the pull request "plugins are layers with a parent, stacked general to specific"), `declare` calls it,
so the kernel stacks the layers and `hz system layer list` shows them. When it hasn't, `declare` records the layer
here only, `hz acme layers` shows the tree, and nothing else changes.

Once the pinned Heinzelmännchen has `Module.layer`, replace each `declare(module, ...)` with `module.layer(...)`, keep
`hz acme layers` or drop it in favour of `hz system layer list`, and delete this module (`git grep "layers.declare"`
finds every call).
"""

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, cast

from heinzel import Module

NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
"""A layer's module name: lowercase words joined by single dashes, its path from the root (ADR 0040 §5)."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Layer:
    """One layer of the company's tree, as its plugin declares it."""

    name: str
    """The module's name: its path from the root joined with dashes, e.g. `acme-payments-checkout`."""
    parent: str | None
    """The layer above, e.g. `acme-payments`; none for the root (the company)."""
    site: str | None
    """The site layer it is at, e.g. `acme-lisbon`; only a team names one."""
    roles: tuple[str, ...]
    """Roles it adds to the core's vocabulary for everyone whose stack includes it."""
    native: bool
    """Whether the installed Heinzelmännchen's `Module.layer` took the declaration too."""


_DECLARED: dict[str, Layer] = {}


def _check(name: str, parent: str | None, site: str | None, roles: tuple[str, ...]) -> None:
    for value in (name, parent, site, *roles):
        if value is not None and not NAME.fullmatch(value):
            msg = f"{value!r} isn't a layer or role name: lowercase words joined by single dashes"
            raise ValueError(msg)
    if parent is not None and not name.startswith(f"{parent}-"):
        msg = f"Layer {name!r} must be named after its path: its parent {parent!r} plus a dash and its own name"
        raise ValueError(msg)
    if name in {parent, site} or (site is not None and site == parent):
        msg = f"Layer {name!r}: a layer is neither its own parent nor site, and its site is never its parent"
        raise ValueError(msg)


def declare(module: Module, *, parent: str | None = None, site: str | None = None, roles: Iterable[str] = ()) -> Layer:
    """Declare that `module`'s plugin is a layer: below `parent`, at `site`, adding `roles`.

    Raises:
        ValueError: If a name is malformed, the name doesn't follow the parent's path, or the layer is its own parent
            or site.
    """
    role_names = tuple(roles)
    _check(module.name, parent, site, role_names)
    native = cast("Callable[..., Any] | None", getattr(module, "layer", None))
    if native is not None:
        native(parent=parent, site=site, roles=role_names)
    layer = Layer(name=module.name, parent=parent, site=site, roles=role_names, native=native is not None)
    _DECLARED[module.name] = layer
    return layer


def declared() -> list[Layer]:
    """Every layer the imported Acme plugins declared, root first, then by name along the tree."""
    return sorted(_DECLARED.values(), key=lambda layer: (layer.parent is not None, layer.name))


def stack(name: str) -> list[str]:
    """The stack of layer `name`, general to specific: the root, each org down to it, then its site, then it.

    Raises:
        KeyError: If `name`, or a layer it names, wasn't declared (its plugin isn't installed).
    """
    layer = _DECLARED[name]
    chain = [layer.name]
    while (parent := _DECLARED[chain[0]].parent) is not None:
        chain.insert(0, parent)
    if layer.site is not None:
        _DECLARED[layer.site]
        chain.insert(len(chain) - 1, layer.site)
    return chain


def label(layer: Layer) -> str:
    """What people call the layer, derived from where it sits (ADR 0040 §1): company, site, team or org."""
    if layer.parent is None:
        return "company"
    if any(other.site == layer.name for other in _DECLARED.values()):
        return "site"
    if layer.site is not None or not any(other.parent == layer.name for other in _DECLARED.values()):
        return "team"
    return "org"
