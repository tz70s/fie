#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

from subprocess import call
from subprocess import STDOUT, Popen, PIPE
import os
import docker
import json

"""
TODO: Use Docker python API instead of shell command for more options.
"""
def init_docker_client():
    client = docker.DockerClient(base_url = 'unix://var/run/docker.sock', version = 'auto')
    return client

# TODO: Modify the "name" due to ambiguity
class Container():
    def __init__(self, client, image, cg_parent, network, name_parent, count):
        self.client = client
        self.image = image
        self.cg_parent = cg_parent
        self.network = network
        # count represented as the numbers of abstraction node containers list, used for dealing with naming conflicts. 
        self.name = name_parent + '-' + str(count)
        self.pid = "none"
    
    # Run an container
    def run(self):
        namestr = image.split('/')[-1]

        call(['docker', 'run', '-itd', '--cgroup-parent=/' + self.cg_parent, \
            '--network=' + self.network , \
            '--name=' + self.name, image], \
            stdout=open(os.devnull, "w"), stderr=STDOUT)
        
        # CHECK THIS: if the pid appears soon after the container created?
        self.pid = self.log_pid(self.name)
    
    # Logs pid of container, return a string
    def log_pid(self):
        p = Popen(['sudo', 'docker', 'inspect', self.name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate((""))
        inspect = json.loads(output)
        return int(inspect[0]["State"]["Pid"])
    
    # Destroy the running container
    def destroy(self):
        call(['docker', 'rm', '-f', self.name], stdout=open(os.devnull, "w"), stderr=STDOUT)
