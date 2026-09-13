"""
    Copyright (C) Smartsoftdev.eu SRL - All Rights Reserved
    Proprietary and confidential license.
    Unauthorized copying via any medium or use of this file IS STRICTLY prohibited
    For any license violations or more about commercial licensing please contact:
    SmartSoftDev.eu

Simple CLI application that uses asyncIO
"""

from frtaclib.errors_mng import FrtacErrMng


class SimpleCliApp:
    def __init__(self):
        self.args = None

    def start_cmd(self):
        method_name = f"_cmd_{self.args.cmd}"
        try:
            method = self.__getattribute__(method_name)
        except AttributeError as exc:
            raise Exception(f"Unknown cmd={self.args.cmd!r}") from exc
            # call the message handler
        try:
            method()
        finally:
            FrtacErrMng.print_findings(self)  # from error_mng class
