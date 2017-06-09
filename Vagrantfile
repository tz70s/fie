# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<SCRIPT

	if [ -e "/home/ubuntu/dockermn" ]; then
		echo " directory existed"
	else
		mkdir -p "/home/ubuntu/dockermn"
	fi
	
	# Install Docker
	sudo apt-get update
	sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
	sudo apt-add-repository 'deb https://apt.dockerproject.org/repo ubuntu-xenial main'
	sudo apt-get update
	apt-cache policy docker-engine
	sudo apt-get install -y python docker-engine uuid-dev git python-pip bridge-utils
	sudo usermod -a -G docker ubuntu # Add ubuntu user to the docker group
	
	cd /home/ubuntu/dockermn
	
	# clone mininet
	# git clone git://github.com/mininet/mininet.git

	# install mininet
	# cd mininet
	# sudo util/install.sh -a
	
	pip install docker psutil

	cd /home/ubuntu/dockermn
	cp dock-mn.py mininet/
SCRIPT

Vagrant.configure("2") do |config|
  
	config.vm.box = "ubuntu/xenial64"
	
 	config.vm.synced_folder ".", "/home/ubuntu/dockermn"

	config.vm.provision "shell", inline: $script

end
