#!/usr/bin/env python
"""Compile django.po → django.mo using Babel (no system gettext required)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        from babel.messages.mofile import write_mo
        from babel.messages.pofile import read_po
    except ImportError:
        print("Install Babel: pip install Babel", file=sys.stderr)
        return 1

    for po_path in ROOT.glob("locale/*/LC_MESSAGES/django.po"):
        catalog = read_po(open(po_path, "rb"))
        buf = io.BytesIO()
        write_mo(buf, catalog)
        mo_path = po_path.with_suffix(".mo")
        mo_path.write_bytes(buf.getvalue())
        print(f"Wrote {mo_path.relative_to(ROOT)} ({buf.tell()} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
