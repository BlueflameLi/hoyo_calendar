"""Backward compatible shim for the legacy CLI entrypoint."""

from __future__ import annotations

from typing import Sequence

from main import main as _main


def main(argv: Sequence[str] | None = None) -> None:  # noqa: D401
    """Proxy to :func:`main.main` for existing workflows."""

    _main(argv)


if __name__ == "__main__":
    main()
