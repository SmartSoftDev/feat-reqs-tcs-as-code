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
from robot.api import TestSuiteBuilder
from robot.model.testcase import TestCase
from robot.model.body import Body
from robot.running import Keyword, TestCase, TestSuite

def parse_robot_file():
    # Load the .robot file
    suite = TestSuiteBuilder().build("examples/robot_tcs/TS-1_my_first_TS.robot")

    # Access the suite name
    print(f"Suite Name: {suite.name}")

    # Iterate over test cases in the suite
    for test in suite.tests:
        test: TestCase
        print("--------------------------------")
        print(f"Test tags: {test.tags}")
        print(f"Test Name: {test.name}")
        print(f"Test Doc: {test.doc}")
        print(f"Test full_name: {test.full_name}")
        print(f"Test id: {test.id}")
        print(f"Test parent: {test.parent}")
        print(f"Test body: {test.body}")
        for el in test.body:
            if isinstance(el, Keyword):
                el: Keyword
                print(f"    {el}")
            else:
                print("NOT A keyword")
