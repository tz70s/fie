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
from mininet.link import TCIntf
from mininet.topolib import TreeTopo
from examples.consoles import ConsoleApp

import psutil

"""
This work is a demonstration of bridging network namespace in mininet and docker containers

Architecture:
    =======     ========
    |     |     |Docker|---CONTAINER
    |netns|=====|      |---CONTAINER
    |     |     |Bridge|---CONTAINER
    =======     ========

"""

class bighost():
        
    """
    Initialize host/namespace informations

    """
    def __init__(self, host, name, ip_pool, docker_client):
        self.host = host
        self.pid = str(host.pid)
        self.name = name
        self.ip_pool = ip_pool
        self.docker_client = docker_client
        
        sub_list = ip_pool.split('/')[0].split('.')
        sub_list[-1] = '1'
        self.gw = '.'.join(sub_list)
    
        self.container_list = [host.name]
        self.pid_list = [host.pid]

    """
    Inheritent mininet host cmd
    
    """
    def cmd(self, cmdstr):
        self.host.cmd(cmdstr)

    """
    create veth in network namespace
    
    """
    def pairNetns(self):
        # print(self.name + ' : add netns veth pair with docker bridge')
        
        create_link = 'ip link add ' + self.name + '-eth1' + ' type veth peer name docker-' + self.name + '-port'
        up_link = 'ip link set dev ' + self.name + '-eth1' + ' up'
        set_ns = 'ip link set netns ' + self.pid + ' dev ' + self.name + '-eth1'

        call(create_link.split(' '))
        call(up_link.split(' '))
        call(set_ns.split(' '))
        
        self.cmd( 'ifconfig ' + self.name + '-eth1 ' + self.gw)
        self.SetNATrules()

    """
    Set the network ip pool for new containers over specific network namespace
    
    """
    def setIPpool(self):

        ipam_pool = docker.types.IPAMPool( subnet = self.ip_pool)
        ipam_config = docker.types.IPAMConfig( pool_configs = [ipam_pool] )

        return ipam_config
    """
    Create docker network a.k.a linux bridge

    """
    def createBridge(self):
        opts = {
            'com.docker.network.bridge.name': 'netns-'+self.name,
                }
        self.dockerbridge = self.docker_client.networks.create('netns-'+self.name, driver='bridge', ipam=self.setIPpool(), options=opts)
        self.patchBridge()
    
    """
    Patch veth with docker network bridges

    """
    
    def patchBridge(self):
        call(['brctl', 'addif', 'netns-'+self.name, 'docker-'+self.name+'-port'])
        call(['ip', 'link', 'set', 'dev', 'docker-'+self.name+'-port', 'up'])
    
    """
    Remove devices
    """

    def destroy(self):
        for container in self.container_list:
            call(['docker', 'rm', '-f', container], stdout=open(os.devnull, "w"), stderr=STDOUT)
        self.dockerbridge.remove()
    
    """
    NAT rules setting inner host/namespace

    """

    def NATrules(self):
        postroute = 'iptables -t nat -A POSTROUTING -o ' + self.name + '-eth0 -j MASQUERADE'
        conn = 'iptables -A FORWARD -i ' + self.name + '-eth0 -o ' + self.name + '-eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT'
        accept = 'iptables -A FORWARD -i ' + self.name + '-eth1 -o ' + self.name + '-eth0 -j ACCEPT'
        
        return [postroute, conn, accept]
    
    def SetNATrules(self):
        for rules in self.NATrules():
            self.cmd(rules)
    
    def net(self):
        self.pairNetns()
        self.createBridge()
    
    """
    Set static route to a specific container subnet
    """
    
    def route(self, host):
        dest_ip = host.ip_pool.split('/')[0]
        dest_gw = host.host.IP(host.name+'-eth0')
        self.cmd('route add -net ' + dest_ip + ' netmask 255.255.255.0 gw ' + dest_gw + ' dev ' + self.name + '-eth0')
        # print(dest_ip)
    
    """
    Native shell operations
    TODO: Docker API Rewrite
    """
    def simpleRun(self, image):
        namestr = image.split('/')[-1]
        call(['docker', 'run', '-itd', '--cgroup-parent=/' + self.name, '--network=netns-' + self.name , '--name='+self.name+'-'+str(len(self.container_list)), image], stdout=open(os.devnull, "w"), stderr=STDOUT)
        
        self.pid_list.append(self.log_pid(self.name + '-' + str(len(self.container_list))))
        self.container_list.append(self.name+'-'+str(len(self.container_list)))
    
    """
    Grep the pid to log CPU/MEM/Disk utilizations
    """
    def log_pid(self, containerName):
        p = Popen(['sudo', 'docker', 'inspect', containerName], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate((""))
        inspect = json.loads(output)
        return int(inspect[0]["State"]["Pid"])

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

"""
Set static route for each host to all container subnets

"""
def routeAll(*args):
    for host in args:
        for another in args:
            if host == another:
                continue
            else:
                host.route(another)
"""
Using psutil to log namespace/containers utilization via PID
Current: Only CPU Percentages

"""
def logHost(*args):

    for host in args:
        print '\n'
        i = 0
        print('*** ' + host.name + ' utilization associate with docker containers ***')
        for pid in host.pid_list:
            p = psutil.Process(pid)
            with p.oneshot():
                print('Host/Container Names : ' + str(host.container_list[i]))
                print('     CPU Percentages : '+ str(p.cpu_percent()))
                i += 1
        print('\n')

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
    
    topo = TreeTopo( depth=1, fanout=4 )
    intf = custom(TCIntf, bw=3)
    host = custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025)
    net = Mininet( topo=topo, host=host, controller=Controller, intf=intf )
    hosts = [ net.getNodeByName( h  ) for h in topo.hosts() ]
    
    
    print("*** Create Simple Topology ***")
    
    for h in hosts:
        dest_gw = h.IP(h.name+'-eth0')
        print("*** " + h.name + " - IP Address : " + dest_gw + " ***")
        
