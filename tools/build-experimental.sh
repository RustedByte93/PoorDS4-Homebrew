#!/usr/bin/env bash
set -euo pipefail
: "${PS5_PAYLOAD_SDK:?Set PS5_PAYLOAD_SDK to the extracted official SDK v0.42}"
root=$(cd "$(dirname "$0")/.." && pwd)
sdk=$(cd "$PS5_PAYLOAD_SDK" && pwd -P)
# SDK v0.42's linker wrapper expands its script path without quoting. A symlink
# is insufficient because the wrapper calls realpath. Use a disposable copy.
temporary_sdk=
trap 'if [[ -n "$temporary_sdk" ]]; then rm -rf "$temporary_sdk"; fi' EXIT
if [[ "$sdk" == *' '* ]]; then
    temporary_sdk=$(mktemp -d /tmp/poords4-sdk.XXXXXX)
    cp -R "$sdk/." "$temporary_sdk/"
    sdk=$temporary_sdk
fi
export PS5_PAYLOAD_SDK=$sdk
make -C "$root/payload" experimental status stop
mkdir -p "$root/dist"
cp "$root/payload/PoorDS4-rc51-prospero-exp1.elf" "$root/dist/"
cp "$root/payload/PoorDS4-status.elf" "$root/dist/PoorDS4-status-prospero-exp1.elf"
cp "$root/payload/PoorDS4-stop.elf" "$root/dist/PoorDS4-stop-prospero-exp1.elf"
"$sdk/bin/prospero-strip" --strip-debug "$root/dist/"*.elf
(cd "$root/dist" && shasum -a 256 ./*.elf > SHA256SUMS)
printf 'Experimental artifacts: %s/dist\n' "$root"
