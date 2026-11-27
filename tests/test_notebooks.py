import runpy
from pathlib import Path

import pytest

pytest.importorskip("marimo")

NOTEBOOKS = sorted((Path(__file__).parents[1] / "notebooks").glob("*.py"))


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_runs_headless(notebook: Path) -> None:
    runpy.run_path(str(notebook), run_name="__main__")
