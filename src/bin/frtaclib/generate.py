import marko
from marko.md_renderer import MarkdownRenderer
from marko.block import Document, Heading, BlankLine
from marko.inline import RawText
from pathlib import Path
from frtaclib.parse_md_item import ItemMdFileContent
import copy


class MdDocumentsGenerator:
    def __init__(self):
        self.cfg: dict = {}
        self.items: dict = {}
        self.prj_root: Path

    def _cmd_generate(self):
        d_cfg = self.cfg.get("docs_settings", {})
        dst = self.prj_root.joinpath(d_cfg.get("out_dir", "output"))
        dst.mkdir(parents=True, exist_ok=True)
        for d in self.cfg.get("documents", []):
            mdoc = Document()
            mdoc.children = []
            mh = Heading.__new__(Heading)
            mh.level = 1
            mh.children = [RawText(f"{d.get('name')}")]
            blank_line = BlankLine.__new__(BlankLine)
            mdoc.children.append(mh)
            for c in d.get("compose", []):
                if c.get("component") == "list-of-items":
                    d_items = c.get("items", [])
                    for i_uid in d_items:
                        if i_uid not in self.items:
                            raise Exception(f"{i_uid=} not found")
                        for f in self.items[i_uid].files:
                            f: ItemMdFileContent
                            new_ast = copy.deepcopy(f.ast)
                            title: Heading = new_ast.children[0]
                            title.children[0].children = f"{f.item_uid}-{f.id}: " + title.children[0].children
                            for child in new_ast.children:
                                if isinstance(child, Heading):
                                    child: Heading
                                    child.level += 1
                            mdoc.children.append(blank_line)
                            mdoc.children += new_ast.children

            dst_fname = d.get("name", "no-name-doc")
            dpath_md = dst.joinpath(dst_fname + ".md")
            dpath_html = dst.joinpath(dst_fname + ".html")

            markdown = MarkdownRenderer()
            html = marko.Markdown()
            dpath_md.write_text(markdown.render(mdoc))
            dpath_html.write_text(html.render(mdoc))
