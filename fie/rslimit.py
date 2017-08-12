#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

"""
This file is modified from mininet/node.py. 
"""

from mininet.node import CPULimitedHost, Host, Node
from mininet.util import ( quietRun, errFail )
from mininet.log import error


class RSLimitedHost(CPULimitedHost):
    def __init__( self, name, sched='cfs', **kwargs ):
        Host.__init__( self, name, **kwargs )
        # Initialize class if necessary
        if not RSLimitedHost.inited:
            RSLimitedHost.init()
        
        # TODO: Add DISK
        self.cgroup = 'cpu,cpuacct,cpuset,memory:/' + self.name
        errFail( 'cgcreate -g ' + self.cgroup )
        errFail( 'cgclassify -g cpu,cpuacct,memory:/%s %s' % ( self.name, self.pid ) )

        self.period_us = kwargs.get( 'period_us', 100000 )
        self.sched = sched
        if sched == 'rt':
            self.checkRtGroupSched()
            self.rtprio = 20

    def setMem( self, mem=0):
        if mem == 0:
            return
        # The mininmum memory limitation is 1MB
        if mem < 1:
            mem = 1
        mega = 1024*1024
        self.cgroupSet( resource = 'memory', param='limit_in_bytes', value=mem*mega)
        errFail( 'cgclassify -g memory:/%s %s' % (
                 self.name, self.pid ) )

    # overwrite the setCPUs method
    def setCPUs( self, cores):
        "Specify (real) cores that our cgroup can run on"
        if not cores:
            return
        if isinstance( cores, list ):
            cores = ','.join( [ str( c ) for c in cores ] )

        self.cgroupSet( resource='cpuset', param='cpus',
                        value=cores )
        errFail( 'cgclassify -g cpuset:/%s %s' % (
                 self.name, self.pid ) )
    # overwrite
    def config( self, cpu=-1, cores=None, mem=0, **params):
        """This will overwrite the configuration from CPULimitedHost"""
        r = Node.config( self, **params)

        # Add memory for params, mininet already add to setCPUs function, but not used though.
        self.setParam(r, 'setCPUFrac', cpu=cpu)
        self.setParam(r, 'setMem', mems=mem)
        self.setParam(r, 'setCPUs', cores=cores)
        return r