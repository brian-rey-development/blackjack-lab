import pkgutil
import sys

import blackjack_lab

BANNED_NAMES = frozenset({"utils", "helpers", "common", "misc", "shared", "types"})
MODULE_NAMES = frozenset(
    info.name.rsplit(".", 1)[-1]
    for info in pkgutil.walk_packages(blackjack_lab.__path__, f"{blackjack_lab.__name__}.")
)


def test_no_module_has_a_vague_name() -> None:
    assert not MODULE_NAMES & BANNED_NAMES


def test_no_module_shadows_the_standard_library() -> None:
    assert not MODULE_NAMES & sys.stdlib_module_names
