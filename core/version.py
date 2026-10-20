"""Application version loaded from the project metadata as the single source."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def _metadata_path() -> Path:
    executable_directory = Path(sys.argv[0]).resolve().parent
    candidates = (
        executable_directory / "pyproject.toml",
        Path(__file__).resolve().parents[1] / "pyproject.toml",
    )
    return next((path for path in candidates if path.is_file()), candidates[-1])


def load_app_version() -> str:
    metadata = tomllib.loads(_metadata_path().read_text(encoding="utf-8"))
    version = metadata.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError("pyproject.toml does not define a project version.")
    return version


APP_VERSION = load_app_version()
