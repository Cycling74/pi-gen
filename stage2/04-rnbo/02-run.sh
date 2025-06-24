#!/bin/bash -e

on_chroot <<- EOF
	apt-mark hold rnbooscquery
	debconf-set-selections <<< "jackd2 jackd/tweak_rt_limits boolean true"
	dpkg-reconfigure -fnoninteractive jackd2
	echo "GOVERNOR=\"performance\"" > /etc/default/cpufrequtils
	echo "RemoveIPC=no" >> /etc/systemd/logind.conf
	echo snd-dummy >> /etc/modules
EOF
