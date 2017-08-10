#!/bin/bash

set -x

# Install Docker
	
sudo apt-get update
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
sudo apt-add-repository 'deb https://apt.dockerproject.org/repo ubuntu-xenial main'
sudo apt-get update
apt-cache policy docker-engine
sudo apt-get install -y python docker-engine uuid-dev git python-pip bridge-utils
sudo usermod -a -G docker $(whoami) # Add user to the docker group
	
# clone mininet

cd $(HOME)
git clone git://github.com/mininet/mininet.git

# install mininet
cd mininet
sudo util/install.sh -a

pip install docker

export PYTHONPATH="$PYTHONPATH:$(HOME)/mininet/mininet"
export PYTHONPATH="$PYTHONPATH:$(HOME)/fie"