#    h1 = net.addHost('h1', ip='10.0.0.1')
#    h2 = net.addHost('h2', ip='10.0.0.2')
   
#    s1 = net.addSwitch('s1')
#    net.addLink(h1, s1)
#    net.addLink(h2, s1)
    
    net.start()
    
    # print(h1.pid)
    # print(h2.pid)

    client = setClient()
    
    # Set hosts
    
    bighosts = {}
    
    sub = 10
    for h in hosts:
        sub += 1
        substr = str(sub)
        bighosts[h.name] = bighost(h, h.name, '192.168.' + substr + '.0/24', client)
        bighosts[h.name].net()
    
    bighosts['h1'].simpleRun('tz70s/node-server')
    bighosts['h1'].simpleRun('tz70s/busy-wait')
    bighosts['h2'].simpleRun('tz70s/busy-wait')
    bighosts['h3'].simpleRun('tz70s/node-server')
    bighosts['h4'].simpleRun('tz70s/busy-wait')
    
    call(["docker", "ps"])
    routeAll(bighosts['h1'], bighosts['h2'], bighosts['h3'], bighosts['h4'])
    
    os.system("gnome-terminal -e 'top'")
    # p= Popen('gnome-terminal', stdin=PIPE, stdout=PIPE, stderr=PIPE)
    # p.communicate(b"'hello world' stdin")
    logHost(bighosts['h1'], bighosts['h2'], bighosts['h3'], bighosts['h4'])
    CLI(net)
    # app = ConsoleApp( net, width=4 )
    # app.mainloop()
    net.stop()

    # destroy containers and bridges
    bighosts['h1'].destroy()
    bighosts['h2'].destroy()
    bighosts['h3'].destroy()
    bighosts['h4'].destroy()

if __name__ == '__main__':
    emptyNet()
