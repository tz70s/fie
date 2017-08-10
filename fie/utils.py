#!/usr/bin/python

"""
This work targets for emulating fog computing infrastructure and fog service and network evaluation.
Original author Tzu-Chiao Yeh (@tz70s), 2017@National Taiwan University, Dependable Distributed System and Network Lab.
Checkout the License for using, modifying and publishing.
"""

from mininet.util import quietRun


def checkIntf( intf ):
    "Make sure intf exists and is not configured."
    config = quietRun( 'ifconfig %s 2>/dev/null' % intf, shell=True )
    if not config:
        print( 'Error:', intf, 'does not exist!\n' )
        exit( 1 )

    # TODO: Regular expression
    ips = re.findall( r'\d+\.\d+\.\d+\.\d+', config )
    if ips:
        print( 'Error:', intf, 'has an IP address,'
               'and is probably in use!\n' )
        exit( 1 )