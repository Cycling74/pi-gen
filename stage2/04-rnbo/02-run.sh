#!/bin/bash -e

on_chroot <<- EOF
	apt-mark hold rnbooscquery
	echo "GOVERNOR=\"performance\"" > /etc/default/cpufrequtils
	echo "RemoveIPC=no" >> /etc/systemd/logind.conf
	echo snd-dummy >> /etc/modules
EOF
