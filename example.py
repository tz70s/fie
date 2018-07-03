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
from fie.fie import FIE, emulation
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

# Custom network topology
# 
# Usage:
#
# 1. Add switches
# 2. Custom interface, the interfaces from peers are symmetric here
# 3. Custom hosts
# 4. Link switches and hosts
#
class NetworkTopology(Topo):

    " define network topo "

    def build(self, **_opts):

        # Add switches
        s1, s2, s3 = [self.addSwitch(s) for s in 's1', 's2', 's3']

        # Custom interfaces with bandwidth and delay limitation.
        DriverFogIntf = custom(TCIntf, bw=100, delay='10ms')
        FogCloudIntf = custom(TCIntf, bw=200, delay='100ms')
        InClusterIntf = custom(TCIntf, bw=1000)

        # Hardware interface

        # IntfName = "enp4s30xxxx"
        # checkIntf(IntfName)
        # patch hardware interface to switch s3
        # hardwareIntf = Intf( IntfName, node=s3 )

        # Node capabilities settings.
        # cloud0 represented a node sits in cloud (datacenter), in whick has a larger capacity. 
        cloud0 = self.addHost('cloud0', cls=custom(
            RSLimitedHost, cpu=0.5, mem=512))
        # cloud1 is same as cloud0 as a node sits in cloud.
        cloud1 = self.addHost('cloud1', cls=custom(
            RSLimitedHost, cpu=0.5, mem=512))

        # fog0 represented a node in fog layer, with medium capacity.
        fog0 = self.addHost('fog0', cls=custom(
            RSLimitedHost, cpu=0.3, mem=512))
        fog1 = self.addHost('fog1', cls=custom(
            RSLimitedHost, cpu=0.3, mem=512))

        # To simulate the vehicle data source.
        # These nodes will run vehicle data simulation and sends up to fog or cloud.
        car_src_0 = self.addHost('car_src_0', cls=custom(
            RSLimitedHost, cpu=0.3, mem=256))
        car_src_1 = self.addHost('car_src_1', cls=custom(
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

        self.addLink(s3, car_src_0, intf=InClusterIntf)
        self.addLink(s3, car_src_1, intf=InClusterIntf)

# Emulate the network topo

# The kwargsHelper function build up dictionary for running containers -> eliminate redundant code.
def kwargsHelper(name, role, location):
    return {
        'image': 'tz70s/reactive-city:0.1.6',
        'name': name,
        'dns': [implicit_dns()],
        'environment': {'CLUSTER_SEED_IP': 'controller.docker', 'CLUSTER_HOST_IP': name+'.docker'},
        'restart_policy': {'Name': 'always', 'MaximumRetryCount': 10},
        'command': '-r ' + role + ' -l ' + location
    }

# The service_deployment function is responsible for deploying containers in the emulated environment.
def service_deployment(net):

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

    # Run a DNS(Domain Name Service) container in cloud0.
    # This is common techniques in a microservice style,
    # the domain address can be resolved to ip address in each services.
    net.node('cloud0').run('phensley/docker-dns',
                           name='dns',
                           volumes={'/var/run/docker.sock': {'bind': '/docker.sock', 'mode': 'rw'}})

    # Run a controller node at the cloud1, actor system role is set to controller, location is set to cloud.
    # Same as following.
    net.node('cloud1').run(**kwargsHelper('controller', 'controller', 'cloud'))
    net.node('fog0').run(**kwargsHelper('partition', 'partition', 'fog-west'))
    net.node('fog1').run(**kwargsHelper('analytics', 'analytics', 'fog-west'))
    net.node('fog1').run(**kwargsHelper('reflector', 'reflector', 'fog-west'))
    net.node('car_src_0').run(**kwargsHelper('simulator', 'simulator', 'fog-west'))


if __name__ == '__main__':
    # The emulation function take two arguments:
    # 1. the build up topology, 2. the service_deployment function
    emulation(NetworkTopology(), service_deployment)
