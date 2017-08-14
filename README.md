# Fog Infrastructure Emulation

An enironement for evaluating containerized applications based-on mininet.

[![Build Status](https://travis-ci.org/tz70s/fie.svg?branch=master)](https://travis-ci.org/tz70s/fie)

### Abstraction Node
We extend cgroups and set _internal_ network topo for multiple containers run along with original mininet network namespace, which we name it as an **_Abstraction Node_**. The abstraction node is **close to the real world PC that we use**.

### Support Extended Resource Limitation Options

For **_CPU_**,

* `cpu_cfs_period`
* `cpu_cfs_runtime`
* `cpu_cfs_share`
* `cpu_rt_period`
* `cpu_rt_runtime`
* `cpu_rt_share`

For **_Memory_**,

* `memory_hard_limit`
* `memory_oom_control`
* `memory_swappiness`
* `memory_memsw_limit`

For **_Blkio_**,

* `blkio_write_bps_device`
* `blkio_write_iops_device`
* `blkio_read_bps_device`
* `blkio_read_iops_device`
* `blkio_weight`
* `blkio_weight_device`

### Installation

```BASH
# Install dep
sudo ./scripts/install.sh
# Dependencies
pip install docker
```

### Execution

```BASH
# Add dependencies
export PYTHONPATH = "$PYTHONPATH:/path/to/mininet"
export PYTHONPATH = "$PYTHONPATH:/path/to/fie"

# Run an example
sudo ./example.py
```
