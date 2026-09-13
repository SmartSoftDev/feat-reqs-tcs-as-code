"""
    Copyright (C) Smartsoftdev.eu SRL - All Rights Reserved
    Proprietary and confidential license.
    Unauthorized copying via any medium or use of this file IS STRICTLY prohibited
    For any license violations or more about commercial licensing please contact:
    SmartSoftDev.eu

validates project config
"""

from typing import List
from frtaclib.errors_mng import FrtacErrMng, FindingWarning, FindingError, Finding


class Allowed:
    ITEM_TYPES = ["item", "group", "requirement", "test-suite", "test-case", "feature", "release"]  # default = item
    PARENTS_VALIDATION = ["minimum-one", "minimum-one-each-type", "optional"]


def validate_prj_config(app) -> "List[Finding]":
    ret = []
    items = app.items.values()
    uids = list(app.items.keys())
    cfg_path = str(app.cfg_path)
    for i in items:
        if not i.get("name"):
            ret.append(FindingError("missing_name", f"Item {i.get('uid')} must have 'name'", cfg_path))
        if i["uid"] != i["uid"].upper():
            ret.append(FindingError("item_uid_upper", f"Item {i.get('uid')} must be UPPER case", cfg_path))
        for p in i.get("parents", []):
            if p not in uids:
                ret.append(FindingError("unk_parent", f"Item {i.get('uid')} parent {p!r} is unknown", cfg_path))
        if i.get("type", Allowed.ITEM_TYPES[0]) not in Allowed.ITEM_TYPES:
            ret.append(
                FindingError("unk_item_type", f"Item {i.get('uid')} type {i.get('type')!r} is unknown", cfg_path)
            )
    return ret
