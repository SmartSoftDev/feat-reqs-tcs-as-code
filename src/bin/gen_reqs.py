#!/usr/bin/env python3
"""
gen_reqs.py — Requirements document generator.

Discovers *ac.md files, groups them by prefix, sorts numerically,
and emits a single Markdown or AsciiDoc requirements document.
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
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
        help="If set, additionally generate an HTML file.",
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
# Git info
# ---------------------------------------------------------------------------

def get_git_info(repo_path: Path) -> dict | None:
    """
    Return git info if `repo_path` lives inside a git working tree.

    Keys collected:
        commit       - full HEAD commit hash
        commit-date  - ISO 8601 committer date of HEAD
        describe     - `git describe --always --tags --dirty` output

    Returns None if git isn't installed, `repo_path` isn't in a repo, or
    the git call times out.
    """
    def _run(args: list[str]) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), *args],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    if _run(["rev-parse", "--is-inside-work-tree"]) != "true":
        return None

    info: dict = {}
    commit = _run(["rev-parse", "HEAD"])
    if commit:
        info["commit"] = commit
    commit_date = _run(["log", "-1", "--format=%cI"])
    if commit_date:
        info["commit-date"] = commit_date
    describe = _run(["describe", "--always", "--tags", "--dirty"])
    if describe:
        info["describe"] = describe
    return info or None


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


def parse_ac_file(
    filepath: Path,
    config_root: Path,
    warnings: list[str],
) -> dict | None:
    """
    Parse an *ac.md file and return a dict with keys:
        id, prefix, number, title, description, notes, filepath, rel_path, meta
    Returns None if the file cannot be parsed; appends a reason to `warnings`.
    """
    text = filepath.read_text(encoding="utf-8")
    rel = _rel_path(filepath, config_root)

    # --- metadata block ---
    m = METADATA_FENCE_RE.search(text)
    if not m:
        warnings.append(f"No metadata block in {rel}, skipped.")
        return None

    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        warnings.append(f"YAML error in {rel}: {exc}, skipped.")
        return None

    req_id: str = str(meta.get("id", "")).strip()
    if not req_id:
        warnings.append(f"No 'id' in metadata of {rel}, skipped.")
        return None

    # Split "UR-1" -> prefix="UR", number=1
    id_match = re.match(r"^([A-Za-z]+)-(\d+)$", req_id)
    if not id_match:
        warnings.append(
            f"id '{req_id}' in {rel} doesn't match PREFIX-NUMBER pattern, skipped."
        )
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
        "rel_path": rel,
        "meta": meta,
    }


def discover_files(
    root_dir_from_config: str,
    config_root: Path,
    warnings: list[str],
) -> list[dict]:
    """Search for *ac.md files under root-dir as specified in the config."""
    search_path = Path(root_dir_from_config).expanduser().resolve()

    if not search_path.exists():
        sys.exit(f"ERROR: search directory does not exist: {search_path}")

    results = []
    for fp in sorted(search_path.rglob("*ac.md")):
        parsed = parse_ac_file(fp, config_root, warnings)
        if parsed:
            results.append(parsed)
    return results


def detect_duplicate_ids(reqs: list[dict], warnings: list[str]) -> None:
    """Append a warning for each id found in more than one file."""
    by_id: dict[str, list[str]] = defaultdict(list)
    for r in reqs:
        by_id[r["id"]].append(r["rel_path"])
    for req_id, paths in by_id.items():
        if len(paths) > 1:
            files_str = ", ".join(paths)
            warnings.append(f"Duplicated ID {req_id} found in files: {files_str}")


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _format_yaml_block(data: dict) -> str:
    """Dump a dict as a ```yml fenced block, preserving insertion order."""
    yaml_str = yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    ).rstrip()
    return f"```yml\n{yaml_str}\n```"


def format_generated_file_section(
    project_config_path: Path,
    warnings: list[str],
) -> str:
    """Top-level `# Generated-file` section with generation metadata."""
    generated: dict = {
        "generated-at": datetime.now().isoformat(timespec="seconds"),
    }
    git_info = get_git_info(project_config_path.resolve().parent)
    if git_info:
        generated["git"] = git_info
    # Always emit the key so downstream tooling can rely on it.
    generated["warnings"] = list(warnings)

    return _format_yaml_block(generated) + "\n"


def _requirement_metadata_block(req: dict) -> str:
    """Return the `### Metadata` subchapter for a single requirement.

    Excludes `id` and `title` (already shown in the H2 chapter header)
    and adds the `path:` key with the relative path of the source file.
    """
    meta = dict(req["meta"])
    meta.pop("id", None)
    meta.pop("title", None)
    meta["path"] = req["rel_path"]

    return "### Metadata\n\n" + _format_yaml_block(meta)


def generate_markdown(
    grouped: dict[str, list[dict]],
    uid_map: dict[str, dict],
    ordered_prefixes: list[str],
) -> str:
    """
    Output structure per requirement:
        ## <ID> <Title>        <- H2
        <description>
        ### Notes              <- H3, only when source has a Notes section
        <notes>
        ### Metadata           <- H3, always emitted; yml block
        ```yml ... ```
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
            req_lines.append(_requirement_metadata_block(req))
            req_lines.append("")

        sections.append("\n".join(req_lines))

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# AsciiDoc conversion
# ---------------------------------------------------------------------------

def markdown_to_adoc(md_text: str) -> str:
    """Convert Markdown to AsciiDoc via pypandoc (wraps pandoc)."""
    try:
        import pypandoc  # type: ignore
    except ImportError:
        sys.exit(
            "ERROR: pypandoc is required for --output adoc.\n"
            "Install it with: pip install pypandoc"
        )
    try:
        return pypandoc.convert_text(md_text, "asciidoc", format="md")
    except OSError:
        sys.exit(
            "ERROR: pandoc binary not found.\n"
            "Install it from https://pandoc.org/installing.html or via your package manager:\n"
            "  brew install pandoc       # macOS\n"
            "  apt install pandoc        # Debian/Ubuntu"
        )


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
    config_path = Path(args.project_config)
    config_root = config_path.resolve().parent
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

    # --- discovery, parsing, and duplicate detection all feed `warnings` ---
    warnings: list[str] = []

    all_reqs = discover_files(root_dir, config_root, warnings)
    detect_duplicate_ids(all_reqs, warnings)

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

    # --- also mirror warnings to stderr ---
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    # --- generate output ---
    generated_section = format_generated_file_section(config_path, warnings)
    reqs_md = generate_markdown(grouped, uid_map, ordered_prefixes)
    md_content = generated_section + "\n" + reqs_md

    if args.output == "md":
        out = Path("requirements.md")
        out.write_text(md_content, encoding="utf-8")
        print(f"Written: {out}")

    elif args.output == "adoc":
        adoc_content = markdown_to_adoc(md_content)
        out = Path("requirements.adoc")
        out.write_text(adoc_content, encoding="utf-8")
        print(f"Written: {out}")

    if args.html:
        html_content = markdown_to_html(md_content, title="Requirements")
        out_html = Path("requirements.html")
        out_html.write_text(html_content, encoding="utf-8")
        print(f"Written: {out_html}")


if __name__ == "__main__":
    main()