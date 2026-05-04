#!/bin/bash -e

install -m 644 files/cycling74.list "${ROOTFS_DIR}/etc/apt/sources.list.d/"
install -m 644 files/apt-cycling74-pubkey.asc "${ROOTFS_DIR}/usr/share/keyrings/apt-cycling74-pubkey.asc"
on_chroot << EOF
apt-get update
EOF
