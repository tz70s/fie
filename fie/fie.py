#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

from mininet.net import Mininet
from mininet.node import (Node, Host, OVSKernelSwitch, DefaultController,
                          Controller)
from mininet.nodelib import NAT
from mininet.link import Link, Intf
from absnode import AbstractionNode
from env import Env


class FIE(Mininet):
    """FIE Class inherit from Mininet class as the core configuration"""

    def __init__(self, topo=None, switch=OVSKernelSwitch, host=Host,
                 controller=DefaultController, link=Link, intf=Intf,
                 build=True, xterms=False, cleanup=False, ipBase='10.0.0.0/8',
                 inNamespace=False,
                 autoSetMacs=False, autoStaticArp=False, autoPinCpus=False,
                 listenPort=None, waitConnected=False):

        Mininet.__init__(self, topo, switch, host,
                         controller, link, intf,
                         build, xterms, cleanup, ipBase,
                         inNamespace,
                         autoSetMacs, autoStaticArp, autoPinCpus,
                         listenPort, waitConnected)

        # We add abstraction nodes in this class.
        # Automatically wraps mininet host, containers, internal network

        self.absnode_map = {}
        e = Env(len(self.hosts))
        self.env = e

        for h in self.hosts:
            self.absnode_map[h.name] = AbstractionNode(
                h.name, h, e.assign_cidr(), e.docker_client)

    # May move to another ideal, meaningful place
    def routeAll(self):
        """(Add static) Route all the hosts"""
        for host in self.absnode_map:
            for another in self.absnode_map:
                if host == another:
                    continue
                else:
                    self.absnode_map[host].route(self.absnode_map[another])

    def node(self, index):
        return self.absnode_map[index]
