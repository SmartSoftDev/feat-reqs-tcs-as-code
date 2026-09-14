from typing import List, Dict
from dataclasses import dataclass
from frtaclib.parse_md_item import MdFile, ItemMdFileContent


@dataclass
class ItemCfg:
    name: str = None
    plural: str = None
    type: str = None
    uid: str = None
    parents: List[str] = None
    stored_externally: bool = None  # default False
    desc_doc: MdFile = None
    files: List[ItemMdFileContent] = None
    ids: Dict[str, ItemMdFileContent] = None
    links: List[LinkCfg] = None

    def __repr__(self):
        return f""

    @classmethod
    def from_cfg(cls: ItemCfg, item: dict):
        return cls(
            name=item.get("name"),
            plural=item.get("plural"),
            type=item.get("type", "item"),
            uid=item.get("uid"),
            parents=item.get("parents", []),
            stored_externally=item.get("stored_externally", False),
            # populated
            files=[],
            ids={},
            links=[],
        )


@dataclass
class LinkCfg:
    uid: str = None
    to_uids: List[str] = None
    to_rel_name: str = None
    to_validation: str = None
    from_uids: List[str] = None
    from_rel_name: str = None
    from_validation: str = None
    relation: str = None

    @classmethod
    def from_cfg(cls, d: dict):
        d_to = d.get("to", {})
        d_from = d.get("from", {})
        return cls(
            uid=d.get("uid"),
            to_uids=d_to.get("uids"),
            to_rel_name=d_to.get("relation-name"),
            to_validation=d_to.get("validation"),
            from_uids=d_from.get("uids"),
            from_rel_name=d_from.get("relation-name"),
            from_validation=d_from.get("validation"),
            relation=d.get("relation", "1-to-n"),
        )
