"""CVsAgent CLI entrypoint.

Thin wrapper around :mod:`cvs_agent.app` so this file stays small and users
can still run ``python main.py`` as advertised in the docs.
"""
from __future__ import annotations

import sys

from cvs_agent.app import main


if __name__ == "__main__":
    sys.exit(main())
