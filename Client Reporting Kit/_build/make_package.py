#!/usr/bin/env python3
"""
Build the downloadable ZIP of the whole system.

    python3 "_build/make_package.py"

Writes  Media-Buyers-Client-Reporting-Kit.zip  at the repository root.

The package is the kit exactly as it sits in git, plus the upstream pipeline
folder, minus everything that must not leave this machine:

  excluded                       why
  ----------------------------   --------------------------------------------
  google_drive/                  real client exports (live revenue data)
  __pycache__/, *.pyc            build residue
  n8n/workflows_READY/           generated, holds your private IDs
  _build/build_gofresh_live.py   one-off scaffolding for a single live client:
  _build/build_gofresh_report.py names that client and reads sandbox-only
                                 paths (/tmp, google_drive/) that do not
                                 exist for anyone else
  n8n/WF4 ...json                byte-identical duplicates of the numbered
  n8n/WF5 ...json                copies in n8n/workflows/. One workflow, one
  n8n/WF2e_PATCH_...json         file, one obvious name. See DUPLICATE_PAIRS -
                                 each pair is checksummed before exclusion.

Nothing is deleted from the repository - the exclusions only affect the ZIP.

The ZIP is self-verifying: MANIFEST.md lists every file with its size and
SHA-256, and the script re-opens the finished archive to confirm the count,
that no excluded path leaked in, and that every JSON still parses.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
REPO = os.path.dirname(KIT)

PKG_NAME = "Media-Buyers-Client-Reporting-Kit"
OUT_ZIP = os.path.join(REPO, PKG_NAME + ".zip")

UPSTREAM_DIR = "Automated Ads Reporting System_files"
UPSTREAM_SUB = "Automated Ads Reporting System NEWW (launching)"

EXCLUDE_DIRS = {"__pycache__", "workflows_READY", ".git", "fonts_backup"}
EXCLUDE_FILES = {
    os.path.join("_build", "build_gofresh_live.py"),
    os.path.join("_build", "build_gofresh_report.py"),
}
EXCLUDE_EXT = {".pyc", ".pyo", ".DS_Store"}

# Same workflow under two names. The numbered copy in n8n/workflows/ is the one
# the guide tells you to import, so the loose original is left out of the
# package - a buyer should not have to guess which of two identical files to
# use. Each pair is checksummed at build time: if they ever diverge the build
# fails, because excluding the loose copy would then mean dropping a workflow
# that is no longer a duplicate.
DUPLICATE_PAIRS = [
    (os.path.join("n8n", "WF4 Provision Client Reporting Kit.json"),
     os.path.join("n8n", "workflows", "07_WF4_Provision_Client_Reporting_Kit.json")),
    (os.path.join("n8n", "WF5 Client Reporting Kit Nightly Refresh.json"),
     os.path.join("n8n", "workflows", "08_WF5_Kit_Nightly_Refresh.json")),
    (os.path.join("n8n", "WF2e_PATCH_TikTok_Ads_Upsert.json"),
     os.path.join("n8n", "workflows", "05b_PATCH_for_WF2e_TikTok_Ads.json")),
]
EXCLUDE_FILES |= {loose for loose, _ in DUPLICATE_PAIRS}


def keep(rel):
    """True if this relative path belongs in the package."""
    if any(part in EXCLUDE_DIRS for part in rel.split(os.sep)):
        return False
    if os.path.splitext(rel)[1] in EXCLUDE_EXT:
        return False
    if rel.replace("\\", "/") in {p.replace("\\", "/") for p in EXCLUDE_FILES}:
        return False
    return True


def read_this_first():
    return """# READ THIS FIRST

This ZIP is the complete system: the reporting kit, the n8n automation, and the
upstream data pipeline it reads from.

## Start here

Open **`START_HERE.md`**. It is one guide, ten numbered steps, from an empty
Google Drive to dashboards that fill themselves every night. Every step ends
with a check so you know it worked before you move on.

About 2 hours. If your data pipeline already runs, start at Step 6 - about 30
minutes.

