import importlib
import pkgutil

import pytest

import blackjack_lab

MODULES = sorted(
    info.name
    for info in pkgutil.walk_packages(blackjack_lab.__path__, f"{blackjack_lab.__name__}.")
)


@pytest.mark.parametrize("module", MODULES)
def test_module_imports_cleanly(module: str) -> None:
    assert importlib.import_module(module).__name__ == module
