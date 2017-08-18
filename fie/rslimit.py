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
from subprocess import call, check_call


class RSLimitedHost(CPULimitedHost):
    """The Resource Limited Host Class"""
    def __init__( self, name, sched='cfs', **kwargs ):
        """Initailized Resource Limited Host Class"""
        Host.__init__( self, name, **kwargs )
        # Initialize class if necessary
        if not RSLimitedHost.inited:
            RSLimitedHost.init()
        
        self.cgroup = 'cpu,cpuacct,cpuset,memory,blkio:/' + self.name

        errFail( 'cgcreate -g ' + self.cgroup )
        errFail( 'cgclassify -g cpu,cpuacct,memory,blkio:/%s %s' % ( self.name, self.pid ) )

        self.period_us = kwargs.get( 'period_us', 100000 )
        self.sched = sched
        if sched == 'rt':
            self.checkRtGroupSched()
            self.rtprio = 20

    # Overwrite cgroupSet for ignore blkio
    def cgroupSet( self, param, value, resource='cpu' ):
        "Set a cgroup parameter and return its value"

        # Replace the old form to the new string formatting in python
        cmd = 'cgset -r {0}.{1}={2} /{3}'.format(resource, param, value, self.name)
        
        # Mininet will split the whitespaces into list for subprocess call...
        # In the blkio, we need whitespaces in a " ", can't be used
        # That is, use shell=True flag instead.

        if resource == 'blkio':
            call(cmd, shell=True)
        else:
            quietRun(cmd)

        # TODO: Currently, we don't check for blkio.
        if resource is 'blkio':
            return value
        if resource is 'memory':
            if param is 'oom_control':
                return value

        nvalue = int( self.cgroupGet( param, resource ) )
        if nvalue != value:
            error( '*** error: cgroupSet: %s set to %s instead of %s\n'
                   % ( param, nvalue, value ) )
        return nvalue


    # We'll not dealing with logging statistics here
    # Set cgroup memory metrics, support:
    #     memory_limit_in_bytes,
    #     oom_control (0 or 1),
    #     swapniess (0-100),
    #     memorysw_limit_in_bytes

    # Originally we want to support kmem_limit_in_bytes, but (in linux cgroup manual)
    #   => The limit cannot be set if the cgroup have children, or if there are already tasks in the cgroup

  
    def setMem( self, mem=0):
        """
        Set memory hard limit.
        The mininmum memory limitation is 1MB, and the basic unit is also 1MB.
        """

        if mem != 0:
            if mem < 1:
                mem = 1
            # 1MB
            mega = 1024*1024
            self.cgroupSet( resource = 'memory', param='limit_in_bytes', value=mem*mega)

    def setMemSW( self, memsw=0):
        """
        Set virtual memory hard limit.
        The mininmum memory limitation is 1MB, and the basic unit is also 1MB.
        """

        if memsw != 0:
            if memsw < 1:
                memsw = 1
            # 1MB
            mega = 1024*1024
            self.cgroupSet( resource = 'memory', param='memsw.limit_in_bytes', value=memsw*mega)

    def setOOM(self, oom_control=0):
        """Out of memory enable/disable"""

        if oom_control == 1:
            self.cgroupSet( resource = 'memory', param='oom_control', value=1)
        
    def setSwappiness(self, swappiness=None):
        """Swappiness capabilities"""

        if swappiness != None and swappiness >= 0 and swappiness <= 100:
            self.cgroupSet( resource = 'memory', param='swappiness', value=swappiness)

    # We'll not dealing with logging statistics in blkio.
    # Set cgroup io metrics, support:
    #     device_write_bps,
    #     device_write_iops,
    #     device_read_bps,
    #     device_read_iops,
    #     blkio_weight,
    #     blkio_weight_device
    
    def setDeviceWriteBps(self, device_write_bps=None):
        """Device_write_bps"""
        if device_write_bps != None:
            self.cgroupSet( resource='blkio', param='throttle.write_bps_device',
            value=str('\"' + device_write_bps + '\"'))
    
    def setDeviceWriteIOps(self, device_write_iops=None):
        """Device_write_iops"""
        if device_write_iops != None:
            self.cgroupSet( resource='blkio', param='throttle.write_iops_device',
            value='"' + device_write_iops + '"' )

    def setDeviceReadBps(self, device_read_bps=None):
        """Device_read_bps"""
        if device_read_bps != None:
            self.cgroupSet( resource='blkio', param='throttle.read_bps_device',
            value='"' + device_read_bps + '"' )

    def setDeviceReadIOps(self, device_read_iops=None):
        """Device_read_iops"""
        if device_read_iops != None:
            self.cgroupSet( resource='blkio', param='throttle.read_iops_device',
            value='"' + device_read_iops + '"' )

    def setBlkioWeight(self, blkio_weight=None):
        """Blkio_weight"""
        if blkio_weight != None and blkio_weight >= 10 and blkio_weight <= 1000:
            self.cgroupSet( resource='blkio', param='weight',
            value=blkio_weight )

    def setBlkioWeightDevice(self, blkio_weight_device=None):
        """Blkio_weight_device"""
        if blkio_weight_device != None and int(blkio_weight_device.split()[-1]) >= 10 and int(blkio_weight_device.split()[-1]) <= 1000:
            self.cgroupSet( resource='blkio', param='weight_device',
            value='"' + blkio_weight_device + '"' )

    # Overwrite config
    def config( self,
        cpu=-1,cores=None,
        mem=0, memsw=0, oom_control=0, swappiness=None,
        device_write_bps=None, device_write_iops=None,
        device_read_bps=None, device_read_iops=None,
        blkio_weight=None, blkio_weight_device=None,
        **params ):
        """This will overwrite the configuration from CPULimitedHost"""
        r = Node.config( self, **params)

        # Add memory for params, mininet already add to setCPUs function, but not used though.
        self.setParam(r, 'setCPUFrac', cpu=cpu)
        self.setParam(r, 'setMem', mem=mem)
        self.setParam(r, 'setMemSw', memsw=memsw)
        self.setParam(r, 'setOOM', oom_control=oom_control)
        self.setParam(r, 'setSwappiness', swappiness=swappiness)
        self.setParam(r, 'setCPUs', cores=cores)
        self.setParam(r, 'setDeviceWriteBps', device_write_bps=device_write_bps)
        self.setParam(r, 'setDeviceWriteIOps', device_write_iops=device_write_iops)
        self.setParam(r, 'setDeviceReadBps', device_read_bps=device_read_bps)
        self.setParam(r, 'setDeviceReadIOps', device_read_iops=device_read_iops)
        self.setParam(r, 'setBlkioWeight', blkio_weight=blkio_weight)
        self.setParam(r, 'setBlkioWeightDevice', blkio_weight_device=blkio_weight_device)

        return r