## What is in the box

    START_HERE.md                 the A-to-Z setup guide - read this first
    README.md                     what each kit file is, and when to open it
    README_AR.md                  the same, in Arabic
    SETUP_GUIDE.md                the in-depth reference (Parts A-D)
    FAQ.md                        publish this before you launch
    LICENCE.md                    what buyers may and may not do

    01_..._Dashboard.xlsx         live dashboard, 11 tabs, 757 formulas
    02_Client_Report_Template.xlsx  client-facing report, 11 tabs, 335 formulas
    03_KPI_Calculator.xlsx        breakeven ROAS, contribution margin, POAS
    04_Monthly_Report_PDF_Template.pdf   5-page designed PDF, blank
    05_AI_Prompts_Campaign_Performance.md   12 prompts, English
    05_AI_Prompts_AR.md           the same 12 prompts, Arabic
    samples/Sample_Monthly_Report.pdf   a filled example of 04

    n8n/workflows/                all 10 workflow JSONs, numbered in the
                                  order you import them (00 ... 08).
                                  This is the only place workflows live -
                                  there is exactly one copy of each, so you
                                  never have to guess which file to import
    n8n/code_*.js                 the three Code nodes, standalone for testing
    n8n/AUTOMATION_GUIDE.md       WF4 and WF5 in detail
    n8n/WF2e_FIX_...md            READ FIRST if your TikTok raw sheet has
                                  duplicated or rounded rows

    _build/                       the Python that regenerates every artefact
                                  above, including the fonts (Inter, SIL OFL)

    Automated Ads Reporting       the upstream pipeline the kit reads from:
    System NEWW (launching)/      the 8 original workflow JSONs plus the PDF

## Two things worth knowing before you start

**1. The workflows already point at one person's live Google account.** The
sheet IDs, the five credential IDs and the owner email addresses inside
`n8n/workflows/` are the original author's. Step 5 of the guide replaces all of
them - 17 distinct values, 254 occurrences. Do not skip it. Run
`_build/personalise_workflows.py` if you can run Python; otherwise the guide
carries the complete find-and-replace table inline.

**2. `06` through `09`, `LAUNCH_COPY.md` and `LICENCE.md` are selling
material, not client material.** They contain pricing strategy and the honest
limits of what has been tested. Keep them for yourself. Never put them in a
folder a client can open.

## Honesty note

The five kit components are built, audited and verified: 1,316 live formulas
across three workbooks, 2,069 formulas audited with zero errors, zero clipped
cells, and the Meta and TikTok dashboards fully separated with zero leakage
between them.

The two automation workflows (WF4 and WF5) have had their logic unit-tested
against real data, but **they have never been executed inside n8n**. Run both
end to end on one brand before you sell automation to anyone. Step 8 of the
guide is exactly that test.

`06_WF3_Ads_Reports.json` also ships with `TEST_MODE = true`, so every report
goes to you and no client receives one. That is deliberate - it fails safe.
Step 9 turns it off.

## Verifying your download

`MANIFEST.md` lists every file in this package with its size and SHA-256.
Unzip, then run this from inside the folder it creates - the paths in the
manifest are relative to the package root, which is where you will be standing:

    cd Media-Buyers-Client-Reporting-Kit
    sha256sum -c MANIFEST.sha256

Every line should say `OK`. The two manifest files are not listed in
themselves, because a file cannot contain its own hash.

This archive is a deterministic build: entry timestamps are fixed, so
rebuilding from the same files produces a bit-identical ZIP and the same
SHA-256. If someone sends you a copy, the hashes should match exactly. To
rebuild it yourself from the git repository:

    python3 "Client Reporting Kit/_build/make_package.py"

## Not in this package

**No client data.** The build exports one live account's sheets to
`google_drive/` for testing; that directory is excluded, along with two one-off
build scripts that read it. No revenue figure, no raw export, no sheet ID
belonging to a client is in this ZIP.

**One name does appear, in three author-owned files.** `06`, `LAUNCH_COPY.md`
and `_build/build_wf2e_patch.py` name the account the demo story and the
integrity checks were measured against. That is deliberate provenance, not a
leak - and `00_READ_THIS_FIRST.md` is generated fresh each build, so if you
hand this ZIP to anyone outside your own team, decide first whether you want
that name in it. The packager reports those files every time it runs.

