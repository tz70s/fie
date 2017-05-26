## Mininet example of the Multi-Docker-Containers-as-a-Single-Host 

A prototyping extension of mininet-based network emulation for integrating multi-containers-as-a-single-host concept. 
## Objective
1. To support multiple Docker containers “running” in a single host with no interference with the normal usage.
2. To clarify the Docker containers and original host scenario, we can name it as an “abstraction node” here. We should have an additional mechanism of the cpu, memory limitation of docker containers running in the “abstraction nodes”. 
3. Also, the original network namespace or Docker container which represented as a host should also be restricted in the abstraction node.

The specific host along with multiple containers are seen as a single identity.
1. User can set the resource limitation for the specific abstraction node.
2. User can set the resource limitation for the specific container running in the abstraction node.
3. User can choose to not set the resource limitation for the specific container running in the abstraction node, but the maximum resource usage of the containers running in the specific abstraction node will not exceed the limitation it sets.


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
# move to mininet module path or create links
./dock-mn.py
```


