# External Reference Snapshot Index

Date: 2026-07-30

The six shallow clones used by the explicit-root/title-demo audits were moved
out of `/tmp` and retained locally under `references/external/20260730/`.
That directory is intentionally ignored: nested Git histories and third-party
source are research inputs, not part of this repository's deliverable.

| Local directory | Upstream | Retained commit |
| --- | --- | --- |
| `PyTouhou` | `https://github.com/GovanifY/PyTouhou.git` | `fbfba5269cfc98def3ff0e899694d2686c8f9eac` |
| `hourglass-win32` | `https://github.com/TASEmulators/hourglass-win32.git` | `78fa7c6d2be1b5eb46b8d4c0a37e56af616e1a46` |
| `libTAS` | `https://github.com/clementgallet/libTAS.git` | `a1bffe9f990734993f795278408f639923e1deb0` |
| `th08-decomp` | `https://github.com/GensokyoClub/th08.git` | `84738749bdcf6cffabe8d0d76e17f19253a20d50` |
| `thprac` | `https://github.com/touhouworldcup/thprac.git` | `8b3338f4d2cc7853d5a32d30dc7d252dc50bf2b3` |
| `thtk` | `https://github.com/thpatch/thtk.git` | `892114a0fcaa0bbdaaecf3cb4ad56f758683fb40` |

The retained snapshot is about 51 MiB including nested `.git` directories.
Every clone was clean when retained.

## Use And Authority

- `th08-decomp`: useful for names, title/replay paths, and static
  cross-reference; central gameplay updates are incomplete and it is not an
  executor.
- `thtk`: useful for archive/data/ECL format tooling; opcode names are not
  shipped runtime semantics.
- `PyTouhou`: architectural precedent for separating gameplay stepping from
  rendering; it primarily targets TH06.
- `thprac`: practice/bootstrap precedent only. The automated solver continues
  to use the repository's native script/menu flow, not THPRAC.
- `libTAS` and `hourglass-win32`: savestate/rollback engineering references,
  not accepted TH08 state ownership or physical validation.

External agreement may suggest an IDA check but never overrides shipped
instructions, runtime evidence, or the connected IDB revalidation contract.
The detailed audits are:

- [explicit-root and title-demo audit](TH08_EXPLICIT_ROOT_AND_TITLE_DEMO_READ_ONLY_REVIEW_20260730.md);
- [replay wind-tunnel audit](TH08_REPLAY_WIND_TUNNEL_READ_ONLY_REVIEW_20260730.md); and
- [retained discussion input](EXPLICIT_ROOT_AND_TITLE_DEMO_DISCUSSION_INPUT_20260730.md).
