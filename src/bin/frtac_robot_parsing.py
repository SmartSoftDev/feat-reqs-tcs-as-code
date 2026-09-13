#!/usr/bin/env python3
"""
    Copyright (C) Smartsoftdev.eu SRL - All Rights Reserved
    Proprietary and confidential license.
    Unauthorized copying via any medium or use of this file IS STRICTLY prohibited
    For any license violations or more about commercial licensing please contact:
    SmartSoftDev.eu

CLI for managing Features, Reqs, TC's
"""

import os
import argparse
from tc_parser_robot.parse_robot import parse_robot_file
from robot.api import TestSuiteBuilder
from robot.model.testcase import TestCase
from robot.model.body import Body
from robot.running import Keyword, TestCase, TestSuite


class App:
    def __init__(self):
        self.args = None

    def parse_args(self):
        parser = sp = argparse.ArgumentParser(description="RPI nano communication tool")
        sp.add_argument(
            "-v", "--verbose", action="count", default=0, help="add verbosity, max -vvv"
        )

        subparsers = sp.add_subparsers(title="Sub commands")

        sp = subparsers.add_parser("robot", help="")
        sp.set_defaults(cmd="robot")

        sp = subparsers.add_parser(
            "watch", help="Watch directory and generate all docs"
        )
        sp.set_defaults(cmd="watch")

        sp = subparsers.add_parser("set_configuration", help="Print Config information")
        sp.set_defaults(cmd="set_configuration")
        sp.add_argument(
            "--toggle_reverse",
            action="store_true",
            help="Toggle the relay reverse polarity",
        )
        sp.add_argument(
            "--toggle_disable_wifi", action="store_true", help="TODO: Toggle the wifi"
        )
        sp.add_argument(
            "--toggle_disable_bluetooth",
            action="store_true",
            help="TODO: Toggle the bluetooth",
        )

        sp = subparsers.add_parser(
            "set_name", help="Add new or update existing GPIO to config"
        )
        sp.set_defaults(cmd="set_name")
        sp.add_argument("name", help="gpio name")
        sp.add_argument("gpio", type=int, help="gpio number")
        sp.add_argument("--description", help="Relay description", default=None)
        sp.add_argument(
            "--on",
            action="store_true",
            help="set the gpio state to ON, otherwise is OFF",
        )

        sp = subparsers.add_parser("del_name", help="Delete GPIO from config")
        sp.set_defaults(cmd="del_name")
        sp.add_argument("gpio", type=int, help="gpio number")

        sp = subparsers.add_parser(
            "set_gpio", help="Set GPIO state (default set to off)"
        )
        sp.add_argument("--name", help="gpio name")
        sp.add_argument("--gpio", type=int, help="gpio pin")
        sp.add_argument(
            "--on",
            action="store_true",
            help="set the gpio state to ON, otherwise is OFF",
        )
        sp.add_argument("--toggle", action="store_true", help="toggle the gpio state")
        sp.set_defaults(cmd="set_gpio")
        sp = subparsers.add_parser("dev_list", help="List available devices")
        sp.set_defaults(cmd="dev_list")

        args = parser.parse_args()
        if not hasattr(args, "cmd"):
            parser.print_usage()
            return
        self.args = args

    def __cmd_watch(self):
        pass

    def __cmd_robot(self):
        parse_robot_file()

    def start(self):
        self.parse_args()
        method_name = f"_cmd_{self.args.cmd}"
        try:
            method = self.__getattribute__(method_name)
        except AttributeError:
            self.log.error("Unknown CMD=%r", self.args.cmd)
            self.is_running.set()
            return
        try:
            # call the message handler
            method()
        except Exception:
            self.log.exception(
                "Unhandled exception while handling cmd=%r", self.args.cmd
            )


if __name__ == "__main__":
    a = App()
    a.start()
