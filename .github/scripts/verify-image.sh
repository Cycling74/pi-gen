#!/bin/bash -e

# Pass expected values as arguments; inspect installed state inside the target
# rootfs before pi-gen exports it.
on_chroot -s -- "${RNBO_RUNNER_VERSION}" "${ARCH}" "${RELEASE}" "${FIRST_USER_NAME}" <<'EOF'
set -eu

check_equal() {
    printf 'Verify %s: expected [%s], found [%s]\n' "$1" "$2" "$3"
    if [ "$2" != "$3" ]; then
        printf 'Image verification failed: %s\n' "$1" >&2
        exit 1
    fi
}

check_equal 'RNBO runner version' "$1" "$(dpkg-query -W -f='${Version}' rnbooscquery)"
check_equal 'package architecture' "$2" "$(dpkg --print-architecture)"
. /etc/os-release
check_equal 'OS release' "$3" "${VERSION_CODENAME:-missing}"
# Query dpkg's selection directly. apt-mark showhold can omit the held package
# in the freshly built rootfs even when dpkg correctly records it as held.
check_equal 'RNBO package hold' hold "$(dpkg-query -W -f='${db:Status-Want}' rnbooscquery)"

printf 'Verify audio group membership for %s\n' "$4"
if ! id -nG "$4" | tr ' ' '\n' | grep -qx audio; then
    printf 'Image verification failed: user is not in the audio group\n' >&2
    exit 1
fi

for setting in 'rtprio 95' 'memlock unlimited'; do
    read -r key value <<< "$setting"
    printf 'Verify JACK %s = %s\n' "$key" "$value"
    if ! grep -Eq "^@audio[[:space:]]+-[[:space:]]+$key[[:space:]]+$value([[:space:]]|$)" /etc/security/limits.d/audio.conf; then
        printf 'Image verification failed: JACK %s limit\n' "$key" >&2
        exit 1
    fi
done
EOF
