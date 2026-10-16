# PoorDS4

> **This fork (`PoorDS4-Homebrew`, maintained by `RustedByte93`) is an unofficial fork** of [ItsBlurf/PoorDS4](https://github.com/ItsBlurf/PoorDS4) adding experimental GOT/`GLOB_DAT` import-hook scanning for `-fno-plt`-built homebrew such as ProsperoEden. ItsBlurf is the author and maintainer of upstream PoorDS4 and has not reviewed or endorsed this fork. See "Experimental: ProsperoEden (Switch Emulator) Support" below for what changed and what was and was not tested.

> PoorDS4 would not have been possible without the excellent work behind
> [Ghostcontrol](https://github.com/StonedModder/Ghostcontrol-PS5-USB-Controller-Patcher)
> by StonedModder. Its controller research and PS5 payload foundation made this
> project possible, this project will eventually be merged to it later on if stoned Modder agrees even though its different now.
> I'm only using this for testing and gathering logs from testers until its fully stable and make this implementation much cleaner.
> PoorDS4 also relies on the
> [PS5 Payload SDK](https://github.com/ps5-payload-dev/sdk) and the remote-syscall
> interface documented by [kstuff-lite](https://github.com/EchoStretch/kstuff-lite).

PoorDS4 lets a wireless DualShock 4 paired with a jailbroken PS5
control native PS5 games. It does not require USB, a DualSense, a second user,
or a profile-selection prompt. Native DualSense controllers remain on Sony's
original input path and can be used independently for local multiplayer.

This is experimental homebrew that modifies a running game's pad imports.
Compatibility checks fail closed, but untested firmware and games can still
crash. Save your gamesave before testing (it broke the save file of a game during very early builds testings, never happened again but there is stil the risk so this is your disclaimer to save your work).

## Requirements

- A jailbroken PS5 with a compatible HEN/kstuff environment and ELF loader.
- A wireless DualShock 4 paired with the PS5 and connected to a logged-in user.
- Firmware 11.60 for the currently live-tested configuration. See
  [firmware support](docs/FIRMWARE_SUPPORT.md) before testing another version.

## Quick start

1. **Bluetooth Pairing**: Put your DualShock 4 into pairing mode by holding `SHARE` + `PS Button` together until the lightbar starts double-blinking rapidly. On the PS5, go to `Settings > Accessories > Bluetooth Accessories` and select **DUALSHOCK 4**.
2. **Controller Profile**: Connect the DS4 to whichever user profile should play (Player 1 or Player 2). If Player 1 is already using a native DualSense, connect the DS4 under Player 2's profile.
3. **Deploy Payload**: Send `PoorDS4rc51.elf` to the console's ELF loader (port 9021). The game may already be running or launched afterward.
4. **Play**: Wait for the `wireless DS4 active` notification, then play normally.

Only run one automatic instance. PoorDS4 follows later game launches without reinjection. It performs safe cleanup before rest mode; reinject after waking. Use `PoorDS4-stop.elf` before replacing a running build.

## In-Game Hotkeys & Reset Combo

- **Universal Reset Shortcut (`L1 + R1 + L2 + R2` held for ~400ms)**:
  Holding `L1 + R1 + L2 + R2` simultaneously on **any connected controller** (DS4 or DualSense) triggers an instant in-game re-synchronization. PoorDS4 will quiesce active hooks, re-evaluate all game pad slots, re-bind the controller to the correct profile, and re-attach seamlessly without needing to reinject the payload.
  Use this shortcut if:
  - You switched user profiles in the middle of a game session.
  - Player 2 joined late after the title screen.
  - You want to force a clean re-detection of the controller table.

## Controller Compatibility & Multiplayer

- **Supported Controllers**: Sony DualShock 4 v1 (`054c:05c4`), DS4 v2 (`054c:09cc`), and official Sony wireless USB adapters (`054c:0ba0`).
- **Multi-Controller & Player 2**: Fully supported. DualSense controllers remain strictly on their original Sony hardware input path and are never clobbered or stolen. PoorDS4 detects open/waiting player slots and binds cleanly to Player 2 alongside a Player 1 DualSense.
- **Native DualSense Touchpad Emulation**: Touchpad geometry is spoofed at native `1920x1080` resolution matching DualSense hardware, ensuring full compatibility with Unreal Engine 4/5 titles, Stellar Blade, and EA Sports FC 26.

## How it works

1. Enumerate the logged-in and Invite users' pad slots.
2. Identify a live DS4 through public device metadata and Sony's DS4 API.
3. Read its 120-byte `ScePadData` state at 120 Hz in `SceRemotePlay`.
4. Wait for one fully initialized native game process.
5. Validate the game's pad ABI, client table, player slot, import owners, and
   target mappings before changing anything.
6. Redirect only validated pad imports to a game-owned anonymous mapping and
   publish translated frames through a double buffer.

The game is never ptraced, stopped, or used to run a borrowed thread. No eboot
or `libScePad` code page is patched, and no game heap, socket, or thread is
created. See the [architecture document](docs/ARCHITECTURE.md) for the exact
safety and cleanup invariants.

## Firmware compatibility

| Firmware | Status |
| --- | --- |
| 6.02 (`0x06020004`) | Exact manifest and dynamic table stride (`0x548`) verified from memory dumps |
| 8.60 (`0x08600004`) | RC39 installed cleanly; RC42/RC43 includes queued/state source reader, source-context setup, and native-frame preservation |
| 10.01 (`0x10010000`) | Exact manifest and stride (`0x5c8`) verified from memory dumps |
| 11.60 (`0x11600005`) | Live-tested across multiple games (Greak, Pragmata, JoJo, FC 26), multiple connection orders, reconnects, and rest cleanup |
| 12.40 (`0x12400009`) | Exact manifest verified from supplied reports and memory dumps |
| Other | Dynamic table stride discovery (`0x548`/`0x5c8`) and structural verification allow execution if ABI matches; fails closed safely |

Compatibility is based on proven ABI structure, not a broad `11.xx` or `12.xx`
version assumption. Unknown layouts fail closed and produce a report instead
of installing hooks. See [docs/FIRMWARE_SUPPORT.md](docs/FIRMWARE_SUPPORT.md).

## Build

Install the official [ps5-payload-sdk](https://github.com/ps5-payload-dev/sdk),
set `PS5_PAYLOAD_SDK`, then build from the repository root:

```sh
make -C payload clean
make -C payload release
```

On the Windows PS5 development workspace used for release builds, load the
environment and select its target wrapper explicitly:

```powershell
. .\ps5dev-env.ps1
make -C payload CC=ps5-clang.cmd clean
make -C payload CC=ps5-clang.cmd release audit
```

RC51 release assets use ps5-payload-sdk v0.42:

| Output | Purpose |
| --- | --- |
| `PoorDS4rc51.elf` | Automatic wireless DS4 bridge |
| `PoorDS4-status.elf` | Read-only bridge status snapshot |
| `PoorDS4-stop.elf` | Cooperative stop request |

## Logs and compatibility reports

Diagnostics are stored under `/data/poords4/`:

- `game-pad-bridge.log` and `game-pad-bridge.log.1`
- `game-pad-bridge-supervisor.txt`
- `game-pad-bridge-last.txt`
- `game-pad-bridge-status.txt` after running the status ELF
- `reports/source-fw-XXXXXXXX-pid-N.txt`
- `reports/fw-XXXXXXXX-pid-N.txt`

For a firmware or game incompatibility, copy the complete `/data/poords4/`
directory and include the steps that reproduced the failure. Source and game
reports identify `poords4_rc` and `report_schema`. Review reports before posting
them publicly because they contain runtime process addresses and controller
diagnostics.

## Experimental: ProsperoEden (Switch Emulator) Support — This Fork

> **This section describes an unofficial, experimental change made in this
> fork (`PoorDS4-Homebrew` by RustedByte93).** It has not been reviewed or
> endorsed by ItsBlurf, the author of upstream PoorDS4. Please do not direct
> bug reports about this change to the upstream project.

### What changed and why

Upstream PoorDS4's import scanner (`game_bridge_collect_import_hooks` in
`payload/wireless_ds4.c`) only walked `.rela.plt` (`R_X86_64_JUMP_SLOT`)
relocations. The public [ProsperoEden](https://github.com/A1vinSmith/prosperoeden)
Switch emulator source is built with `-fno-plt`, so its calls into
`scePadRead`/`scePadReadState` compile to `R_X86_64_GLOB_DAT` entries in
`.rela.dyn` instead of PLT stubs — a binary built that way is invisible to the
original PLT-only scan, which finds zero hooks for it.

This fork adds a second relocation table to the same scan: `.rela.dyn`
entries are accepted **only** when the relocation type is `GLOB_DAT`, the
addend is zero, the symbol is undefined (`SHN_UNDEF`) with type `FUNC`/`NOTYPE`,
and the resolved name matches one of the seven known ScePad import symbols
exactly (no prefix matching — a prior version of this logic could in theory
misidentify `scePadReadState` as `scePadRead` since one name is a prefix of
the other; this fork requires an exact name match or a correctly terminated
NID). All existing safety checks are unchanged: module ownership filtering,
table bounds/overflow checks, slot-must-still-hold-the-original-pointer
verification before any write, duplicate-slot rejection, and the existing
rollback path that un-patches already-installed hooks if a later hook in the
same batch fails to install. No hook-installation or rollback code was
modified — only which relocation entries are considered candidates.

### What was actually tested

- **Confirmed on hardware** by a tester running `PoorDS4-rc51-prospero-exp1.elf`
  on a PS5 Slim, firmware 13.60 (this is the build attached to this release),
  across several different games inside ProsperoEden:
  - DualShock 4 buttons, sticks, and D-pad.
  - Touchpad input.
  - Motion sensors (gyro/accelerometer).
  - The tester describes overall behavior across the games tried as working
    well. This is a hands-on tester report, not an automated test, and does
    not cover every game or ProsperoEden build.
- **Confirmed not working**: DS4 rumble/vibration. The maintainer is actively
  working on this; it is not part of what this release claims to support.
- **Confirmed by automated tests** (`tests/import-scanner-test.py`, run against
  the real collector function, not a reimplementation): 21 cases covering
  GOT/PLT relocation handling, NID and full-name identity matching, table
  bounds, ownership filtering, and stale-hook discovery; plus a regression
  test proving the unmodified upstream scanner finds zero hooks on a
  `-fno-plt`-style fixture that this fork's scanner correctly detects.
- **Not verified / explicitly out of scope for this release**:
  - Adaptive triggers or any DualSense feature parity — this project does not
    touch the native DualSense input path at all.
  - Exhaustive coverage of every Switch game or ProsperoEden build — testing
    so far covers multiple games, not all of them.
  - Any multiplayer/multi-controller configuration under ProsperoEden, or any
    firmware other than 13.60.
  - Behavior if a module is loaded/unloaded concurrently with the scan, or
    survival of a hard kernel panic mid-write — these were not exercised on
    real hardware and are inherited, unchanged, from upstream's existing
    hook-install/rollback mechanism.
- **Known test-suite limitation**: this fork's `tests/static-audit-portable.py`
  (a portable re-implementation of upstream's `tests/static-audit.ps1`) will
  report one failing assertion — the hard-coded tracked-file inventory check —
  because this fork adds three new tracked files (`tools/build-experimental.sh`,
  `tests/import-scanner-test.py`, `tests/static-audit-portable.py`) that the
  upstream list does not know about. All functional assertions, including the
  21 real-collector cases, pass.

### The three release binaries

| File | Purpose |
| --- | --- |
| `PoorDS4-rc51-prospero-exp1.elf` | Main bridge. Load this to start the experimental bridge. |
| `PoorDS4-status-prospero-exp1.elf` | Read-only status snapshot of the running bridge; writes a report, does not start anything. |
| `PoorDS4-stop-prospero-exp1.elf` | Cooperative stop request to an already-running bridge instance. |

### Pairing, loading, and verifying it worked

1. Pair your DualShock 4 over Bluetooth to the PS5 user profile that will run
   ProsperoEden (`Settings > Accessories > Bluetooth Accessories`).
2. If a build of this bridge (or the official `PoorDS4rc51.elf`) is already
   running, load `PoorDS4-stop-prospero-exp1.elf` first and wait for it to
   finish before loading another main payload. Never run two main bridge
   instances at once.
3. Load `PoorDS4-rc51-prospero-exp1.elf` through your ELF loader (port 9021).
4. Open ProsperoEden. Check `/data/poords4/game-pad-bridge-supervisor.txt` for
   `build_id=rc51-prospero-exp1` and look for an `import_hook ... relocation=GLOB_DAT`
   line followed by `result=1` in the reports under `/data/poords4/reports/`.
5. Run `PoorDS4-status-prospero-exp1.elf` while ProsperoEden is still open to
   capture a status snapshot if you want to report back.

### Reverting to the official build

Load `PoorDS4-stop-prospero-exp1.elf`, wait for the existing instance to stop,
then load the official `PoorDS4rc51.elf` from the
[upstream project](https://github.com/ItsBlurf/PoorDS4). No reinstall of
ProsperoEden or the jailbreak environment is required.

### Warning

This is **experimental, unofficial** homebrew. Crashes may occur. Back up your
saves before testing. Do not add this build to autoload while testing — load
it manually each time.

## Multi-Controller Support (Experimental)

PoorDS4 now supports streaming multiple wireless DS4 controllers concurrently (up to 4 controllers as Player 1..Player 4), along with simulated controller channels and native DualSense passthrough. Please note that multi-controller support is currently **experimental** as I haven't done heavy testing with multiple physical DS4s yet because I don't have a reliable second DualShock 4 controller. If you have multiple DS4 controllers, please test them out and let me know how they work!

## Testers Needed

I need testers especially for firmwares **13.40**, **13.20**, **13.00**, **12.60**, and **9.60**. If you encounter any bugs, crashes, or want to contribute test logs, please zip the entire `/data/poords4/` folder on your PS5 and send it over in GitHub issues or reach out to me directly on Discord (`blurf.`).

## Special Thanks & Shoutout

A huge shoutout to [reyzinhoplayoliver-design](https://github.com/reyzinhoplayoliver-design) / `ElCauaRey` on Discord for helping with a lot of testing and finding bugs!

## Donations & Support

If you find PoorDS4 helpful and would like to support faster future development, hardware acquisition (like additional controllers and testing gear), and maintenance, please consider donating:

- **PayPal**: [paypal.me/nblurf](https://paypal.me/nblurf)
- **Bitcoin (BTC Network)**: `1CW8JWSnWc5w7yKhYk7ixAFG487nU5Jrzc`
- **USDT (Tron / TRC20)**: `TRcrCeonXzgyxjR4LGzo4JdfEHYGGqD3gX`

## Attribution and license

PoorDS4 is a focused wireless-DS4 derivative of Ghostcontrol. The original USB
implementations and binaries are intentionally not distributed in this tree.
See [NOTICE.md](NOTICE.md) for detailed credits and [LICENSE](LICENSE) for the
GPL-3.0-or-later terms.
