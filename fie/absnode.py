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
from mininet.util import custom
from container import Container


class AbstractionNode():
    """
     Initialize host/namespace informations
        head_node, 
        pid of head_node, 
        name of abstraction node, 
        ip_pool,
        cgroup,
        docker client
        network,
        container_list,
        pid_list 
    as necessary params
    """

    def __init__(self, name, head_node, ip_pool, docker_client, **opts):
        """Initialization"""
        self.head_node = head_node
        self.pid = str(head_node.pid)
        self.name = name
        self.ip_pool = ip_pool
        self.gw = self.create_gateway()
        self.cg = "/" + self.name

        # Network name for creating bridge
        self.network = 'netns-' + self.name

        # Initialize docker client
        self.docker_client = docker_client

        # Initialize lists of containers and pids

        self.container_list = []
        self.pid_list = []

        self.dockerbridge = None

        self.net_default()

    def cmd(self, cmdstr):
        """Inherit mininet host cmd"""
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

    def net_default(self):
        """The default network settings inner abstraction node"""
        self.create_veth()
        self.createBridge()
        self.set_nat_rules()

    def create_gateway(self):
        """Create the gateway of abstraction node route"""
        sub_list = self.ip_pool.split('/')[0].split('.')
        sub_list[-1] = '1'
        return '.'.join(sub_list)

    def create_veth(self):
        """Create additional veth for head_node (eth1)"""
        # print(self.name + ' : add netns veth pair with docker bridge')

        create_link = 'ip link add ' + self.name + '-eth1' + \
            ' type veth peer name ' + self.name + '-dport'
        up_link = 'ip link set dev ' + self.name + '-eth1' + ' up'
        set_ns = 'ip link set netns ' + self.pid + ' dev ' + self.name + '-eth1' + ' up'

        call(create_link.split(' '))
        call(up_link.split(' '))
        call(set_ns.split(' '))

        self.cmd('ifconfig ' + self.name + '-eth1 ' + self.gw)
        self.cmd('route add -net ' + self.ip_pool.split('/')
                 [0] + ' netmask 255.255.255.0 gw ' + self.gw + ' dev ' + self.name + '-eth1')

    def createBridge(self):
        """Create docker network a.k.a linux bridge"""

        # Up the parent interface, a.k.a xxx-dport
        call(['ip', 'link', 'set', 'dev', self.name+'-dport', 'up'])

        # Set the network ip pool for new containers over specific network namespace
        ipam_pool = docker.types.IPAMPool(subnet=self.ip_pool, gateway=self.gw)
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

        opts = {
            'parent': self.name+'-dport'
        }

        self.dockerbridge = self.docker_client.networks.create(
            self.network, driver='macvlan', ipam=ipam_config, options=opts)

    def set_nat_rules(self):
        """NAT rules setting inner host/namespace"""
        rules = []

        # Postroute
        rules.append('iptables -t nat -A POSTROUTING -o ' +
                     self.name + '-eth0 -j MASQUERADE')

        # Conn
        rules.append('iptables -A FORWARD -i ' + self.name + '-eth0 -o ' +
                     self.name + '-eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT')

        # Accept
        rules.append('iptables -A FORWARD -i ' + self.name +
                     '-eth1 -o ' + self.name + '-eth0 -j ACCEPT')

        for rule in rules:
            self.cmd(rule)

    """
    Containers management here, have some functions.
        1. Run a container
        2. Destroy specific container
        3. Destroy all containers
    """

    def run(self, image, **params):
        """Run a container and add information into the lists keep from abstraction node"""

        # Create a class of container
        c = Container(docker_client=self.docker_client, image=image, cg_parent=self.cg,
                      network=self.network, name_parent=self.name, count=len(self.container_list), **params)
        c.run()
        self.container_list.append(c)
        self.pid_list.append(c.log_pid)

    def stop(self, container):
        """Destroy specific container"""
        for c in self.container_list:
            if c.name == container:
                c.stop()
                return "Successful stop container : " + c.name
        return "The target container to stop doesn't exist!"

    # Stop all
    def stopall(self):
        """Checkout all containers in container_list and stop all of them"""
        for c in self.container_list:
            c.stop()
        # REMARK: the container stop command doesn't remove the docker network

    def destroy(self, container):
        """Destroy specific container"""
        for c in self.container_list:
            if c.name == container:
                c.destroy()
                return "Successful destory container : " + c.name
        return "The target container to destroy doesn't exist!"

    # Destroy all
    def destroyall(self):
        """Checkout all containers in container_list and remove all of them"""
        for c in self.container_list:
            c.destroy()
        self.dockerbridge.remove()

    # Set static route
    def route(self, host):
        """Set static route to a specific container subnet"""
        dest_ip = host.ip_pool.split('/')[0]
        dest_gw = host.head_node.IP(host.name+'-eth0')
        self.cmd('route add -net ' + dest_ip + ' netmask 255.255.255.0 gw ' +
                 dest_gw + ' dev ' + self.name + '-eth0')
