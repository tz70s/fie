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
        self._fie = FIE
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

    def do_migrate(self, _line):
        """
        Migrate container to dst node.
        migrate <container> <dst_node>
        """
        try:
            args = _line.split(' ')
            container = args[0]
            dst_node = args[1]
            for node in self._fie.absnode_map:
                for c in self._fie.absnode_map[node].container_list:
                    if c.name == container:
                        self._fie.absnode_map[node].container_list.remove(c)
                        c.destroy()
                        # do migration
                        self._fie.node(dst_node).dry_run(c)
        except Exception as e:
            print(e)
            print("invalid arguments, expect migrate <container> <dst_node>")
