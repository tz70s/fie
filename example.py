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

class NetworkTopo( Topo ):

    " define network topo "

    def build( self, **_opts ):

        # Add switches
        s1, s2, s3 = [ self.addSwitch( s ) for s in 's1', 's2', 's3' ]
        
        # Custom interface 
        DriverFogIntf = custom(TCIntf, bw=5)
        FogCloudIntf = custom(TCIntf, bw=15)
        CloudIntf = custom(TCIntf, bw=50)

        # Hardware interface
        
        # IntfName = "enp4s30xxxx"
        # checkIntf(IntfName)
        # patch hardware interface to switch s3
        # hardwareIntf = Intf( IntfName, node=s3 )

        """
        Node capabilities settings
        """

        cloud = self.addHost('cloud', cls=custom(RSLimitedHost, cpu=0.1,
            mem=10, memsw=20, oom_control=1, swappiness=60,
            device_write_bps="8:0 1024")) # /dev/sda write 1024 bytes per sec 
        
        fog = self.addHost('fog', cls=custom(RSLimitedHost, cpu=0.1, mem=10))
        driver = self.addHost('driver', cls=custom(RSLimitedHost, cpu=0.1, mem=10))

        self.addLink( s1, cloud, intf=CloudIntf )
        self.addLink( s1, s2, intf=FogCloudIntf )
        self.addLink( s1, s3, intf=FogCloudIntf )
        self.addLink( s2, fog, intf=FogCloudIntf )
        self.addLink( s3, driver, intf=DriverFogIntf )

# Emulate the network topo
def emulate():
    
    print("""

Demonstration of fog infrastructure emulation.
    
Architecture:
    =======     ========
    |     |     |Docker|---CONTAINER
    |netns|=====|      |---CONTAINER
    |     |     |Bridge|---CONTAINER
    =======     ========
    
    """
    )
    
    # Set mininet settings
    topo = NetworkTopo()
    # The abstraction node automatically wrapped here.
    net = FIE( topo=topo )
    
    try:
        net.start()
        net.routeAll()
        
        net.absnode_map['cloud'].run('tz70s/kuery:0.1.3.1')
        net.absnode_map['fog'].run('tz70s/kuery:0.1.3.1')
        net.absnode_map['driver'].run('tz70s/kuery:0.1.3.1')
        FCLI(net)

    finally:
        net.absnode_map['cloud'].destroyall()
        net.absnode_map['fog'].destroyall()
        net.absnode_map['driver'].destroyall()
        net.stop()

if __name__ == '__main__':
    emulate()