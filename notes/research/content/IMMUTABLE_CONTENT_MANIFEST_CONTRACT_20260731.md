# Immutable TH08 Content-Manifest Contract

Date: 2026-07-31

Taskbook card: `CONTENT-01`

Status: content identity gate passed; no runtime-event or action authority

## Task Card

Question: can the shipped TH08 ECL, STD, ANM, and MSG content used by the
mandatory Lunatic workloads be pinned and independently reproduced before an
event atlas assigns semantic origins?

Hypothesis: pinned `thtk` extraction and the repository's native-derived
PBGZ/`edz?` decoders will agree byte for byte over the complete content scope,
and independent ECL parsers will agree on the exact instruction opcode
sequence.

Earliest decision effect: none. This is an offline content-identity gate.

Win condition:

- bind the archive to the expected shipped executable;
- compare the complete archive directory, not selected filenames only;
- independently extract and decode every ECL, STD, ANM, and `msg*.dat`
  payload;
- compare every ECL subroutine/timeline count and opcode sequence;
- publish exact content-set digests for Stage 3, Stage 4A, Stage 5, and
  Final B; and
- preserve external-tool failures without treating them as missing shipped
  content.

Reject or defer: any archive-directory, decoded-payload, tracked-artifact, or
ECL opcode-sequence mismatch blocks content identity. An external pretty
printer crash is a tool limitation unless the independently decoded bytes
also disagree.

Out of scope: runtime resource selection, event reachability, opcode meaning,
native update order, side effects, RNG, planner coverage, and physical
gameplay.

## Immutable Inputs

Observed shipped inputs:

- `th08.dat`: 46,838,025 bytes, SHA-256
  `9d7edf43b8ddd347cbb641836f6b5050745dd936f688daebbf9382ca557043bb`;
- `th08.exe`: 840,704 bytes, SHA-256
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
  and
- clean `thpatch/thtk` source commit
  `892114a0fcaa0bbdaaecf3cb4ad56f758683fb40`, reporting release 12.

The external tools were built out of tree with CMake Release,
`WITH_LIBPNG_SOURCE=OFF`, `WITH_OPENMP=OFF`, and static libraries. The report
retains each built tool's SHA-256. Build products remain temporary and are
not repository evidence.

The independent repository path is:

1. `scripts/th08_pbgz.py`, derived from shipped archive parser, XOR/shuffle,
   and LZSS routines;
2. `scripts/th08_resource.py`, derived from shipped `decode_edz_resource`;
   and
3. `scripts/th08_ecl.py`, derived from the shipped ECL loader, enemy VM, and
   timeline scheduler.

## Differential Result

Observed:

- `thtk thdat` and `PbgzArchive` agree in archive order on name, declared
  uncompressed size, and stored size for all 317 entries;
- the independent archive parser retains directory offset 46,833,858,
  decoded directory size 9,063, and 1,268 zero padding bytes;
- the declared content scope contains 188 assets:
  24 ECL, 18 STD, 113 ANM, and 33 message resources;
- `thdat` decoded extraction equals
  `decode_resource(PbgzArchive.extract(...))` byte for byte for all 188;
- the 42 pre-existing tracked wrapped artifacts and 42 tracked decoded
  artifacts also match the shipped archive exactly; and
- all 24 ECL files agree on subroutine count, timeline count, and the complete
  38,696-opcode sequence, including retained negative-time timeline terminal
  records.

The complete 188-asset content-set digest is
`ee11d010d74e5e66da5fb0f098406d3dc0b32598e18fe7472d33b8dd4bb9d6de`.

Filename-scoped mandatory-scene sets are:

| Workload | Route index | Assets | Content-set SHA-256 |
| --- | ---: | ---: | --- |
| Stage 3 | 2 | 14 | `4b2c350c00358865787be0c19a2eba4d547b31f041aad5e75c57cad4abe5e60e` |
| Stage 4A | 3 | 12 | `71d40f0041ddf09edd7cf21ae9242bac050ed1f910c9abf56882e22f2f281234` |
| Stage 5 | 5 | 16 | `38bda7bbf9d938427308055975490da01f05c334e5b15e1feb9fb577e9fad43f` |
| Final B / content stage 7 | 7 | 14 | `46072579e3011a0062b52768d98f03b017dccebd02e086c1f1e587df5b8f2da0` |

These sets use explicit stage filename families for normal/spell ECL and STD,
effect/face/stage ANM, and all same-stage messages. They pin candidate content
versions; the names alone do not prove which resource the runtime loaded at a
particular frame.

The compact manifest is
`artifacts/runtime_reports/th08_immutable_content_manifest_20260731.json`,
SHA-256
`3a52b6f485ada63c833f77ae8cd1653f469ae4fadeef3c38336a737c7e753ae1`.
Independent regeneration with the same shipped files, source commit, and
tool binaries is byte-identical.

Focused manifest-helper tests and Ruff pass. Complete Linux discovery passes
1,390 tests in 12.760 seconds. Exact Windows UNC discovery passes 1,390 tests
in 26.724 seconds with the three existing skips.

## External STD Parser Limitation

The release-12 `thstd -d8` diagnostic succeeds for `stage3.std` and
`stage3_s.std`. On the other mandatory files it terminates as follows:

- `stage4a.std` and `stage4a_s.std`: `SIGSEGV`;
- `stage5.std` and `stage5_s.std`: `SIGABRT` after partial output; and
- `stage7.std` and `stage7_s.std`: `SIGABRT`.

This is observed external-tool compatibility evidence, not a shipped-content
mismatch. All eight STD payloads already passed independent archive
extraction and resource decoding, and their exact decoded hashes remain in
the manifest. `thstd` output has no runtime or semantic authority.

## Formal Authority Answers

1. Two content histories are equivalent only when executable, archive, asset
   name, wrapped bytes, decoded bytes, and relevant content-set digest agree.
   No physical histories or controller states are merged.
2. There is no controller/nature recurrence. Every selected archive member is
   enumerated, and no unknown content branch is optimized away.
3. Exact completion answers which immutable bytes belong to this shipped
   archive and filename-scoped workload set. It does not answer whether,
   when, or with what side effects the game executes them.
4. The algorithm is exact for the archive/extraction/ECL-structure
   projection. Any list, payload, tracked-artifact, declaration, or opcode
   mismatch falsifies the gate. The `thstd` failures falsify only complete
   external STD pretty-print compatibility.
5. There is no issue-time consumer, publication path, shared worker, or live
   fallback change.

## Required Next Gate

`CONTENT-02` may now build a symbolic mandatory-stage ECL event atlas. Each
row must retain content-set digest, ECL file, subroutine or timeline,
instruction offset, difficulty/route mask, event class, and unsupported
operand semantics. Native observations may join to that atlas only through
an exact runtime ECL image/PC mapping.

The atlas must keep static reachability, observed native execution, and
runtime side effects separate. `thtk` names do not define native semantics.
