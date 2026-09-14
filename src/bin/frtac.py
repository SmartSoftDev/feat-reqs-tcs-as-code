#!/usr/bin/env python3
"""
Ftrac tool is used to manage and check FRTAC logic
"""

import os
import argparse
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml
from frtaclib.simple_cli_app import SimpleCliApp
from frtaclib.errors_mng import FrtacErrMng, FindingError, FindingWarning
from frtaclib.validate_prj import validate_prj_config
from frtaclib.parse_md_item import MdFile, ItemMdFileContent
from frtaclib.generate import MdDocumentsGenerator


class Frtac(SimpleCliApp, FrtacErrMng, MdDocumentsGenerator):

    def __init__(self):
        super(SimpleCliApp, self).__init__()
        super(FrtacErrMng, self).__init__()
        super(MdDocumentsGenerator, self).__init__()
        self.args = None
        self.cfg_path = None
        self.cfg = None
        self.prj_root = None
        self.items = None
        self.ordered_uids = None

    def parse_args(self) -> argparse.Namespace:
        p = sp = argparse.ArgumentParser(
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
            metavar="UR-PR-SR-TC-...",
            help="Dash-separated list of UIDs to include, e.g. BR-UR-PR. "
            "If omitted, all prefixes from the config are included.",
        )
        p.add_argument(
            "--html",
            action="store_true",
            help="If set, additionally generate an HTML file.",
        )
        subparsers = p.add_subparsers(title="Sub commands")

        sp = subparsers.add_parser("check", help="Execute all checks needed for FRTAC")
        sp.set_defaults(cmd="check")

        sp = subparsers.add_parser("stats", help="Show stats")
        sp.set_defaults(cmd="stats")
        sp = subparsers.add_parser("generate", help="Generate docs")
        sp.set_defaults(cmd="generate")

        self.args = p.parse_args()

    def load_prj_config(self) -> dict:
        self.cfg_path = Path(self.args.project_config)
        if not self.cfg_path.exists():
            raise Exception(f"ERROR: project config not found: {self.cfg_path}")
        with self.cfg_path.open() as fh:
            self.cfg = yaml.safe_load(fh)
        if self.cfg.get("frtac_project_config_version") != "v1.0.0":
            self.add_finding(
                FindingError(
                    "frtac_verion_missing", "Project config file does not seem to be for FRTac", str(self.cfg_path)
                )
            )
        self.prj_root = self.cfg.get("root-dir", ".")
        if self.prj_root == ".":
            self.prj_root = self.cfg_path.resolve().parent
        # preprocessing the cfg data
        self.items = {item["uid"]: item for item in self.cfg.get("items-grouping", [])}
        allowed_item_types = ["item", "requirement", "feature", "test-case", "test-suite", "release"]
        for k, i in self.items.items():
            i["files"] = []
            i_type = i.get("type", "item")
            if i_type not in allowed_item_types:
                raise Exception(f"Unknown item type {i_type=} {allowed_item_types=}")

        # --- determine which prefixes to include, in config order ---
        if self.args.only_include_prefix:
            requested = [p.strip().upper() for p in self.args.only_include_prefix.split("-") if p.strip()]
            self.ordered_uids = [uid for uid in self.items.keys() if uid in requested]
            for p in requested:
                if p not in self.items.keys():
                    raise Exception(f"Prefix '{p}' not found in PRJ config")
        else:
            self.ordered_uids = list(self.items.keys())

    def discover_files(self):
        for root, _, files in os.walk(self.prj_root):
            for filename in files:
                full_path = Path(os.path.join(root, filename))
                rel_path = full_path.relative_to(self.prj_root)
                str_path = str(rel_path)
                if not str_path.endswith(".ac.md"):
                    continue
                if rel_path.name.endswith(".desc.ac.md"):

                    i_uid = rel_path.name[:-11]
                    if i_uid not in self.items:
                        self.add_finding(
                            FindingError(
                                "unk_item_type", f"Description file for Unknown ITEM type {i_uid!r}", file=str(rel_path)
                            )
                        )
                        continue
                    desc_file = MdFile(full_path)
                    self.items[i_uid]["desc_doc"] = desc_file
                    continue

                item_file = ItemMdFileContent(full_path)
                self.add_finding_list(item_file.parse_file())

                if item_file.item_uid not in self.items:
                    self.add_finding(
                        FindingError("unk_item_type", f"Unknown ITEM type {item_file.item_uid!r}", file=str(rel_path))
                    )
                else:
                    i = self.items.get(item_file.item_uid)
                    i["files"].append(item_file)

        for i in self.items.values():
            i["files"] = sorted(i["files"], key=lambda x: x.id)
            if not i.get("desc_doc"):
                self.add_finding(FindingWarning("item_wo_desc", f"Item {i.get('uid')} has no description document"))

    def get_git_info(self, repo_path: Path) -> dict | None:
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

    def _cmd_check(self):
        pass

    def _cmd_stats(self):
        for i in self.items.values():
            txt = f"{i['uid']} ({len(i['files'])})"
            print(txt + "-" * (30 - len(txt)))
            for f in i.get("files"):
                f: ItemMdFileContent
                print(f"\t{f.item_uid}-{f.id}  {f.title}")

    def run(self):
        self.parse_args()
        self.load_prj_config()
        self.discover_files()
        self.add_finding_list(validate_prj_config(self))
        self.start_cmd()
        return

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
        sys.exit("ERROR: pypandoc is required for --output adoc.\n" "Install it with: pip install pypandoc")
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
    app = Frtac()
    app.run()


if __name__ == "__main__":
    main()
