#!/bin/bash -e

# Expand only the expected values on the build host; inspect installed state
# inside the target rootfs before pi-gen exports it.
on_chroot <<EOF
set -eu
actual=\$(dpkg-query -W -f='\${Version}' rnbooscquery)
test "\$actual" = "${RNBO_RUNNER_VERSION}"
test "\$(dpkg --print-architecture)" = "${ARCH}"
. /etc/os-release
test "\$VERSION_CODENAME" = "${RELEASE}"
apt-mark showhold | grep -qx rnbooscquery
id -nG "${FIRST_USER_NAME}" | tr ' ' '\n' | grep -qx audio
grep -Eq '^@audio[[:space:]]+-[[:space:]]+rtprio[[:space:]]+95([[:space:]]|$)' /etc/security/limits.d/audio.conf
grep -Eq '^@audio[[:space:]]+-[[:space:]]+memlock[[:space:]]+unlimited([[:space:]]|$)' /etc/security/limits.d/audio.conf
EOF
