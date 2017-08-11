#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

from mininet.node import CPULimitedHost
from mininet.cli import CLI
from mininet.util import custom
from mininet.link import TCIntf, Intf
from mininet.topo import Topo
from mininet.util import quietRun
from fie.absnode import AbstractionNode
from fie.env import Env
from fie.fie import FIE
import fie.utils


"""
Integration test. 
"""
def assert_eq(left, right, err_msg):
    if left != right:
        print(err_msg)
        exit(1)

class NetworkTopo( Topo ):
    """define network topo"""
    def build( self, **_opts ):

        # Add switches
        s1, s2, s3 = [ self.addSwitch( s ) for s in 's1', 's2', 's3' ]
        
        # Custom interface 
        DriverFogIntf = custom(TCIntf, bw=5)
        FogCloudIntf = custom(TCIntf, bw=15)
        CloudIntf = custom(TCIntf, bw=50)

        """Node capabilities settings"""
        cloud = self.addHost('cloud', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))
        fog = self.addHost('fog', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))
        driver = self.addHost('driver', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))

        self.addLink( s1, cloud, intf=CloudIntf )
        self.addLink( s1, s2, intf=FogCloudIntf )
        self.addLink( s1, s3, intf=FogCloudIntf )
        self.addLink( s2, fog, intf=FogCloudIntf )
        self.addLink( s3, driver, intf=DriverFogIntf )

def emulate():
    
    # Set mininet settings
    
    topo = NetworkTopo()
    net = FIE( topo=topo )
    
    # Test nodes exist

    net.start()
    net.routeAll()
    
    net.absnode_map['cloud'].run('tz70s/node-server')
    net.absnode_map['fog'].run('tz70s/node-server')
    net.absnode_map['driver'].run('tz70s/node-server')
    # Test containers ran up

    net.stop()

    # destroy containers and bridges
    net.absnode_map['cloud'].destroyall()
    net.absnode_map['fog'].destroyall()
    net.absnode_map['driver'].destroyall()

    # Test containers safely destroyed

if __name__ == '__main__':
    emulate()
