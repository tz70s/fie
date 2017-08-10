#!/usr/bin/python

from subprocess import call
from subprocess import STDOUT, Popen, PIPE
import os
import docker
import json

from mininet.net import Mininet
from mininet.node import Controller, CPULimitedHost
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import custom
from mininet.link import TCIntf, Intf
from mininet.topolib import TreeTopo
from mininet.topo import Topo
from mininet.util import quietRun
from fie.absnode import AbstractionNode
from fie.topo import AbsTopo
from fie.env import Env
from fie.fie import FIE



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

def checkIntf( intf ):
    "Make sure intf exists and is not configured."
    config = quietRun( 'ifconfig %s 2>/dev/null' % intf, shell=True )
    if not config:
        error( 'Error:', intf, 'does not exist!\n' )
        exit( 1 )
    ips = re.findall( r'\d+\.\d+\.\d+\.\d+', config )
    if ips:
        error( 'Error:', intf, 'has an IP address,'
               'and is probably in use!\n' )
        exit( 1 )

"""
Custom network topology

Usage

1. Add switches
2. Custom interface, the interfaces from peers are symmetric here
3. Custom hosts
4. Link switches and hosts

"""

class NetworkTopo( AbsTopo ):

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
        cloud = self.addHost('cloud', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))
        fog = self.addHost('fog', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))
        driver = self.addHost('driver', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))

        self.addLink( s1, cloud, intf=CloudIntf )
        self.addLink( s1, s2, intf=FogCloudIntf )
        self.addLink( s1, s3, intf=FogCloudIntf )
        self.addLink( s2, fog, intf=FogCloudIntf )
        self.addLink( s3, driver, intf=DriverFogIntf )

# Hardware interface

def emulate():
    
    print("""

This work is a demonstration of bridging network namespace in mininet and docker containers
    
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
    net = FIE( topo=topo )
    
    net.start()
    net.routeAll()
    
    # Set hosts
    
    
    net.absnode_map['cloud'].run('tz70s/node-server')
    net.absnode_map['fog'].run('tz70s/node-server')
    net.absnode_map['driver'].run('tz70s/node-server')
    
    # topo.routeAll()
    CLI(net)

    net.stop()

    # destroy containers and bridges
    net.absnode_map['cloud'].destroyall()
    net.absnode_map['fog'].destroyall()
    net.absnode_map['driver'].destroyall()

if __name__ == '__main__':
    emulate()