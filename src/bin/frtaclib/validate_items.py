from typing import List
from pathlib import Path
from frtaclib.parse_md_item import ItemMdFileContent
from frtaclib.errors_mng import FindingWarning, FindingError, Finding
from frtaclib.data_model import LinkCfg


class ValidateItems:
    def __init__(self):
        self.cfg: dict = {}
        self.items: dict = {}
        self.links: dict = {}
        self.prj_root: Path

    def validate_and_populate_items(self) -> List[Finding]:
        errs = []
        # pupulate links for items
        for lcfg in self.cfg.get("links-to", []):
            l: LinkCfg = LinkCfg.from_cfg(lcfg)
            print(l)
            self.links[l.uid] = l
            for tol in l.from_uids:
                if tol not in self.items:
                    errs.append(FindingError("unk-link-uid", f"link Item {tol!r} not found", file=self.prj_root))
                i = self.items[tol]
                i.links.append(l)
        for i in self.items.values():
            # print(i)
            pass
        return errs
