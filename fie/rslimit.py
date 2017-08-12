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
        cmd = 'cgset -r %s.%s=%s /%s' % (
            resource, param, value, self.name )
        quietRun( cmd )

        # TODO: Currently, we don't check for blkio.
        if resource is 'blkio':
            return value

        nvalue = int( self.cgroupGet( param, resource ) )
        if nvalue != value:
            error( '*** error: cgroupSet: %s set to %s instead of %s\n'
                   % ( param, nvalue, value ) )
        return nvalue

    # We'll not dealing with logging statistics here
    def setMem( self, mem=0, kmem=0, oom_control=0, swappiness=None):
        """
        Set cgroup memory metrics, support:
            memory_limit_in_bytes,
            kmem_limit_in_bytes,
            oom_control (0 or 1),
            swapniess (0-100)
        """
        print ("SETMEM")

        # The mininmum memory limitation is 1MB
        # Memory hard limit
        if mem != 0:
            if mem < 1:
                mem = 1
            mega = 1024*1024
            self.cgroupSet( resource = 'memory', param='limit_in_bytes', value=mem*mega)
        
        # The mininmum kernel memory limitation is 1MB
        # Kernel memory hard limit
        if kmem != 0:
            if kmem < 1:
                kmem = 1
            mega = 1024*1024
            self.cgroupSet( resource = 'memory', param='kmem.limit_in_bytes', value=mem*mega)
        
        # Out of memory enable/disable
        if oom_control == 1:
            self.cgroupSet( resource = 'memory', param='oom_control', value=1)
        
        # Swappiness capabilities
        if swappiness != None and swappiness >= 0 and swappiness <= 100:
            self.cgroupSet( resource = 'memory', param='swappiness', value=swappiness)


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

    # We'll not dealing with logging statistics here
    
    def setBLKIO(self, 
        device_write_bps=None, device_write_iops=None,
        device_read_bps=None, device_read_iops=None,
        blkio_weight=None, blkio_weight_device=None):
        """
        Set cgroup io metrics, support:
            device_write_bps,
            device_write_iops,
            device_read_bps,
            device_read_iops,
            blkio_weight,
            blkio_weight_device
        """

        print ("SETBLKIO")

        if device_write_bps != None:
            self.cgroupSet( resource='blkio', param='throttle.write_bps_device',
            value='"' + device_write_bps + '"' )
            print('\"' + device_write_bps + '\"')
        else:
            print("None")

        if device_write_iops != None:
            self.cgroupSet( resource='blkio', param='throttle.write_iops_device',
            value='"' + device_write_iops + '"' )

        if device_read_bps != None:
            self.cgroupSet( resource='blkio', param='throttle.read_bps_device',
            value='"' + device_read_bps + '"' )
        
        if device_read_iops != None:
            self.cgroupSet( resource='blkio', param='throttle.read_iops_device',
            value='"' + device_read_iops + '"' )
        
        if blkio_weight != None and blkio_weight >= 10 and blkio_weight <= 1000:
            self.cgroupSet( resource='blkio', param='weight',
            value=blkio_weight )

        if blkio_weight_device != None and int(blkio_weight_device.split()[-1]) >= 10 and int(blkio_weight_device.split()[-1]) <= 1000:
            self.cgroupSet( resource='blkio', param='weight_device',
            value='"' + blkio_weight_device + '"' )

    # Overwrite config
    def config( self,
        cpu=-1,cores=None,
        mem=0, kmem=0, oom_control=0, swappiness=None,
        device_write_bps=None, device_write_iops=None,
        device_read_bps=None, device_read_iops=None,
        blkio_weight=None, blkio_weight_device=None,
        **params ):
        """This will overwrite the configuration from CPULimitedHost"""
        r = Node.config( self, **params)

        # Add memory for params, mininet already add to setCPUs function, but not used though.
        self.setParam(r, 'setCPUFrac', cpu=cpu)
        self.setParam(r, 'setMem', mem=mem, kmem=kmem, oom_control=oom_control, swappiness=swappiness)
        self.setParam(r, 'setCPUs', cores=cores)

        self.setParam(r, 'setBLKIO', device_write_bps=device_write_bps, device_write_iops=device_write_iops,
        device_read_bps=device_read_bps, device_read_iops=device_read_iops,
        blkio_weight=blkio_weight, blkio_weight_device=blkio_weight_device)

        return r