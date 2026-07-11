#!/usr/bin/env python3
"""CLI entry point for the Phase 1 StoryGraph discovery tool."""

import sys
from pathlib import Path

# Allow the documented ``python scripts/...`` invocation from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storygraph.discovery import main


if __name__ == "__main__":
    main()
