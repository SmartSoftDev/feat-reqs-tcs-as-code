"""
    Copyright (C) Smartsoftdev.eu SRL - All Rights Reserved
    Proprietary and confidential license.
    Unauthorized copying via any medium or use of this file IS STRICTLY prohibited
    For any license violations or more about commercial licensing please contact:
    SmartSoftDev.eu

Simple error management
"""

from typing import List
from dataclasses import dataclass
from pathlib import Path


class Finding:
    LEVEL_ERROR = "err"
    LEVEL_WARNING = "wrn"

    def __init__(self, level: str, msg_uid: str, msg: str, file: str, location: str):
        self.level = level
        self.msg_uid = msg_uid
        self.msg = msg
        self.file = file
        self.location = location


class FindingError(Finding):
    def __init__(self, msg_uid, msg, file="", location=""):
        super().__init__(self.LEVEL_ERROR, msg_uid, msg, file, location)


class FindingWarning(Finding):
    def __init__(self, msg_uid, msg, file="", location=""):
        super().__init__(self.LEVEL_WARNING, msg_uid, msg, file, location)


@dataclass
class FrtacFinding:
    level: str = "err"  # or wrn
    msg: str = ""
    msg_uid: str = ""  # id of the message
    file: Path = None
    location: str = ""


class FrtacErrMng:
    def __init__(self):
        self.findings = []
        self.error_findings = 0
        self.warning_findings = 0

    def has_findings(self):
        return len(self.findings) > 0

    def add_finding(self, finding: Finding):
        if finding.level == Finding.LEVEL_ERROR:
            self.error_findings += 1
        else:
            self.warning_findings += 1
        self.findings.append(finding)

    def add_finding_list(self, findings_list: "List[Finding]"):
        if not findings_list:
            return
        for f in findings_list:
            self.add_finding(f)

    def print_findings(self):
        if not self.has_findings():
            return
        print(f"Found: {self.error_findings} ERRORS and {self.warning_findings} WARNINGS")
        for ndx, f in enumerate(self.findings, 1):
            f: FrtacFinding
            txt = f"{ndx:02d}.  ({f.level}:{f.msg_uid}) {f.msg}"
            if f.file:
                txt += f" '{f.file}"
                if f.location:
                    txt += f":{f.location}"
                txt += "'"
            print(txt)
