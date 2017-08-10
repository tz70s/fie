#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

"""
The declaration of abstraction node class in this file.
Checkout the docs for more detailed abstraction node concepts.
"""

import docker
import os

from subprocess import call
from subprocess import STDOUT, Popen, PIPE

from mininet.util import custom
from mininet.node import CPULimitedHost

from container import Container


class AbstractionNode():
            
    # Initialize host/namespace informations

    def __init__(self, name, head_node, ip_pool, docker_client, **opts):
        
        # self.head_node_cls = self.config_head_node(**opts)
        self.head_node = head_node
        self.pid = str(head_node.pid)
        self.name = name
        self.ip_pool = ip_pool
        self.gw = self.create_gateway()
        self.cg = self.name

        # Network name for creating bridge
        self.network = 'netns-' + self.name

        # Initialize docker client
        self.docker_client = docker_client
        
        # Initialize lists of containers and pids 

        self.container_list = []
        self.pid_list = []

        self.container_list_true = []
        self.dockerbridge = None

        self.net_default()

    # Create a mininet host as an abstraction node's head node
    # TODO: USE resource limited host instead of CPULimitedHost
    
    
    # Inheritent mininet host cmd
    def cmd(self, cmdstr):
        self.head_node.cmd(cmdstr)

    """
    Internal network from head_node to containers
    We should do following things,
        1. Create gateway of abstraction node route
        2. Create additional veth for head_node (eth1)
        3. Create Bridge and Patch with head_node veth
        4. Set nat rules inner head_node
        5. Set ip pools for docker containers

    Architecture:
        =======     ========
        |     |     |Docker|---CONTAINER
        |netns|=====|      |---CONTAINER
        |     |     |Bridge|---CONTAINER
        =======     ========
    """

    # The default network settings inner abstraction node
    def net_default(self):
        self.create_veth()
        self.createBridge()
        self.set_nat_rules()

    # Create the gateway of abstraction node route
    def create_gateway(self):
        sub_list = self.ip_pool.split('/')[0].split('.')
        sub_list[-1] = '1'
        return '.'.join(sub_list)

    # Create additional veth for head_node (eth1)
    def create_veth(self):
        # print(self.name + ' : add netns veth pair with docker bridge')
        
        create_link = 'ip link add ' + self.name + '-eth1' + ' type veth peer name ' + self.name + '-dport'
        up_link = 'ip link set dev ' + self.name + '-eth1' + ' up'
        set_ns = 'ip link set netns ' + self.pid + ' dev ' + self.name + '-eth1'

        call(create_link.split(' '))
        call(up_link.split(' '))
        call(set_ns.split(' '))
        
        self.cmd( 'ifconfig ' + self.name + '-eth1 ' + self.gw)
    
    # Create docker network a.k.a linux bridge
    def createBridge(self):

        # Set the network ip pool for new containers over specific network namespace
        ipam_pool = docker.types.IPAMPool( subnet = self.ip_pool)
        ipam_config = docker.types.IPAMConfig( pool_configs = [ipam_pool] )
        
        
        opts = {
            'com.docker.network.bridge.name': self.network,
        }

        self.dockerbridge = self.docker_client.networks.create(self.network, driver='bridge', ipam=ipam_config, options=opts)
        
        # Patch veth with docker network bridges
        call(['brctl', 'addif', self.network, self.name+'-dport'])
        call(['ip', 'link', 'set', 'dev', self.name+'-dport', 'up'])

    # NAT rules setting inner host/namespace
    def set_nat_rules(self):
        rules = []

        # Postroute
        rules.append('iptables -t nat -A POSTROUTING -o ' + self.name + '-eth0 -j MASQUERADE')
        # Conn
        rules.append('iptables -A FORWARD -i ' + self.name + '-eth0 -o ' + self.name + '-eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT')
        # Accept
        rules.append('iptables -A FORWARD -i ' + self.name + '-eth1 -o ' + self.name + '-eth0 -j ACCEPT')
        
        for rule in rules:
            self.cmd(rule)

    """
    Containers management here, have some functions.
        1. Run a container
        2. Destroy specific container
        3. Destroy all containers
    """

    # Run a container and add information into the lists keep from abstraction node
    def run(self, image):
        # Create a class of container
        c = Container(docker_client=self.docker_client, image=image, cg_parent=self.cg, network=self.network, name_parent = self.name, count=len(self.container_list_true))
        c.run()
        self.container_list.append(c)
        self.pid_list.append(c.log_pid)
        
    # Destroy specific container
    def destroy(self, container):
        for c in self.container_list:
            if c.name == container:
                c.destroy()
                return "Successful destory container : " + c.name
        return "The target container to destroy doesn't exist!"

    # Destroy all
    def destroyall(self):
        # Checkout all containers in container_list and remove all of them
        # TODO: Safe remove
        for c in self.container_list:
            c.destroy()
        self.dockerbridge.remove()
    
    # Consider to remove this
    # Set static route to a specific container subnet
    def route(self, host):
        dest_ip = host.ip_pool.split('/')[0]
        dest_gw = host.head_node.IP(host.name+'-eth0')
        self.cmd('route add -net ' + dest_ip + ' netmask 255.255.255.0 gw ' + dest_gw + ' dev ' + self.name + '-eth0')