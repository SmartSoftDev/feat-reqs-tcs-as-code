import yaml
import marko
from pathlib import Path
from marko.block import Heading, Document, FencedCode
from frtaclib.errors_mng import FindingWarning, FindingError


def remove_one_chapter(ast, start_ndx):
    ast.children.pop(start_ndx)
    while len(ast.children) > (start_ndx + 1):
        e = ast.children[start_ndx]
        if isinstance(e, Heading):
            break
        else:
            ast.children.pop(start_ndx)


def skip_until_first_heading(ast):
    found = None
    for ndx, e in enumerate(ast.children, 1):
        if isinstance(e, Heading):
            found = ndx
            if e.level != 1:
                e.level = 1
            break
    if found:
        ast.children = ast.children[found - 1 :]
    else:
        ast.children = []


class MdFile:

    def __init__(self, fpath_rel: Path):
        self.fpath_rel = fpath_rel
        self.ast: Document = None
        self.meta: dict = {}
        self.title: str = None

    def parse_file(self):
        errs = []
        c = self.fpath_rel.read_text()

        parser = marko.Markdown()
        self.ast = parser.parse(c)
        errs += self.populate_and_validate()

        return errs

    def populate_and_validate(self):
        errs = []
        if not isinstance(self.ast.children[0], Heading):
            errs.append(FindingWarning("md_no_h", "Markdown Item must start always with H1.", self.fpath_rel))
            skip_until_first_heading(self.ast)

        if not isinstance(self.ast.children, list) or len(self.ast.children) < 1:
            errs.append(FindingWarning("md_empty", "Markdown Item appears empty! skipping this item", self.fpath_rel))
            return errs
        lvl1_heading = 0
        for e in self.ast.children:
            if isinstance(e, Heading):
                e: Heading
                if e.level == 1:
                    lvl1_heading += 1
                    if lvl1_heading > 1:
                        e.level = 2
        if lvl1_heading > 1:
            errs.append(FindingWarning("md_multi_h1", "Markdown has multiple H1 level in one file", self.fpath_rel))

        # extract meta
        for ndx, e in enumerate(self.ast.children):
            if isinstance(e, Heading):
                e: Heading
                if e.children[0].children == "metadata":
                    found: FencedCode = None
                    for c in self.ast.children[ndx + 1 :]:
                        if isinstance(c, FencedCode):
                            found = c
                            break
                        if isinstance(c, Heading):
                            break
                    if not found:
                        errs.append(
                            FindingWarning(
                                "md_no_fencecode",
                                "Markdown ## metadata does not have fenced code ```...```",
                                self.fpath_rel,
                            )
                        )
                    if found:
                        meta: FencedCode = found
                        try:
                            self.meta = yaml.safe_load(meta.children[0].children)
                        except yaml.YAMLError as exc:
                            errs.append(
                                FindingError(
                                    "malf_item_meta_yml",
                                    f"Item metadata text if malformed (yml error) {exc}",
                                    file=self.fpath_rel,
                                )
                            )
                    # FIXME: decide if: remove_one_chapter(self.ast, ndx)

        h1: Heading = self.ast.children[0]
        self.title = h1.children[0].children

        return errs


class ItemMdFileContent(MdFile):
    def __init__(self, fpath_rel: Path):
        super().__init__(fpath_rel)

        # populated data
        self.valid = False
        self.item_uid = None
        self.id: str = None

    def populate_and_validate(self):
        errs = []
        errs += super().populate_and_validate()

        # extract the ID
        self.id = self.meta.get("id", "${FROM_FILE_NAME}")
        if self.id == "${FROM_FILE_NAME}":
            fname = self.fpath_rel.name
            if fname.startswith("_"):
                fname = fname.lstrip("_")
            f_cmps = fname.split("_", 1)
            if len(f_cmps) != 2:
                errs.append(
                    FindingError(
                        "fname_id_fail", "Could not parse the ID and Item UID from file name", file=self.fpath_rel
                    )
                )
                self.id = fname
                self.item_uid = ""
            else:
                f_id = f_cmps[0]
                f_id_uid_cmps = f_id.split("-", 1)
                if len(f_id_uid_cmps) != 2:
                    errs.append(
                        FindingError("fname_uid_fail", f"Could not parse the Item UID from {f_id}", file=self.fpath_rel)
                    )
                    self.id = f_id
                    self.item_uid = ""
                else:
                    self.id = f_id_uid_cmps[1]
                    self.item_uid = f_id_uid_cmps[0]
        else:
            f_id_uid_cmps = self.id.split("-", 1)
            if len(f_id_uid_cmps) != 2:
                errs.append(
                    FindingError("meta_uid_fail", f"Could not parse the Item UID from {f_id}", file=self.fpath_rel)
                )
                self.id = f_id
                self.item_uid = ""
            else:
                self.id = f_id_uid_cmps[1]
                self.item_uid = f_id_uid_cmps[0]

        return errs


def promote_headings(element, depth_increment=1):
    """Recursively traverses the AST and shifts heading levels down."""
    if isinstance(element, Heading):
        # Shift heading levels (e.g., level 1 -> level 2)
        element.level = min(element.level + depth_increment, 6)

    # Recurse into child elements if they exist
    if hasattr(element, "children") and isinstance(element.children, list):
        for child in element.children:
            promote_headings(child, depth_increment)
