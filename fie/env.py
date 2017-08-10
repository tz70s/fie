#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

import docker
import fie

class Env(object):
    """The declaration of some share variables."""
    def __init__(self, node_num):
        self.docker_client = self.init_docker_client()
        self.cidr_list = self.set_cidr(node_num)
        self.used_list = [False] * node_num

    def init_docker_client(self):
        """Init docker client for docker daemon api """
        client = docker.DockerClient(base_url = 'unix://var/run/docker.sock', version = 'auto')
        return client

    def set_cidr(self, node_num):
        """Set CIDR for private ip pool assignment, return a list of cidrs"""
        # TODO: support this, extend to ip_addr class C
        if node_num > 200:
            print("We don't support nodes exceed 200 currently")
            exit(1)
        
        sub = node_num
        cidr_list = []
        for _ in range(node_num):
            sub += 1
            substr = str(sub)
            cidr_list.append('192.168.' + substr + '.0/24')
        return cidr_list

    def assign_cidr(self):
        """Assign CIDR for an absraction node, return a string from this method"""
        for i in range(len(self.used_list)):
            if self.used_list[i] is False:
                self.used_list[i] = True
                return self.cidr_list[i]
        return ""

    def routeAll(self, *args):
        """(Add static) Route all the hosts"""
        for host in args:
            for another in args:
                if host == another:
                    continue
                else:
                    host.route(another)