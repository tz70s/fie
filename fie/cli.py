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
from copy import copy


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
        except:
            print("invalid arguments, expect migrate <container> <dst_node>")

    def do_scale(self, _line):
        """
        Scale one container to dst node.
        scale <container> <container_new_name> <dst_node>
        """
        try:
            args = _line.split(' ')
            container = args[0]
            new_container_name = args[1]
            dst_node = args[2]
            for node in self._fie.absnode_map:
                for c in self._fie.absnode_map[node].container_list:
                    if c.name == container:
                        new_c = copy(c)
                        new_c.params = copy(c.params)
                        new_c.params['environment'] = {
                            'CLUSTER_SEED_IP': 'controller.docker', 'CLUSTER_HOST_IP': new_container_name + '.docker'}
                        new_c.name = new_container_name
                        self._fie.node(dst_node).dry_run(new_c)
        except Exception as e:
            print(
                "invalid arguments, expect scale <container> <container_new_name> <dst_node>")
            print(e)

    def do_routeall(self, _line):
        """
        Route all utility, by inserting static routes.
        """
        self._fie.routeAll()

    def do_ps(self, _line):
        """
        Show all containers locate in where.
        """
        try:
            for node in self._fie.absnode_map:
                sys.stdout.write(node + " - ")
                for c in self._fie.absnode_map[node].container_list:
                    sys.stdout.write(c.name + ' ')
                print('')
        except Exception as e:
            print("internal error occurred.")
            print(e)

    def do_destroy(self, _line):
        """
        Destroy container.
        destroy <container_name>
        """
        try:
            args = _line.split(' ')
            container = args[0]
            for node in self._fie.absnode_map:
                for c in self._fie.absnode_map[node].container_list:
                    if c.name == container:
                        self._fie.absnode_map[node].container_list.remove(c)
                        c.destroy()
        except Exception as e:
            print("internal error occurred.")
            print(e)
