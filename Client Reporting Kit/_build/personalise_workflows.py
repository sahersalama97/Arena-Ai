#!/usr/bin/env python3
"""
Make the n8n workflows yours.

The ten workflow JSONs in `n8n/workflows/` contain the original author's Google
sheet IDs, n8n credential IDs and email addresses -- about 100 values spread
across every file. Editing them by hand is slow and it is easy to miss one,
which produces a workflow that fails quietly at 3am.

Fill in CONFIG below, run this script, and import the files it writes to
`n8n/workflows_READY/`.

    python3 "_build/personalise_workflows.py"

The script refuses to write anything while CONFIG still holds a placeholder, so
you cannot accidentally ship someone else's IDs. It validates every output file
afterwards: JSON parses, node count unchanged, no connection points at a node
that no longer exists.

Run with --check to see what is currently in the files without changing anything.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
SRC = os.path.join(KIT, "n8n", "workflows")
OUT = os.path.join(KIT, "n8n", "workflows_READY")

# ===========================================================================
# FILL THIS IN. Everything between the <<< and >>> markers.
# Leave a value as CHANGE_ME and the script will stop and tell you which ones.
# ===========================================================================
CONFIG = {
    # ---- Google Sheets. Copy the ID out of the URL:                        <<<
    #      https://docs.google.com/spreadsheets/d/<THIS PART>/edit
    "BRAND_REGISTRY_ID":      "CHANGE_ME",   # your Brand Registry sheet
    "RAW_TEMPLATE_ID":        "CHANGE_ME",   # your Raw Data master template
    "REPORT_TEMPLATE_ID":     "CHANGE_ME",   # your Ads Report master template
    "KIT_TEMPLATE_ID":        "CHANGE_ME",   # the uploaded 01_...Dashboard sheet

    # ---- n8n credentials. n8n -> Credentials -> open it -> ID is in the URL
    "CRED_GOOGLE_SHEETS_ID":  "CHANGE_ME",
    "CRED_GOOGLE_SHEETS_NAME":"CHANGE_ME",   # the name you gave it in n8n
    "CRED_GOOGLE_DRIVE_ID":   "CHANGE_ME",
    "CRED_GOOGLE_DRIVE_NAME": "CHANGE_ME",
    "CRED_SMTP_ID":           "CHANGE_ME",
    "CRED_SMTP_NAME":         "CHANGE_ME",
    "CRED_GMAIL_ID":          "CHANGE_ME",
    "CRED_GMAIL_NAME":        "CHANGE_ME",
    "CRED_META_ID":           "CHANGE_ME",   # Meta access-token credential
    "CRED_META_NAME":         "CHANGE_ME",

    # ---- Who gets the alerts and the reports
    "OWNER_EMAIL":            "CHANGE_ME",
}                                                                    # >>>
# ===========================================================================

# What is in the shipped files, mapped to the CONFIG key that replaces it.
REPLACEMENTS = [
    ("1ytFhXwRpANDR5HB1NnKFcmeQspVZ-Ves3h03dsFq4xU", "BRAND_REGISTRY_ID"),
    ("1_FdrtJsPsi8bi2K55P1vUn-Y_bzb5cQGwIkrzdzJ3Fs", "RAW_TEMPLATE_ID"),
    ("1ENZCyFBgTNiPuE7nRz5ofic5pao_zjdhwiFLIEyo5LE", "REPORT_TEMPLATE_ID"),
    ("1LT44dvW6b3iuhvUDA9k_zUuRlz4KUXTqxDXinq4dP9s", "KIT_TEMPLATE_ID"),

    ("SBl4DBB9PIqzy5w0", "CRED_GOOGLE_SHEETS_ID"),
    ("Ai Saher Google Sheets", "CRED_GOOGLE_SHEETS_NAME"),
    ("5KJlnp3mTAKGBAdb", "CRED_GOOGLE_DRIVE_ID"),
    ("Ai Saher Google Drive", "CRED_GOOGLE_DRIVE_NAME"),
    ("cEBcWP6Pk9IcmcvL", "CRED_SMTP_ID"),
    ("Report Email SMTP", "CRED_SMTP_NAME"),
    ("zzQuQyhvHs6xuSu1", "CRED_GMAIL_ID"),
    ("n8n Gmail TikTok Reports", "CRED_GMAIL_NAME"),
    ("qQUVSfCeWtFUWkkM", "CRED_META_ID"),
    ("Meta-Access Tokens", "CRED_META_NAME"),

    # Every alert and report address collapses onto yours. Per-client report
    # addresses are driven by the Report_Email column of your registry, not by
    # these literals, so this does not change who your clients receive.
    ("sahersalama97@gmail.com", "OWNER_EMAIL"),
    ("saherahmed773@gmail.com", "OWNER_EMAIL"),
    ("thebreadbutteragency@gmail.com", "OWNER_EMAIL"),
]

# Deliberately NOT replaced:
#   PASTE_YOUR_EMAIL@example.com  -- a guard. WF4 skips sharing while it is
#                                    present, which is the behaviour you want
#                                    until you put real addresses in the registry.
#   meta.instanceId               -- n8n rewrites this on import.
#   node UUIDs                    -- internal, and must stay unique per node.


def placeholders_left():
    return sorted(k for k, v in CONFIG.items() if v == "CHANGE_ME")


def check_only():
    print("Current contents of the shipped workflows:\n")
    print(f"{'value':<46}{'what it is':<28}{'hits':>6}")
    print("-" * 82)
    for old, key in REPLACEMENTS:
        n = 0
        for f in glob.glob(os.path.join(SRC, "*.json")):
            n += open(f, encoding="utf-8").read().count(old)
        label = {
            "BRAND_REGISTRY_ID": "Brand Registry sheet",
            "RAW_TEMPLATE_ID": "Raw Data master template",
            "REPORT_TEMPLATE_ID": "Ads Report master template",
            "KIT_TEMPLATE_ID": "Kit dashboard template",
            "OWNER_EMAIL": "alert / report address",
        }.get(key, key.replace("CRED_", "").replace("_ID", " credential").replace("_NAME", " credential name"))
        print(f"{old[:44]:<46}{label:<28}{n:>6}")
    print("\nRun without --check after filling in CONFIG to write your copies.")


def validate(path, expected_nodes):
    with open(path, encoding="utf-8") as fh:
        wf = json.load(fh)
    problems = []
    if len(wf["nodes"]) != expected_nodes:
        problems.append(f"node count {len(wf['nodes'])} != expected {expected_nodes}")
    names = {n["name"] for n in wf["nodes"]}
    for src, conns in wf.get("connections", {}).items():
        for outs in conns.values():
            for out in outs:
                for t in out:
                    # Error outputs legitimately point at nodes in the host
                    # workflow (the patch file is the one case where that is so).
                    if t["node"] not in names and not os.path.basename(path).startswith("05b"):
                        problems.append(f"connection to unknown node {t['node']!r}")
    return problems


def main():
    if "--check" in sys.argv:
        check_only()
        return 0

    left = placeholders_left()
    if left:
        print("STOP -- CONFIG still has placeholders. Fill these in first:\n")
        for k in left:
            print(f"    {k}")
        print(f"\n{len(left)} of {len(CONFIG)} values still need filling.")
        print("Nothing was written. Re-run when they are all set.")
        return 1

    files = sorted(glob.glob(os.path.join(SRC, "*.json")))
    if not files:
        print(f"No workflow JSONs found in {SRC}")
        return 1

    # Guard against stale patterns. If a value below matches nothing in the
    # shipped files, the ID has drifted and part of the output would silently
    # keep the original author's value. Stop rather than write that.
    corpus = "".join(open(f, encoding="utf-8").read() for f in files)
    stale = [(old, key) for old, key in REPLACEMENTS if old not in corpus]
    if stale:
        print("STOP -- these patterns match nothing in n8n/workflows/, so they are")
        print("stale. Updating them is required before this script is trustworthy:\n")
        for old, key in stale:
            print(f"    {key:<26} {old}")
        print("\nNothing was written.")
        return 1

    os.makedirs(OUT, exist_ok=True)
    grand = {}
    failed = False
    print(f"Writing personalised workflows to n8n/workflows_READY/\n")
    print(f"{'file':<46}{'nodes':>6}{'replacements':>14}")
    print("-" * 68)

    for f in files:
        text = open(f, encoding="utf-8").read()
        expected = len(json.loads(text)["nodes"])
        count = 0
        for old, key in REPLACEMENTS:
            n = text.count(old)
            if n:
                text = text.replace(old, CONFIG[key])
                count += n
                grand[key] = grand.get(key, 0) + n
        dest = os.path.join(OUT, os.path.basename(f))
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(text)
        problems = validate(dest, expected)
        flag = "" if not problems else "  <-- PROBLEM"
        print(f"{os.path.basename(f):<46}{expected:>6}{count:>14}{flag}")
        for p in problems:
            print(f"      {p}")
            failed = True

    print("-" * 68)
    print(f"{'TOTAL':<46}{'':>6}{sum(grand.values()):>14}")
    print("\nReplaced, by what it was:")
    for old, key in REPLACEMENTS:
        if key in grand:
            print(f"    {grand[key]:>4}x  {key:<26} -> {CONFIG[key]}")

    # Nothing of the original author's should survive.
    print("\nLeftover check:")
    clean = True
    for old, key in REPLACEMENTS:
        if CONFIG[key] == old:
            continue          # you kept the original value, so of course it is there
        n = 0
        for f in glob.glob(os.path.join(OUT, "*.json")):
            n += open(f, encoding="utf-8").read().count(old)
        if n:
            print(f"    {n:>4}x  {old}  STILL PRESENT")
            clean = False
    if clean:
        print("    none -- every original ID, credential and address is gone")

    if failed:
        print("\nSome files have problems. Fix them before importing.")
        return 1
    print(f"\nDone. Import the {len(files)} files in n8n/workflows_READY/ in filename order.")

    # WF3 ships in test mode: every report goes to TEST_RECIPIENT instead of the
    # client address in the registry. Worth shouting about, because turning the
    # schedules on with it still true means no client ever receives a report and
    # nothing errors.
    wf3 = os.path.join(OUT, "06_WF3_Ads_Reports.json")
    if os.path.exists(wf3) and "const TEST_MODE = true" in open(wf3, encoding="utf-8").read():
        print("\n" + "!" * 68)
        print("WF3 (06_WF3_Ads_Reports) has TEST_MODE = true.")
        print("While that is set, EVERY report goes to your address and no client")
        print("receives one. Nothing errors, so it is easy to miss.")
        print("Leave it true while testing. Before you go live, open that Code node")
        print("and change it to:  const TEST_MODE = false;")
        print("!" * 68)

    print("\nThen follow START_HERE.md from step 5.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
