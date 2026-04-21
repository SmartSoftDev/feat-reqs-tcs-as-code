# gen_reqs.py

Discovers `*ac.md` requirement files in a directory tree, groups them by
prefix, sorts them numerically, and emits a single consolidated requirements
document.

## Requirements

Install Python dependencies:

```bash
pip install -r requirements.txt
```

For AsciiDoc output, `pandoc` must also be installed on your system:

```bash
brew install pandoc      # macOS
apt install pandoc       # Debian/Ubuntu
```

## Usage

```bash
python gen_reqs.py [OPTIONS]
```

## Options

| Option | Default | Description |
|---|---|---|
| `--project-config FILE` | `./config.frtac.yml` | Path to the frtac config YAML. Defines the known prefixes and their display names. The `root-dir` key in this file determines where `*ac.md` files are searched. |
| `--output FORMAT` | `md` | Output format: `md` or `adoc`. |
| `--html` | *(off)* | Also generate an HTML file from the Markdown. |
| `--only-include-prefix` | *(all)* | Dash-separated list of prefixes to include, e.g. `UR-PR-SR`. Chapters appear in the order they are defined in the config. |

## Examples

Generate Markdown for all prefixes found in the config:

```bash
python gen_reqs.py --project-config path/to/config.frtac.yml
```

Generate Markdown for user and software requirements only:

```bash
python gen_reqs.py \
  --project-config path/to/config.frtac.yml \
  --only-include-prefix UR-SR
```

Generate AsciiDoc:

```bash
python gen_reqs.py \
  --project-config path/to/config.frtac.yml \
  --output adoc
```

Generate Markdown and also export to HTML:

```bash
python gen_reqs.py \
  --project-config path/to/config.frtac.yml \
  --html
```

## Source file format

Each requirement file must be named `*ac.md` and contain a `metadata` section
with at least an `id` field in the form `PREFIX-NUMBER`:

```markdown
# metadata

\```yml
id: UR-1
tags: [fe]
\```

# Title of the requirement

Description text goes here, directly below the title.

### Notes

Optional notes section — only included in the output if present in the source file.
```

The `id` determines which prefix chapter the requirement appears in and its
sort order within that chapter. The first `#` heading after the metadata block
becomes the title. Any text between the title and a `Notes` heading (if
present) is treated as the description.

The search root is the `root-dir` value from the config file, resolved relative
to the config file's own location.

## Output format

```
# <Prefix plural name>              (e.g. "User Requirements")

## <ID> <Title>                     (e.g. "UR-1 Allow UI composing configuration")

<Description text>

### Notes                           (only if the source file contains a Notes section)

<Notes text>
```

Prefix chapter order follows the order of `items-grouping` in the project
config, not the order of `--only-include-prefix`.