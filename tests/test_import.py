from importlib.metadata import version
from pathlib import Path

from packaging.version import Version

import visualific

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_pep440():
    Version(visualific.__version__)


def test_installed_metadata_matches_package():
    assert version("visualific") == visualific.__version__


def test_citation_file_matches_package():
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert f"version: {visualific.__version__}" in citation.splitlines()
