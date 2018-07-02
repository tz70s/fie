#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""


from fie.cli import FCLI
from mininet.util import custom
from mininet.link import TCIntf, Intf
from mininet.topo import Topo
from mininet.util import quietRun
from fie.absnode import AbstractionNode
from fie.env import Env
from fie.fie import FIE
from fie.rslimit import RSLimitedHost
import fie.utils
from fie.utils import implicit_dns
import time

"""
Simple emptyNet for h1, h2, s1, c0 architecture

h1 runs on 10.0.0.1 along with 192.168.52.0/24 subnet and a node-server app
h2 runs on 10.0.0.2 along with 192.168.53.0/24 subnet and a ubuntu app

Each host can ping each other and works with the docker application on itself:
    $h1 curl -qa 192.168.52.2:8181
    $h2 ping 192.168.53.2

Testing for cross-hosts:
    # set static routes
    $h1 route add -net 192.168.53.0 netmask 255.255.255.0 gw 10.0.0.2 dev h1-eth0
    $h2 route add -net 192.168.52.0 netmask 255.255.255.0 gw 10.0.0.1 dev h2-eth0

    # cross-hosts tests
    $h2 curl -qa 192.168.52.2:8181
    $h1 ping 192.168.53.2

"""

"""
Custom network topology

Usage
1. Add switches
2. Custom interface, the interfaces from peers are symmetric here
3. Custom hosts
4. Link switches and hosts

"""


class NetworkTopo(Topo):

    " define network topo "

    def build(self, **_opts):

        # Add switches
        s1, s2, s3 = [self.addSwitch(s) for s in 's1', 's2', 's3']

        # Custom interface
        DriverFogIntf = custom(TCIntf, bw=100, delay='10ms')
        FogCloudIntf = custom(TCIntf, bw=200, delay='100ms')
        InClusterIntf = custom(TCIntf, bw=1000)

        # Hardware interface

        # IntfName = "enp4s30xxxx"
        # checkIntf(IntfName)
        # patch hardware interface to switch s3
        # hardwareIntf = Intf( IntfName, node=s3 )

        """
        Node capabilities settings
        """

        cloud0 = self.addHost('cloud0', cls=custom(
            RSLimitedHost, cpu=0.5, mem=512))
        cloud1 = self.addHost('cloud1', cls=custom(
            RSLimitedHost, cpu=0.5, mem=512))

        fog0 = self.addHost('fog0', cls=custom(
            RSLimitedHost, cpu=0.3, mem=512))
        fog1 = self.addHost('fog1', cls=custom(
            RSLimitedHost, cpu=0.3, mem=512))

        driver0 = self.addHost('driver0', cls=custom(
            RSLimitedHost, cpu=0.3, mem=256))
        driver1 = self.addHost('driver1', cls=custom(
            RSLimitedHost, cpu=0.3, mem=256))

        # Link switch s1 with cloud nodes.
        self.addLink(s1, cloud0, intf=InClusterIntf)
        self.addLink(s1, cloud1, intf=InClusterIntf)

        # s1 -- s2
        self.addLink(s1, s2, intf=FogCloudIntf)
        # s2 -- s3
        self.addLink(s2, s3, intf=DriverFogIntf)

        # Link switch s2 with fog nodes
        self.addLink(s2, fog0, intf=InClusterIntf)
        self.addLink(s2, fog1, intf=InClusterIntf)

        self.addLink(s3, driver0, intf=InClusterIntf)
        self.addLink(s3, driver1, intf=InClusterIntf)

# Emulate the network topo


def failSafe(emulateFunc):
    # Set mininet settings
    topo = NetworkTopo()
    # The abstraction node automatically wrapped here.
    net = FIE(topo=topo)

    try:
        net.start()
        net.routeAll()
        emulateFunc(net)
    finally:
        for n in net.absnode_map:
            net.absnode_map[n].destroyall()
        net.stop()


def akkaHelper(name, role, location):
    return {
        'image': 'tz70s/reactive-city:0.1.4',
        'name': name,
        'dns': [implicit_dns()],
        'environment': {'CLUSTER_SEED_IP': 'controller.docker', 'CLUSTER_HOST_IP': name+'.docker'},
        'command': '-r ' + role + ' -l ' + location
    }


def emulate(net):

    print("""

Demonstration of fog infrastructure emulation.

Architecture:
    =======     =========
    |     |     |       |---CONTAINER
    |netns|=====|macvlan|---CONTAINER
    |     |     |       |---CONTAINER
    =======     =========

    """
          )

    # Create DNS service in cloud.
    net.node('cloud0').run('phensley/docker-dns',
                           name='dns',
                           volumes={'/var/run/docker.sock': {'bind': '/docker.sock', 'mode': 'rw'}})

    net.node('cloud1').run(**akkaHelper('controller', 'controller', 'cloud'))
    net.node('fog0').run(**akkaHelper('partition', 'partition', 'fog-west'))
    net.node('fog1').run(**akkaHelper('analytics', 'analytics', 'fog-west'))
    net.node('fog1').run(**akkaHelper('reflector', 'reflector', 'fog-west'))
    net.node('driver0').run(**akkaHelper('simulator', 'simulator', 'fog-west'))

    FCLI(net)


if __name__ == '__main__':
    failSafe(emulate)
