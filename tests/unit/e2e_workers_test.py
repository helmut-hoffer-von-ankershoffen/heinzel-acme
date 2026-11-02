"""End-to-end modules that share one `uv tool install` run it once, on one xdist worker.

Three workers each building the module's `hz` fixture ran three `uv tool install` into one UV_CACHE_DIR at once; on a
cold cache one lost its temporary file before the rename and the release pull request's CI failed (11-02).
"""

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def lives_per_module(decorator: ast.expr) -> bool:
    """Whether a decorator is a fixture that lives as long as the module or session (one per worker under xdist)."""
    return isinstance(decorator, ast.Call) and any(
        k.arg == "scope" and isinstance(k.value, ast.Constant) and k.value.value in {"module", "session"}
        for k in decorator.keywords
    )


def module_scoped_fixtures(tree: ast.Module) -> list[str]:
    """Names of the fixtures in a test module that are built once per worker."""
    return [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and any(lives_per_module(d) for d in node.decorator_list)
    ]


def has_xdist_group(tree: ast.Module) -> bool:
    """Whether the module-level pytestmark puts the module in an xdist group."""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets):
            return "xdist_group" in ast.unparse(node.value)
    return False


def test_an_e2e_module_with_a_shared_install_stays_on_one_worker():
    modules = sorted((ROOT / "tests" / "e2e").glob("*_test.py"))
    assert modules
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if module_scoped_fixtures(tree):
            assert has_xdist_group(tree), f"{path.name}: a module-scoped fixture needs pytest.mark.xdist_group"


def test_make_test_e2e_honours_the_groups():
    recipe = re.search(r"^test-e2e:.*\n\t(.*)$", (ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    assert recipe
    assert "--dist loadgroup" in recipe[1], "without --dist loadgroup, xdist ignores xdist_group"
