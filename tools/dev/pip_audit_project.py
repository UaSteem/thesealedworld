"""Run pip-audit in the existing project .venv, never in a hook environment.

This gate does not install packages, synchronize dependencies, or alter locks.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    project = Path(__file__).resolve().parents[2]
    environment = project / ".venv"
    # Keep this path intact: resolving bin/python symlinks can escape a Unix venv.
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not (environment / "pyvenv.cfg").is_file() or not python.is_file():
        print(
            "pip-audit requires the existing project .venv and its Python interpreter; nothing was installed.",
            file=sys.stderr,
        )
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        # -I ignores PYTHONPATH/PYTHONHOME and user-site packages. The venv's own
        # site-packages, including its pip-audit installation, remain available.
        result = subprocess.run([str(python), "-I", "-m", "pip_audit", *args], cwd=project, check=False)
    except OSError as exc:
        print(f"Could not execute project .venv audit interpreter ({type(exc).__name__}).", file=sys.stderr)
        return 2
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
