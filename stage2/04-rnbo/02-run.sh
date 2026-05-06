#!/bin/bash -e

on_chroot <<- EOF
	apt-mark hold rnbooscquery
	debconf-set-selections <<< "jackd2 jackd/tweak_rt_limits boolean true"
	dpkg-reconfigure -fnoninteractive jackd2
	cat > /etc/systemd/system/cpupower.service << 'UNIT'
[Unit]
Description=Set CPU governor to performance
After=sysinit.target

[Service]
Type=oneshot
ExecStart=/usr/bin/cpupower frequency-set -g performance
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT
	systemctl enable cpupower.service
	echo "RemoveIPC=no" >> /etc/systemd/logind.conf
	echo snd-dummy >> /etc/modules
EOF
