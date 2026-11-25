#!/usr/bin/env python3
"""Register the fitted-cuff candidate through the current monitoring packager."""
import sys as _sys
from pathlib import Path as _Path
_TOOLS_DIR = str(_Path(__file__).resolve().parents[2] / 'tools')
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
import argparse
from pathlib import Path
from register_monitoring_repairs import register
ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'work/action-contact-repair-20261024/mac_bp_cuff_action_v1'


def freeze(folder=STAGE, root=ROOT):
    return register('mac_bp_cuff_action_v1', folder, root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze'])
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--stage', default=str(STAGE))
    args = parser.parse_args()
    freeze(args.stage, args.root)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
