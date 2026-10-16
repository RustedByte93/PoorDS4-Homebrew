# Attribution

PoorDS4 would not have been possible without
[Ghostcontrol](https://github.com/StonedModder/Ghostcontrol-PS5-USB-Controller-Patcher)
and its author, StonedModder. Ghostcontrol supplied the original project base,
controller research, PS5 process-injection groundwork, and the early pad bridge
work from which PoorDS4 was developed. The public repository intentionally
remains a GitHub fork so that this relationship is visible alongside this
notice.

PoorDS4 also depends on and gratefully acknowledges:

- [ps5-payload-sdk](https://github.com/ps5-payload-dev/sdk), maintained by John
  Törnblom and its contributors, for the PS5 payload toolchain, headers, loader
  ABI, kernel helpers, and mdbg interfaces;
- [kstuff-lite](https://github.com/EchoStretch/kstuff-lite), maintained by
  EchoStretch and based on the original kstuff research, for the remote-syscall
  ABI used to allocate the game-owned bridge mapping.

The current tree is deliberately limited to the wireless DualShock 4 bridge.
Ghostcontrol's USB controller implementations, launchers, research documents,
and compiled binaries are not redistributed here; their authorship remains in
the shared upstream Git history.

PoorDS4 is distributed under GPL-3.0-or-later. See [LICENSE](LICENSE).

## Fork notice (this repository)

This repository (`PoorDS4-Homebrew`) is an unofficial fork of
[ItsBlurf/PoorDS4](https://github.com/ItsBlurf/PoorDS4), maintained by
`RustedByte93`. All attributions above apply unchanged to the inherited code.
ItsBlurf is the author and maintainer of upstream PoorDS4; ItsBlurf has not
reviewed, tested, or endorsed the changes in this fork. This fork adds a
single, narrowly-scoped change — GOT/`GLOB_DAT` relocation scanning alongside
the existing PLT scan, to support `-fno-plt`-built homebrew such as
ProsperoEden — described in the README and CHANGELOG. No other part of
upstream PoorDS4 was modified.