No buyer-facing file - not the README, not `START_HERE.md`, not the setup
guide, not any workflow JSON, not any template - contains a client name. The
packager fails the build if one ever does.
"""


def _client_name_scan(zip_path, pkg_name):
    """Check no live client name reaches a buyer-facing file.

    Two tiers, because the rule is not the same everywhere:

      buyer-facing  README, START_HERE, SETUP_GUIDE, FAQ, the numbered
                    artefacts, samples/, everything under n8n/, and the
                    upstream pipeline. These ship to whoever buys the kit.
                    A client name here is a HARD FAILURE.

      author-owned  06-09, LAUNCH_COPY, LICENCE and _build/*.py. These are
                    the author's own selling material and build scaffolding;
                    the demo narrative and the provenance comments name the
                    account they were measured against on purpose. A hit here
                    is a warning only.

    This script itself is skipped: its exclusion list has to spell out the
    filenames it refuses to package, so it can never pass its own scan.
    """
    author_owned = ("06_", "07_", "08_", "09_", "LAUNCH_COPY", "LICENCE")
    needles = ("gofresh",)
    hard, warn = [], []

    with zipfile.ZipFile(zip_path) as z:
        for n in z.namelist():
            if not n.endswith((".md", ".json", ".js", ".py")):
                continue
            rel = n.split("/", 1)[1] if n.startswith(pkg_name + "/") else n
            base = os.path.basename(rel)
            if base == "make_package.py":
                continue
            text = z.read(n).decode("utf-8", "ignore").lower()
            if not any(k in text for k in needles):
                continue
            is_author = (rel.startswith("_build/") or
                         base.startswith(author_owned))
            (warn if is_author else hard).append(rel)

    if hard:
        return hard, warn
    return None, warn


def main():
    if not os.path.isdir(KIT):
        sys.exit("cannot find the kit directory at " + KIT)

    upstream = os.path.join(REPO, UPSTREAM_DIR, UPSTREAM_SUB)
    if not os.path.isdir(upstream):
        sys.exit("cannot find the upstream pipeline at " + upstream)

    # A loose workflow is only safe to leave out while it is still a duplicate.
    for loose, numbered in DUPLICATE_PAIRS:
        a, b = os.path.join(KIT, loose), os.path.join(KIT, numbered)
        for p in (a, b):
            if not os.path.isfile(p):
                sys.exit(f"expected {os.path.relpath(p, REPO)} but it is missing - "
                         "update DUPLICATE_PAIRS in make_package.py")
        ha = hashlib.sha256(open(a, "rb").read()).hexdigest()
        hb = hashlib.sha256(open(b, "rb").read()).hexdigest()
        if ha != hb:
            sys.exit(f"refusing to build: {os.path.basename(loose)} no longer matches "
                     f"{os.path.basename(numbered)}, so excluding it would drop a "
                     f"workflow. Reconcile the two files, or remove the pair from "
                     f"DUPLICATE_PAIRS.")

    stage = tempfile.mkdtemp(prefix="pkg_")
    root = os.path.join(stage, PKG_NAME)
    os.makedirs(root)

    copied = []

    # --- the kit -------------------------------------------------------
    for dirpath, dirnames, filenames in os.walk(KIT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in sorted(filenames):
            src = os.path.join(dirpath, fn)
            rel = os.path.relpath(src, KIT)
            if not keep(rel):
                continue
            dst = os.path.join(root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied.append((rel, dst))

    # --- the upstream pipeline -----------------------------------------
    up_rel = UPSTREAM_SUB
    for fn in sorted(os.listdir(upstream)):
        src = os.path.join(upstream, fn)
        if not os.path.isfile(src):
            continue
        rel = os.path.join(up_rel, fn)
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied.append((rel, dst))

    # --- cover note ----------------------------------------------------
    rtf = os.path.join(root, "00_READ_THIS_FIRST.md")
    with open(rtf, "w", encoding="utf-8") as fh:
        fh.write(read_this_first())
    copied.append(("00_READ_THIS_FIRST.md", rtf))

    # --- manifest ------------------------------------------------------
    rows = []
    for rel, path in sorted(copied):
        data = open(path, "rb").read()
        rows.append((rel.replace(os.sep, "/"), len(data),
                     hashlib.sha256(data).hexdigest()))

    man = ["# MANIFEST", "",
           f"{len(rows)} files. Every checksum is SHA-256.", "",
           "| File | Bytes | SHA-256 |", "|---|---|---|"]
    for rel, size, digest in rows:
        man.append(f"| `{rel}` | {size:,} | `{digest[:16]}...` |")
    with open(os.path.join(root, "MANIFEST.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(man) + "\n")

    # Paths are relative to the package root, not to its parent: the manifest
    # sits inside the extracted folder, and that is where anyone following the
    # cover note will be standing when they run sha256sum -c.
    with open(os.path.join(root, "MANIFEST.sha256"), "w", encoding="utf-8") as fh:
        for rel, size, digest in rows:
            fh.write(f"{digest}  {rel.replace(os.sep, '/')}\n")

    # --- zip -----------------------------------------------------------
    # Deterministic build. A plain z.write() stamps each entry with the file's
    # mtime, and git resets mtimes to checkout time - so two rebuilds of
    # identical content produce different archives and different SHA-256s, and
    # "verify your download against this hash" becomes meaningless. Fixing the
    # timestamps makes the whole archive reproducible bit for bit. Honours
    # SOURCE_DATE_EPOCH, the usual convention for this.
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    stamp = time.gmtime(int(epoch))[:6] if epoch else (2026, 1, 1, 0, 0, 0)

    if os.path.exists(OUT_ZIP):
        os.remove(OUT_ZIP)
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                arc = os.path.relpath(full, stage).replace(os.sep, "/")
                zi = zipfile.ZipInfo(arc, date_time=stamp)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                with open(full, "rb") as fh:
                    z.writestr(zi, fh.read())

    # --- verify --------------------------------------------------------
    problems = []
    with zipfile.ZipFile(OUT_ZIP) as z:
        bad = z.testzip()
        if bad:
            problems.append("corrupt member: " + bad)
        names = z.namelist()
        forbidden = ["google_drive/", "__pycache__/", "workflows_READY/",
                     "build_gofresh_live.py", "build_gofresh_report.py"]
        forbidden += [os.path.basename(loose) for loose, _ in DUPLICATE_PAIRS]
        for bad_path in forbidden:
            if any(bad_path in n for n in names):
                problems.append("excluded path leaked into the ZIP: " + bad_path)
        wf = [n for n in names if "/n8n/workflows/" in n and n.endswith(".json")]
        if len(wf) != 10:
            problems.append(f"expected 10 workflow JSONs, found {len(wf)}")
        for n in wf:
            try:
                json.loads(z.read(n))
            except Exception as exc:
                problems.append(f"{os.path.basename(n)} does not parse: {exc}")
        for need in ("00_READ_THIS_FIRST.md", "MANIFEST.md", "MANIFEST.sha256",
                     "START_HERE.md"):
            if not any(n.endswith("/" + need) for n in names):
                problems.append("missing " + need)
    hard, warns = _client_name_scan(OUT_ZIP, PKG_NAME)
    if hard:
        problems.append("client name in buyer-facing files: " + ", ".join(hard))

    shutil.rmtree(stage, ignore_errors=True)

    size = os.path.getsize(OUT_ZIP)
    print(f"\nwrote {os.path.relpath(OUT_ZIP, REPO)}")
    print(f"  {size:,} bytes ({size/1024/1024:.2f} MB)")
    print(f"  {len(rows)} files with checksums in MANIFEST.md")
    print(f"  {len(rows)+2} files in the archive (the two manifest files are")
    print("    not self-listed - a file cannot contain its own hash)")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("  verified: archive intact, 10 workflows parse, no excluded path,")
    print("            no client name in any buyer-facing file, cover note +")
    print("            manifest present")
    if warns:
        print(f"\n  note: {len(warns)} author-owned file(s) still name the demo")
        print("        account, by design (your selling material and build")
        print("        scaffolding, not anything a client sees):")
        for w in warns:
            print("          - " + w)


if __name__ == "__main__":
    main()
