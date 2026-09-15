from typing import List
from pathlib import Path
from frtaclib.parse_md_item import ItemMdFileContent
from frtaclib.errors_mng import FindingWarning, FindingError, Finding
from frtaclib.data_model import LinkCfg, ItemCfg


class ValidateItems:
    def __init__(self):
        self.cfg: dict = {}
        self.items: dict = {}
        self.links: dict = {}
        self.prj_root: Path
        self.cfg_path = None

    def validate_and_populate_items(self) -> List[Finding]:
        errs = []
        # populate links for items
        for l_cfg in self.cfg.get("links-to", []):
            l: LinkCfg = LinkCfg.from_cfg(l_cfg)
            if not l.to_allowed and l.to_validation:
                errs.append(
                    FindingError(
                        "no-sense-link-val-to",
                        f"link to:validation makes no sense since it is not allowed {l.uid!r}",
                        file=self.cfg_path,
                    )
                )
            if not l.from_allowed and l.from_validation:
                errs.append(
                    FindingError(
                        "no-sense-link-val-from",
                        f"link from:validation makes no sense since it is not allowed {l.uid!r}",
                        file=self.cfg_path,
                    )
                )

            self.links[l.uid] = l

            def __add_l_to_i(i_uid, l):
                if i_uid not in self.items:
                    errs.append(FindingError("unk-link-uid", f"link Item {i_uid!r} not found", file=self.cfg_path))
                i: ItemCfg = self.items[i_uid]
                if l.uid not in i.links:
                    i.links[l.uid] = l

            for i_uid in l.from_uids:
                __add_l_to_i(i_uid, l)
            for i_uid in l.to_uids:
                __add_l_to_i(i_uid, l)

        # check there are only configured links in the MD files
        for i in self.items.values():
            i: ItemCfg
            for f in i.files:
                f: ItemMdFileContent
                f_links: dict = f.meta.get("links-to", {})
                if not isinstance(f_links, dict):
                    errs.append(
                        FindingError("malformed-links-to", f"Links-to must be dict {f.full_id()}", file=f.fpath_rel)
                    )
                    continue
                for k in f_links.keys():
                    if k not in i.links:
                        errs.append(
                            FindingError(
                                "unk-link",
                                f"Unknown link {k!r} on {f.full_id()} (allowed: {list(i.links.keys())})",
                                file=f.fpath_rel,
                            )
                        )

        # let's process the links and validations
        for i in self.items.values():
            i: ItemCfg
            for l in i.links.values():
                l: LinkCfg

                def __verify_min_one(i, l):
                    for i_f in i.files:
                        i_f: ItemMdFileContent
                        if_links = i_f.meta.get("links-to", {})
                        if not isinstance(if_links, dict):
                            continue  # no need for errs because above it is checked
                        if_link_value = if_links.get(l.uid)
                        if not if_link_value or not len(if_link_value):
                            errs.append(
                                FindingError(
                                    "link-val-min-one",
                                    f"Link {l.uid!r} is configured as minimum-one, item={i_f.full_id()} does not have it",
                                    file=i_f.fpath_rel,
                                )
                            )
                            continue
                        # now check if configured link values are valid (exits, and respect relation)
                        for l_value in if_link_value:
                            print(l_value)

                if l.to_allowed and i.uid in l.to_uids:
                    if l.to_validation == "minimum-one":
                        __verify_min_one(i, l)
                if l.from_allowed and i.uid in l.from_uids:
                    if l.from_validation == "minimum-one":
                        __verify_min_one(i, l)

        return errs
