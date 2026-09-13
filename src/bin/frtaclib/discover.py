import re
from pathlib import Path

# ---------------------------------------------------------------------------
# File discovery & parsing
# ---------------------------------------------------------------------------

# Matches the full metadata section: "# metadata" heading + fenced yml block.
# Group 1 captures the raw YAML content inside the fences.
METADATA_FENCE_RE = re.compile(
    r"^#\s*metadata\s*\n```(?:ya?ml)?\n(.*?)```\n?",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)

FIRST_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _rel_path(filepath: Path, config_root: Path) -> str:
    """Posix-style path relative to config_root, or absolute fallback."""
    try:
        return filepath.resolve().relative_to(config_root).as_posix()
    except ValueError:
        return filepath.resolve().as_posix()
