"""Models returned by the company plugin's operations, and shared by ACME's other layers."""

from pydantic import BaseModel, Field


class LayerView(BaseModel):
    """One layer of ACME's tree."""

    name: str = Field(description="Its module name: its path from the root, joined with dashes.")
    label: str = Field(description="What people call it, from where it sits: company, org, site or team.")
    parent: str | None = Field(description="The layer above; none for the company.")
    site: str | None = Field(description="The site it is at; only a team names one.")
    roles: list[str] = Field(description="Roles it adds to the core's vocabulary.")
    stack: list[str] = Field(description="Its stack, general to specific; empty when a layer it names is missing.")
    native: bool = Field(description="Whether the core's layer API took the declaration (`hz system layer list`).")


class LayerList(BaseModel):
    """`hz acme layers`: ACME's layers that are installed, and what is missing."""

    layers: list[LayerView] = Field(description="Root first.")
    missing: list[str] = Field(description="Layers named as a parent or site whose plugin isn't installed.")


class BindingView(BaseModel):
    """A capability binding the company recommends, and whether it is in effect."""

    capability: str = Field(description="The capability.")
    setting: str = Field(description="The setting that binds it, as `hz system config set` takes it.")
    adapter: str = Field(description="The adapter ACME binds to it.")
    plugin: str = Field(description="The plugin that brings the adapter.")
    transport: str = Field(description="What the adapter talks through.")
    login: str = Field(description="What you run once so it reads as you.")
    installed: bool = Field(description="Whether the adapter's plugin is installed.")
    bound: str | None = Field(description="The adapter your configuration binds to it now, if any.")


class LayerAbout(BaseModel):
    """What an ACME plugin is: its distribution and version, its place in the tree and what it brings."""

    plugin: str = Field(description="Distribution name of the plugin.")
    version: str = Field(description="Installed version of the plugin.")
    heinzel_version: str = Field(description="Version of the Heinzelmännchen it runs in.")
    layer: LayerView | None = Field(description="Its place in ACME's tree.")
    brings: list[str] = Field(description="What this layer contributes, in words.")


class AcmeAbout(LayerAbout):
    """The company plugin: its layer and the bindings it recommends."""

    bindings: list[BindingView] = Field(description="The capability bindings ACME recommends.")
