#!/bin/bash -e

# Install the configuration files before the kernels, then defer both kernel
# postinst generation and APT-triggered updates until final image export.
sed -i 's/^update_initramfs=.*/update_initramfs=no/' "${ROOTFS_DIR}/etc/initramfs-tools/update-initramfs.conf"

# Keep any pre-existing setting intact underneath this temporary override.
# Removing an earlier copy makes restarting this stage safe.
sed -i '/^SKIP_INITRAMFS_GEN=yes # pi-gen build only$/d' "${ROOTFS_DIR}/etc/default/raspi-firmware"
echo 'SKIP_INITRAMFS_GEN=yes # pi-gen build only' >> "${ROOTFS_DIR}/etc/default/raspi-firmware"
