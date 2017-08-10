#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

"""
This file is modified from mininet/topo.py. 
"""

from mininet.topo import Topo

# TODO: May lacks some opts, may check later

class AbsTopo(Topo):
    """Custom methods into abstraction node form, inherit form topo"""
    def __init__(self, *args, **params):
        """Inherit the topo defined from mininet"""
        Topo.__init__(self, *args, **params)

    def add_abs_host( self, absnode ):
        """Rewrite addHost into the abstraction node form"""
        absnode.head_node = self.addHost(absnode.name, cls = absnode.head_node_cls)
        absnode.pid = str(absnode.head_node.pid)

    def add_abs_link(self, node1, absnode, port1=None, port2=None, key=None, **opts):
        """Rewrite addLink into the abstraction node form"""
        self.addLink(node1, absnode.headNode, port1, port2, key, **opts)