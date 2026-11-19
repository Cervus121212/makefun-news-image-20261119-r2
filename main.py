#!/usr/bin/env python3
"""Entry point for the makefun harness.

Copies the pre-rendered front page to the harness output directory.
The page itself is produced by generate.py (run it first to rebuild
entry.png); this file only moves the bytes, so the submitted image is
exactly the one that was reviewed.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not outdir:
        print("MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1
    src = os.path.join(HERE, "entry.png")
    if not os.path.exists(src):
        print("entry.png missing: run python3 generate.py first",
              file=sys.stderr)
        return 1
    os.makedirs(outdir, exist_ok=True)
    shutil.copyfile(src, os.path.join(outdir, "entry.png"))
    print("wrote %s" % os.path.join(outdir, "entry.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
