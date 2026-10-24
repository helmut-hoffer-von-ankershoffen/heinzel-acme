"""A submodule. Its only operation shares its name, so the CLI collapses it to `hz acme hello`."""

from typing import Annotated

from heinzel import Module
from pydantic import Field

from heinzel_acme._models import AcmeGreeting
from heinzel_acme._service import AcmeService

module = Module("hello", "Greet someone.")


@module.operation
def hello(
    service: AcmeService,
    name: Annotated[str, Field(description="Who to greet.")] = "world",
) -> AcmeGreeting:
    """Greet someone by name."""
    return service.greet(name)
