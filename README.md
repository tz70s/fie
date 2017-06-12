## Mininet example of the Multi-Docker-Containers-as-a-Single-Host 

A prototyping extension of mininet-based network emulation for integrating multi-containers-as-a-single-host concept.

## Objective

1. To support multiple Docker containers “running” in a single host with no interference with the normal usage.
2. To clarify the Docker containers and original host scenario, we can name it as an “abstraction node” here. We should have an additional mechanism of the cpu, memory limitation of docker containers running in the “abstraction nodes”. 
3. Also, the original network namespace or Docker container which represented as a host should also be restricted in the abstraction node.

## The specific host along with multiple containers are seen as a single identity - abstraction node

1. User can set the resource limitation for the specific abstraction node.
2. User can set the resource limitation for the specific container running in the abstraction node.
3. User can choose to not set the resource limitation for the specific container running in the abstraction node, but the maximum resource usage of the containers running in the specific abstraction node will not exceed the limitation it sets.

## [Reference issue](https://github.com/containernet/containernet/issues/29)

* python verison

```BASH
# Problems of mininet support python3
2.7.12

# Dependencies
Pip install docker
Pip install pyutil

```

* mininet version

```BASH
2.3.0d1
``` 

* Execution

```BASH
# Install dep
sudo ./start.sh

# move to mininet module path or create links
# run in root

sudo ./mininet/mininet/dock-mn.py
```

## Configuration

```python
class NetworkTopo( Topo ):

    " define network topo "

    def build( self, **_opts ):

        # Add switches
        s1, s2, s3 = [ self.addSwitch( s ) for s in 's1', 's2', 's3' ]
        
        # Custom interface 
        DriverFogIntf = custom(TCIntf, bw=5)
        FogCloudIntf = custom(TCIntf, bw=15)
        CloudIntf = custom(TCIntf, bw=50)

        """
        Node capabilities settings
        """
        
        # custom hosts, adjust cpu utilization in cpu metrics
        cloud = self.addHost('cloud', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))
        fog = self.addHost('fog', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))
        driver = self.addHost('driver', cls=custom(CPULimitedHost, sched='cfs', period_us=50000, cpu=0.025))

        # link hosts, switches, and interfaces
        self.addLink( s1, cloud, intf=CloudIntf )
        self.addLink( s1, s2, intf=FogCloudIntf )
        self.addLink( s1, s3, intf=FogCloudIntf )
        self.addLink( s2, fog, intf=FogCloudIntf )
        self.addLink( s3, driver, intf=DriverFogIntf )
```

## Run docker images

```python

# ports need to write in docker file, no port-forward here

bighosts['cloud'].simpleRun('tz70s/node-server')
bighosts['fog'].simpleRun('tz70s/busy-wait')
bighosts['driver'].simpleRun('tz70s/busy-wait')

# remember to destroy

# destroy containers and bridges
bighosts['cloud'].destroy()
bighosts['fog'].destroy()
bighosts['driver'].destroy()

```

