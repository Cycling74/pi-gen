#!/bin/bash -e

on_chroot <<- EOF
	apt-mark hold rnbooscquery
EOF
