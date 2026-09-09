#!/bin/bash -e

install -v -d "${ROOTFS_DIR}/etc/NetworkManager/conf.d"
install -v -m 644 files/10-ethernet-linklocal.conf \
	"${ROOTFS_DIR}/etc/NetworkManager/conf.d/10-ethernet-linklocal.conf"
