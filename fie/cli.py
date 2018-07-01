#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

"""
This file is inherit from mininet/cli.py
"""

from mininet.cli import CLI
from fie import FIE
import sys
from cmd import Cmd
from subprocess import call


class FCLI(CLI):
    def __init__(self, FIE, stdin=sys.stdin, script=None):
        CLI.__init__(self, FIE, stdin, script)
        Cmd.__init__(self)

    def do_docker(self, line):
        """
        Docker command line interface.
        Detailed actions and options => 
        $ docker 
        """
        self.do_sh("docker" + " " + line)

    def do_top(self, _line):
        """Top for perf monitoring"""
        self.do_sh("top")

    def do_clear(self, _line):
        """Clear the terminal"""
        self.do_sh("clear")
