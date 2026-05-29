#!/usr/bin/env python3
"""Privacy regression: the MinerU-cloud path must refuse to upload a local PDF
to the public catbox.moe relay unless the caller explicitly consents.

ARFD-364 H1 added a `--allow-public-upload` consent gate to
`skills/ocr-run/scripts/mineru_client.py` so a user's possibly-unpublished
historical scans are never silently exfiltrated to a 24h-public URL. The gate
was previously exercised only indirectly (other tests set
COLLATE_ALLOW_PUBLIC_UPLOAD=1 to keep working), so a future refactor could drop
the refusal with zero test signal. This test pins the refusal directly:

  - MINERU_API_KEY is set (so key resolution succeeds and we reach the gate),
  - --allow-public-upload is NOT passed,
  => mineru_client.py must exit 6 BEFORE any network upload, and say why.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "skills" / "ocr-run" / "scripts" / "mineru_client.py"


def assert_refuses_without_consent() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        pdf = td_path / "private_scan.pdf"
        pdf.write_bytes(b"%PDF-1.4 stub\n")
        out = td_path / "private_scan.ocr"

        env = os.environ.copy()
        # Key present => key resolution succeeds and execution reaches the
        # consent gate rather than failing earlier on a missing key.
        env["MINERU_API_KEY"] = "dummy-key-for-gate-test"
        # Make sure no ambient consent leaks in from the caller's environment.
        env.pop("COLLATE_ALLOW_PUBLIC_UPLOAD", None)

        run = subprocess.run(
            [
                sys.executable,
                str(CLIENT),
                "--pdf",
                str(pdf),
                "--out",
                str(out),
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert run.returncode == 6, (
            "mineru_client.py must refuse (rc=6) to upload a local PDF without "
            f"--allow-public-upload, got rc={run.returncode}\n"
            f"stdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        )
        blob = run.stdout + run.stderr
        assert "allow-public-upload" in blob, (
            "refusal must tell the user how to consent (--allow-public-upload)\n"
            f"stderr:\n{run.stderr}"
        )
        # The refusal is pre-network: no raw.md / meta.json should be produced.
        assert not (out / "raw.md").exists(), "refused run must not write raw.md"


def main() -> int:
    assert_refuses_without_consent()
    print("PASS smoke_public_upload_gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
