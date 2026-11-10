#!/bin/bash -e

if [ ! -f "${ROOTFS_DIR}/etc/kernel-img.conf" ]; then
	echo "do_symlinks=0" > "${ROOTFS_DIR}/etc/kernel-img.conf"
fi
rm -f "${ROOTFS_DIR}/"{vmlinuz,initrd.img}*
