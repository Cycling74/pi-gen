#!/bin/bash -e

on_chroot <<- EOF
	apt-mark hold rnbooscquery
	debconf-set-selections <<< "jackd2 jackd/tweak_rt_limits boolean true"
	dpkg-reconfigure -fnoninteractive jackd2
EOF
