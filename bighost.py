#!/usr/bin/python

from subprocess import call
import docker

from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.log import setLogLevel, info

"""
This work is a demonstration of bridging network namespace in mininet and docker containers

Architecture:
    =======     ========
    |     |     |Docker|---CONTAINER
    |netns|=====|      |---CONTAINER
    |     |     |Bridge|---CONTAINER
    =======     ========

"""


"""
Class bighost for creating object associate with network namespace and docker containers/bridges informations

pairNetns() : create veth in network namespace

setIPpool() : set the network ip pool for new containers over specific network namespace

createBridge() : create docker network a.k.a linux bridge

patchBridge() : patch the linux bridge with namespace veth

setNATrule() : set NAT rules


"""
class bighost():
    
    def __init__(self, pid, name, ip_pool, docker_client):
        self.pid = pid
        self.name = name
        self.ip_pool = ip_pool
        self.docker_client = docker_client
        
        sub_list = ip_pool.split('/')[0].split('.')
        sub_list[-1] = '1'
        self.gw = '.'.join(sub_list)

    def pairNetns(self):
        print(self.name + ' : add netns veth pair with docker bridge')
        
        create_link = 'ip link add ' + self.name + '-eth1' + ' type veth peer name docker-' + self.name + '-port'
        up_link = 'ip link set dev ' + self.name + '-eth1' + ' up'
        set_ns = 'ip link set netns ' + self.pid + ' dev ' + self.name + '-eth1'

        call(create_link.split(' '))
        call(up_link.split(' '))
        call(set_ns.split(' '))
    

    def setIPpool(self):

        ipam_pool = docker.types.IPAMPool( subnet = self.ip_pool)
        ipam_config = docker.types.IPAMConfig( pool_configs = [ipam_pool] )

        return ipam_config
    
    def createBridge(self):
        opts = {
            'com.docker.network.bridge.name': 'netns-'+self.name,
                }
        self.dockerbridge = self.docker_client.networks.create('netns-'+self.name, driver='bridge', ipam=self.setIPpool(), options=opts)
        self.patchBridge()
    
    def patchBridge(self):
        call(['brctl', 'addif', 'netns-'+self.name, 'docker-'+self.name+'-port'])
        call(['ip', 'link', 'set', 'dev', 'docker-'+self.name+'-port', 'up'])
    
    def destroy(self):
        self.dockerbridge.remove()

    def setNATrule(self):
        postroute = 'iptables -t nat -A POSTROUTING -o ' + self.name + '-eth0 -j MASQUERADE'
        conn = 'iptables -A FORWARD -i ' + self.name + '-eth0 -o ' + self.name + '-eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT'
        accept = 'iptables -A FORWARD -i ' + self.name + '-eth1 -o ' + self.name + '-eth0 -j ACCEPT'
        
        return [postroute, conn, accept]
    def simpleRun(self, image):
        namestr = image.split('/')[-1]
        call(['docker', 'run', '-itd', '--network=netns-' + self.name , '--name='+self.name+'-'+namestr, image])

def setClient():
    client = docker.DockerClient(base_url = 'unix://var/run/docker.sock', version = 'auto')
    return client

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


def emptyNet():
    
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
    net = Mininet( controller=Controller )

    net.addController( 'c0' )

    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')

    s1 = net.addSwitch('s1')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.start()
    
    # print(h1.pid)
    # print(h2.pid)

    client = setClient()

    host1 = bighost(str(h1.pid), 'h1', '192.168.52.0/24', client)

    host1.pairNetns()
    host1.createBridge()
    h1.cmd( 'ifconfig h1-eth1 ' + host1.gw)
    for rule in host1.setNATrule():
        h1.cmd(rule)

    host2 = bighost(str(h2.pid), 'h2', '192.168.53.0/24', client)
    host2.pairNetns()
    host2.createBridge()
    h2.cmd('ifconfig h2-eth1 ' + host2.gw)
    for rule in host2.setNATrule():
        h2.cmd(rule)

    # container = client.containers.run(image='tz70s/node-server', detach=True, networks=['netns-'+host1.name,], name=host1.name+'app1')
    host1.simpleRun('tz70s/node-server')
    host2.simpleRun('ubuntu')
    CLI(net)

    net.stop()

    # destroy containers
    call(['docker', 'rm', '-f', host1.name+'-node-server'])
    call(['docker', 'rm', '-f', host2.name+'-ubuntu'])
    host1.destroy()
    host2.destroy()

if __name__ == '__main__':
    emptyNet()
