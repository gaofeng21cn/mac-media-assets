# MAC Media Assets

[English](README.en.md) · [中文](README.md)

A reusable medical-education media library for [Med Auto Cast](https://github.com/gaofeng21cn/med-autocast).
It contains paper-theatre visual parts, motion and code components, music, sound effects, and reusable
assemblies. The catalog points to real versioned files in `payloads/`; cloning the repository supports
offline discovery and verification.

## Installation

MAC declares `mac-media-assets` as a required capability Package. OPL Framework installs it through
the existing native Package carrier and exposes discovery and media paths through the installed
descriptor. OPL App uses the same path for first installation and explicit Official Profile restoration.
The library does not store accounts, user projects, or installation state.

For direct offline use:

```bash
git clone https://github.com/gaofeng21cn/mac-media-assets.git
cd mac-media-assets
python3 tools/query_assets.py --help
python3 tools/verify_catalog.py
```

Find the current inventory, examples, and assembly descriptions in the [Chinese guide](README.md),
[asset inventory](docs/asset-inventory.md), and [coverage guide](docs/asset-coverage.md).
Historical workstation paths in provenance records identify the source only. Runtime consumers use
the actual installed library root and relative catalog references.

## License and provenance

Original tool code and documentation are licensed under [Apache-2.0](LICENSE). Media files and
third-party material retain their recorded licenses, attribution, and reuse scope; the code license
does not relicense those files. Read each asset's record before reuse. Source links and license
statements for third-party material, including CC0 recordings, remain with their records.

Private author assets, licensed voice identities, personal branding, and branded episode samples are
outside this public library. Asset records describe visual, motion, listening, and medical review
separately. A file's presence or checksum establishes its identity; creative and medical acceptance
remains specific to the intended use.

## Development

Development checks use Python 3.11, Pillow, and Node.js 24.

```bash
uv run --with Pillow python -m unittest discover -s tests -v
python3 tools/verify_catalog.py
node tools/check_motion_studies.mjs
python3 tools/materialize_package.py --check
```

After changing catalog or payload files, run `python3 tools/materialize_package.py` to refresh the
capability descriptor's content lock, then repeat these checks. The existing Framework
`publish-package.yml` publishes an exact owner version and source commit with a checked OCI
predecessor. This repository does not maintain a parallel publisher or channel pointer.

## Current inventory

The public catalog currently contains **211 asset identities, 225 registered revisions, and 919
payload references**. All 211 identities are available to default discovery. The collection layer
contains 17 assemblies and 14 event kits. Character coverage provides 49 baseline role/pose slots;
registration and required anchor gaps are checked separately from motion, medical, listening, and
current-shot review.

The library includes generic Chinese male and female clinician assets. Private author identities,
licensed voices, personal branding, and branded episode samples remain outside this repository.
On a local author workspace, a generic clinician import receives identity context stating that it is
not the current author presenter; that context does not block production. Static walking poses do not
prove a continuous gait, and an imported asset does not prove medical or publication approval.

Four [complete motion samples](tools/preview-engine/motion.html) now cover a bilateral walk cycle,
sitting down and standing up, daily assistance from approach through release, and food preparation
from three cuts through stirring and serving. Each self-contained package includes editable code,
source media, a full video, and visual review bound to its exact bytes. Character actions use
flipbook paper-theatre poses; daily assistance depicts light support rather than clinical transfer.
See [reuse and review scope](docs/motion-studies.md).

## Documentation

- [Documentation index](docs/README.md)
- [Asset inventory](docs/asset-inventory.md)
- [Coverage and reserves](docs/asset-coverage.md)
- [Governance and review boundaries](docs/governance-and-review.md)
- [First-draft quality baseline](docs/first-draft-quality.md)

## License

Original tool code and documentation are licensed under [Apache-2.0](LICENSE). Media files and
third-party content retain their recorded licenses, attribution, and reuse scope; [NOTICE](NOTICE)
does not relicense them.
