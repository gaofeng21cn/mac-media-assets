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

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_catalog.py
python3 tools/materialize_package.py --check
```

After changing catalog or payload files, run `python3 tools/materialize_package.py` to refresh the
capability descriptor's content lock, then repeat these checks. The existing Framework
`publish-package.yml` publishes an exact owner version and source commit with a checked OCI
predecessor. This repository does not maintain a parallel publisher or channel pointer.
