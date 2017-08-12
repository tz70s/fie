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

class Container(object):
    """The declaration of container, important method, run, log_pid, destroy"""
    def __init__(self, docker_client, image, cg_parent, network, name_parent, count, **params):
        self.docker_client = docker_client
        self.image = image
        self.cg_parent = cg_parent
        self.network = network
        # count represented as the numbers of abstraction node containers list, used for dealing with naming conflicts. 
        self.name = name_parent + '-' + str(count)
        self.pid = None
        self.params = params
        self.container = None

    def run(self):
        """Run an container"""
        self.container = self.docker_client.containers.run( 
            image=self.image,
            detach=True, 
            name=self.name, 
            network=self.network, 
            cgroup_parent=self.cg_parent,
            **self.params
            )
        # CHECK THIS: if the pid appears soon after the container created?
        # self.pid = self.log_pid()
    
    # TODO: Currently, this start is useless, we should find additonal way to let this container start parameters to available since abstraction node
    def start(self):
        self.container.start(
            image=self.image,
            detach=True, 
            name=self.name, 
            network=self.network, 
            cgroup_parent=self.cg_parent,
            **self.params)
    def log_pid(self):
        """Logs pid of container, return a string"""
        p = Popen(['sudo', 'docker', 'inspect', self.name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, _ = p.communicate((""))
        inspect = json.loads(output)
        return int(inspect[0]["State"]["Pid"])

    def stop(self):
        """Stop the running container"""

        self.container.stop()

    def destroy(self):
        """Destroy the running container"""

        # CONCERN: Do we really need the step of safe stop?
        # timeout 10 secs
        # self.container.stop()
        self.container.remove(force=True)
        