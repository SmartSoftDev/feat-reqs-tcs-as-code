#!/usr/bin/env python3
"""
gen_reqs.py — Requirements document generator.

Discovers *ac.md files, groups them by prefix, sorts numerically,
and emits a single Markdown or AsciiDoc requirements document.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a requirements document from *ac.md files.",
    )
    p.add_argument(
        "--output",
        choices=["md", "adoc"],
        default="md",
        help="Output format: md (default) or adoc.",
    )
    p.add_argument(
        "--project-config",
        default="./config.frtac.yml",
        metavar="FILE",
        help="Path to the frtac config YAML (default: ./config.frtac.yml). "
             "Example: examples/Project1/config.frtac.yml. "
             "The root-dir key in this file determines where *ac.md files are searched.",
    )
    p.add_argument(
        "--only-include-prefix",
        default=None,
        metavar="BR-UR-PR-SR-HR-RR",
        help="Dash-separated list of UIDs to include, e.g. BR-UR-PR. "
             "If omitted, all prefixes from the config are included.",
    )
    p.add_argument(
        "--html",
        action="store_true",
        help="If set, additionally generate an HTML file. Only applies with --output md.",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        sys.exit(f"ERROR: project config not found: {config_path}")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_uid_map(config: dict) -> dict[str, dict]:
    """Return {uid: item_entry} preserving config order."""
    return {item["uid"]: item for item in config.get("items-grouping", [])}


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


def parse_ac_file(filepath: Path) -> dict | None:
    """
    Parse an *ac.md file and return a dict with keys:
        id, prefix, number, title, description, notes, filepath, meta
    Returns None if the file cannot be parsed.
    """
    text = filepath.read_text(encoding="utf-8")

    # --- metadata block ---
    m = METADATA_FENCE_RE.search(text)
    if not m:
        print(f"WARNING: no metadata block in {filepath}, skipping.", file=sys.stderr)
        return None

    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        print(f"WARNING: YAML error in {filepath}: {exc}, skipping.", file=sys.stderr)
        return None

    req_id: str = str(meta.get("id", "")).strip()
    if not req_id:
        print(f"WARNING: no 'id' in metadata of {filepath}, skipping.", file=sys.stderr)
        return None

    # Split "UR-1" -> prefix="UR", number=1
    id_match = re.match(r"^([A-Za-z]+)-(\d+)$", req_id)
    if not id_match:
        print(f"WARNING: id '{req_id}' doesn't match PREFIX-NUMBER pattern in {filepath}, skipping.", file=sys.stderr)
        return None

    prefix = id_match.group(1).upper()
    number = int(id_match.group(2))

    # --- strip metadata section from body ---
    body_text = METADATA_FENCE_RE.sub("", text).strip()

    # --- first remaining H1 becomes the title ---
    h1_match = FIRST_H1_RE.search(body_text)
    title = h1_match.group(1).strip() if h1_match else req_id

    # Remove the title line from the body so we don't duplicate it
    if h1_match:
        body_text = body_text[h1_match.end():].strip()

    # Split body into description (before any Notes heading) and notes (after)
    notes_match = re.search(r"^#{1,6}\s*Notes\s*$", body_text, re.IGNORECASE | re.MULTILINE)
    if notes_match:
        description = body_text[:notes_match.start()].strip()
        notes = body_text[notes_match.end():].strip()
    else:
        description = body_text
        notes = None

    return {
        "id": req_id,
        "prefix": prefix,
        "number": number,
        "title": title,
        "description": description,
        "notes": notes,
        "filepath": filepath,
        "meta": meta,
    }


def discover_files(root_dir_from_config: str) -> list[dict]:
    """
    Search for *ac.md files under root-dir as specified in the config.
    """
    search_path = Path(root_dir_from_config).expanduser().resolve()

    if not search_path.exists():
        sys.exit(f"ERROR: search directory does not exist: {search_path}")

    results = []
    for fp in sorted(search_path.rglob("*ac.md")):
        parsed = parse_ac_file(fp)
        if parsed:
            results.append(parsed)
    return results


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_markdown(
    grouped: dict[str, list[dict]],
    uid_map: dict[str, dict],
    ordered_prefixes: list[str],
) -> str:
    """
    Output structure:
        # <Plural group name>          <- H1 per prefix
        ## <ID> <Title>                <- H2 per requirement
        <description>
        ### Notes                      <- H3, only when source has a Notes section
        <notes>
    """
    sections: list[str] = []

    for prefix in ordered_prefixes:
        items = grouped.get(prefix, [])
        if not items:
            continue

        entry = uid_map[prefix]
        chapter_title = entry.get("plural") or entry.get("name") or prefix

        req_lines: list[str] = [f"# {chapter_title}", ""]

        for req in items:
            req_lines.append(f"## {req['id']} {req['title']}")
            req_lines.append("")
            if req["description"]:
                req_lines.append(req["description"])
                req_lines.append("")
            if req["notes"] is not None:
                req_lines.append("### Notes")
                req_lines.append("")
                req_lines.append(req["notes"])
                req_lines.append("")

        sections.append("\n".join(req_lines))

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def markdown_to_html(md_text: str, title: str = "Requirements") -> str:
    try:
        import markdown  # type: ignore
        body = markdown.markdown(md_text, extensions=["fenced_code", "tables"])
    except ImportError:
        print(
            "WARNING: 'markdown' package not installed; "
            "falling back to basic HTML wrapping. "
            "Install with: pip install markdown",
            file=sys.stderr,
        )
        escaped = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body = f"<pre>{escaped}</pre>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
    h1 {{ border-bottom: 2px solid #333; padding-bottom: .4rem; }}
    h2 {{ border-bottom: 1px solid #999; padding-bottom: .2rem; margin-top: 2rem; }}
    h3 {{ color: #2c5282; margin-top: 1.5rem; }}
    code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
    pre  {{ background: #f4f4f4; padding: 1rem; border-radius: 4px; overflow-x: auto; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # --- load config ---
    config = load_config(args.project_config)
    uid_map = build_uid_map(config)
    root_dir = config.get("root-dir", ".")

    # --- determine which prefixes to include, in config order ---
    if args.only_include_prefix:
        requested = [p.strip().upper() for p in args.only_include_prefix.split("-") if p.strip()]
        ordered_prefixes = [uid for uid in uid_map if uid in requested]
        for p in requested:
            if p not in uid_map:
                print(f"WARNING: prefix '{p}' not found in config, ignoring.", file=sys.stderr)
    else:
        ordered_prefixes = list(uid_map.keys())

    # --- discover & parse files ---
    all_reqs = discover_files(root_dir)

    # --- filter by included prefixes ---
    included_set = set(ordered_prefixes)
    filtered = [r for r in all_reqs if r["prefix"] in included_set]

    # --- group by prefix ---
    grouped: dict[str, list[dict]] = {p: [] for p in ordered_prefixes}
    for req in filtered:
        grouped[req["prefix"]].append(req)

    # --- sort each group numerically ---
    for prefix in ordered_prefixes:
        grouped[prefix].sort(key=lambda r: r["number"])

    # --- generate output ---
    md_content = generate_markdown(grouped, uid_map, ordered_prefixes)

    if args.output == "md":
        out = Path("requirements.md")
        out.write_text(md_content, encoding="utf-8")
        print(f"Written: {out}")

    if args.html:
        html_content = markdown_to_html(md_content, title="Requirements")
        out_html = Path("requirements.html")
        out_html.write_text(html_content, encoding="utf-8")
        print(f"Written: {out_html}")

if __name__ == "__main__":
    main()