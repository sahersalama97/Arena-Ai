#!/usr/bin/env python3
"""
Generates the two n8n workflows that drive the Client Reporting Kit:

  WF4 Provision Client Reporting Kit      -- run once per brand, creates its dashboard
  WF5 Client Reporting Kit Nightly Refresh -- fills every dashboard from the raw sheets

Node parameter shapes, credentials, error handling and the loop-back wiring are
copied from the workflows already running in this install (WF1u / WF1bu /
WF_Provision), so these import into the same n8n without surprises.

Run:  python3 "_build/build_n8n_workflows.py"
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "n8n")  # Client Reporting Kit/n8n

# ---- IDs from this install ---------------------------------------------------
REGISTRY_ID = "1ytFhXwRpANDR5HB1NnKFcmeQspVZ-Ves3h03dsFq4xU"   # Brand Registry, tab Sheet1
KIT_TEMPLATE_ID = "1LT44dvW6b3iuhvUDA9k_zUuRlz4KUXTqxDXinq4dP9s"  # TEMPLATE - Client Reporting Dashboard
OWNER_EMAIL = "sahersalama97@gmail.com"

SHEETS = {"googleSheetsOAuth2Api": {"id": "SBl4DBB9PIqzy5w0", "name": "Ai Saher Google Sheets"}}
DRIVE = {"googleDriveOAuth2Api": {"id": "5KJlnp3mTAKGBAdb", "name": "Ai Saher Google Drive"}}
SMTP = {"smtp": {"id": "cEBcWP6Pk9IcmcvL", "name": "Report Email SMTP"}}
GMAIL = {"gmailOAuth2": {"id": "zzQuQyhvHs6xuSu1", "name": "n8n Gmail TikTok Reports"}}

RAW_TABS = ["Daily_Raw_Meta", "Daily_Raw_TikTok", "Daily_Raw_Meta_Ads", "Daily_Raw_TikTok_Ads"]

# ---- node helpers ------------------------------------------------------------
def node(name, typ, params, pos, version=None, creds=None, **flags):
    n = {"parameters": params, "type": f"n8n-nodes-base.{typ}",
         "typeVersion": version or DEFAULT_VERSIONS[typ], "name": name, "position": pos}
    if creds:
        n["credentials"] = creds
    n.update(flags)
    return n


DEFAULT_VERSIONS = {
    "manualTrigger": 1, "scheduleTrigger": 1.2, "errorTrigger": 1, "googleSheets": 4.7,
    "googleDrive": 3, "code": 2, "splitInBatches": 3, "if": 2.2, "httpRequest": 4.2,
    "emailSend": 2.1, "gmail": 2.2,
}

# Resilience flags, exactly as the running sync workflows set them.
RETRY = {"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000}
API_FAIL = dict(RETRY, onError="continueErrorOutput", alwaysOutputData=True)
SHEET_FAIL = {"onError": "continueRegularOutput", "alwaysOutputData": True}
# Two-output variant: out0 = success, out1 = error. Needed wherever a failed
# step has to be reported instead of silently continuing.
SHEET_FAIL2 = {"onError": "continueErrorOutput", "alwaysOutputData": True}


def sheets_read(name, doc_id, tab, pos, expr_doc=False):
    return node(name, "googleSheets", {
        "documentId": {"__rl": True, "mode": "id",
                       "value": ("=" + doc_id) if expr_doc else doc_id},
        "sheetName": {"__rl": True, "mode": "name", "value": tab},
        "options": {},
    }, pos, creds=SHEETS, **SHEET_FAIL)


def sheets_clear(name, doc_expr, tab, rng, pos):
    return node(name, "googleSheets", {
        "operation": "clear",
        "documentId": {"__rl": True, "mode": "id", "value": doc_expr},
        "sheetName": {"__rl": True, "mode": "name", "value": tab},
        "clear": "specificRange",
        "range": rng,
    }, pos, creds=SHEETS, **SHEET_FAIL)


def code(name, js, pos):
    return node(name, "code", {"jsCode": js}, pos)


def cond(cid, left, op, right, ctype="number", single=False):
    return {"id": cid, "leftValue": left,
            "operator": {"operation": op, "singleValue": single, "type": ctype},
            "rightValue": right}


def if_node(name, conditions, pos):
    return node(name, "if", {
        "conditions": {"combinator": "and", "conditions": conditions,
                       "options": {"caseSensitive": True, "leftValue": "",
                                   "typeValidation": "strict", "version": 2}},
        "options": {}}, pos)


def email(name, subject, text, pos, html=None):
    p = {"fromEmail": OWNER_EMAIL, "toEmail": OWNER_EMAIL, "subject": subject,
         "options": {"appendAttribution": False}}
    if html is not None:
        p.update({"emailFormat": "html", "html": html})
    else:
        p["text"] = text
    return node(name, "emailSend", p, pos, creds=SMTP, onError="continueRegularOutput",
                alwaysOutputData=True)


def connect(conns, src, *targets):
    """targets is a list of branch-lists; branch 0 = success/true, 1 = error/false."""
    main = []
    for branch in targets:
        main.append([{"node": t, "type": "main", "index": 0} for t in branch])
    conns[src] = {"main": main}


def workflow(name, nodes, conns):
    return {"name": name, "nodes": nodes, "connections": conns, "active": False,
            "settings": {"executionOrder": "v1", "binaryMode": "separate",
                         "availableInMCP": False},
            "pinData": {}, "meta": {"templateCredsSetupCompleted": True}, "tags": []}


def js(filename):
    with open(os.path.join(OUT_DIR, filename)) as f:
        return f.read()


# ============================================================ WF5  NIGHTLY REFRESH
def build_refresh():
    n, c = [], {}
    X = -1900

    n.append(node("Manual Test", "manualTrigger", {}, [X, 320]))
    n.append(node("Daily 14:00", "scheduleTrigger", {
        "rule": {"interval": [{"field": "cronExpression", "expression": "0 14 * * *"}]}},
        [X, 520]))
    n.append(sheets_read("Read Brand Registry", REGISTRY_ID, "Sheet1", [X + 240, 400]))
    n.append(code("Filter brands with a kit", """// A brand is refreshable when it is active, its pipeline has a Raw sheet, and
// WF4 has already given it a dashboard of its own. Anything else is skipped
// silently rather than failing the run -- WF4 will pick it up on its next pass.
return items.filter(i => {
  const j = i.json || {};
  return (j.Status || '').toLowerCase() === 'active' && j.Raw_Sheet_ID && j.Kit_Sheet_ID;
});""", [X + 480, 400]))
    n.append(node("Loop brands", "splitInBatches", {"batchSize": 1, "options": {}}, [X + 720, 400]))

    # one batchGet for all four raw tabs: 1 read per brand instead of 4
    ranges = "&".join(
        "ranges={{ encodeURIComponent(\"'%s'!A:Z\") }}" % t for t in RAW_TABS)
    fetch_url = ("=https://sheets.googleapis.com/v4/spreadsheets/"
                 "{{ $('Loop brands').item.json.Raw_Sheet_ID }}/values:batchGet?"
                 + ranges +
                 "&majorDimension=ROWS&valueRenderOption=UNFORMATTED_VALUE"
                 "&dateTimeRenderOption=SERIAL_NUMBER")
    n.append(node("Fetch raw tabs", "httpRequest", {
        "url": fetch_url, "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googleSheetsOAuth2Api", "options": {}},
        [X + 960, 520], creds=SHEETS, **API_FAIL))

    n.append(code("Flatten to kit shape", js("code_flatten_to_kit_shape.js"), [X + 1200, 520]))

    n.append(if_node("Has rows to write?", [
        cond("rows", "={{ $json.fundRows + $json.adRows }}", "gt", 0)], [X + 1440, 520]))

    kit = "{{ $('Flatten to kit shape').item.json.kitId }}"
    n.append(node("Clear kit data tabs", "httpRequest", {
        "method": "POST",
        "url": "=https://sheets.googleapis.com/v4/spreadsheets/" + kit + "/values:clear",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googleSheetsOAuth2Api",
        "sendBody": True, "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ ranges: $('Flatten to kit shape').item.json.clearRanges }) }}",
        "options": {}}, [X + 1680, 400], creds=SHEETS, **API_FAIL))

    n.append(node("Write kit data", "httpRequest", {
        "method": "POST",
        "url": "=https://sheets.googleapis.com/v4/spreadsheets/" + kit + "/values:batchUpdate",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googleSheetsOAuth2Api",
        "sendBody": True, "specifyBody": "json",
        # RAW, not USER_ENTERED: RAW preserves JSON types, so the date serials
        # land as real dates. USER_ENTERED would parse them fine but would also
        # reinterpret ad names like "50% off" as 0.5.
        "jsonBody": ("={{ JSON.stringify({ valueInputOption: 'RAW', "
                     "data: $('Flatten to kit shape').item.json.data }) }}"),
        "options": {}}, [X + 1920, 400], creds=SHEETS, **API_FAIL))

    n.append(email("Email fetch failure",
                   "=Kit refresh: cannot read raw data - {{ $('Loop brands').item.json.Brand_Name }}",
                   "=The batchGet against the Raw Data sheet did not return the four raw tabs.\n\n"
                   "Brand: {{ $('Loop brands').item.json.Brand_Name }}\n"
                   "Raw_Sheet_ID: {{ $('Loop brands').item.json.Raw_Sheet_ID }}\n"
                   "Kit_Sheet_ID: {{ $('Loop brands').item.json.Kit_Sheet_ID }}\n"
                   "Error: {{ $json.error ? JSON.stringify($json.error) : ($json.message || 'see the n8n execution log') }}\n\n"
                   "Usual causes: the Raw sheet is not shared with the n8n Google account, a raw tab was "
                   "renamed, or the sheet was deleted.", [X + 1440, 760]))

    n.append(email("Email no data",
                   "=Kit refresh: nothing to write - {{ $json.brand }}",
                   "=The raw tabs came back but produced no usable rows.\n\n"
                   "Brand: {{ $json.brand }}\n"
                   "Fundamentals rows: {{ $json.fundRows }}\n"
                   "Ad rows: {{ $json.adRows }}\n"
                   "Days found: {{ $json.daysKept }}\n"
                   "Tabs missing: {{ $json.missingTabs.join(', ') || 'none' }}\n\n"
                   "Nothing was written, so the dashboard still shows the previous refresh. Check whether "
                   "the sync workflows ran for this brand.", [X + 1680, 760]))

    n.append(email("Email write failure",
                   "=Kit refresh: write failed - {{ $('Flatten to kit shape').item.json.brand }}",
                   "=Reading the raw data worked; writing the dashboard did not.\n\n"
                   "Brand: {{ $('Flatten to kit shape').item.json.brand }}\n"
                   "Kit_Sheet_ID: {{ $('Flatten to kit shape').item.json.kitId }}\n"
                   "Error: {{ $json.error ? JSON.stringify($json.error) : ($json.message || 'see the n8n execution log') }}\n\n"
                   "Usual causes: the dashboard tab was renamed (_Control, Fundamentals, Ad Data must keep "
                   "their names), or the kit sheet was deleted or moved to trash.", [X + 2160, 620]))

    n.append(code("Summarise run", js("code_summarise_run.js"), [X + 720, 140]))
    n.append(email("Email run summary", "={{ $json.subject }}", None, [X + 960, 140],
                   html="={{ $json.html }}"))

    n.append(node("Error Trigger", "errorTrigger", {}, [X, 40]))
    n.append(node("Send a message", "gmail", {
        "sendTo": OWNER_EMAIL,
        "subject": "Error in WF5 CLIENT REPORTING KIT REFRESH",
        "message": ("=Workflow: {{ $json.workflow.name }}\n"
                    "Failed node: {{ $json.execution.lastNodeExecuted }}\n"
                    "Error: {{ $json.execution.error.message }}\n"
                    "Execution: {{ $json.execution.url }}"),
        "options": {"appendAttribution": False}}, [X + 240, 40], creds=GMAIL))

    LOOP = ["Loop brands"]
    connect(c, "Manual Test", ["Read Brand Registry"])
    connect(c, "Daily 14:00", ["Read Brand Registry"])
    connect(c, "Read Brand Registry", ["Filter brands with a kit"])
    connect(c, "Filter brands with a kit", ["Loop brands"])
    # splitInBatches: output 0 = done, output 1 = one brand at a time
    connect(c, "Loop brands", ["Summarise run"], ["Fetch raw tabs"])
    connect(c, "Fetch raw tabs", ["Flatten to kit shape"], ["Email fetch failure"])
    connect(c, "Flatten to kit shape", ["Has rows to write?"])
    connect(c, "Has rows to write?", ["Clear kit data tabs"], ["Email no data"])
    connect(c, "Clear kit data tabs", ["Write kit data"], ["Email write failure"])
    connect(c, "Write kit data", LOOP, ["Email write failure"])
    connect(c, "Email fetch failure", LOOP)
    connect(c, "Email no data", LOOP)
    connect(c, "Email write failure", LOOP)
    connect(c, "Summarise run", ["Email run summary"])
    connect(c, "Error Trigger", ["Send a message"])

    return workflow("WF5 Client Reporting Kit Nightly Refresh", n, c)


# ============================================================== WF4  PROVISIONING
def build_provision():
    n, c = [], {}
    X = -1900

    n.append(node("Manual Test", "manualTrigger", {}, [X, 320]))
    n.append(node("Daily 10:30", "scheduleTrigger", {
        "rule": {"interval": [{"field": "cronExpression", "expression": "30 10 * * *"}]}},
        [X, 520]))
    n.append(sheets_read("Read Brand Registry", REGISTRY_ID, "Sheet1", [X + 240, 400]))
    n.append(code("Filter brands needing a kit", """// Only brands that are active, already have a Raw sheet to read from, and do
// not yet have a dashboard. Re-running is therefore safe: it creates the
// missing ones and leaves existing dashboards -- and any edits a human made to
// their Benchmarks or business inputs -- completely alone.
return items.filter(i => {
  const j = i.json || {};
  return (j.Status || '').toLowerCase() === 'active' && j.Raw_Sheet_ID && !j.Kit_Sheet_ID;
});""", [X + 480, 400]))
    n.append(node("Loop brands", "splitInBatches", {"batchSize": 1, "options": {}}, [X + 720, 400]))

    n.append(node("Copy kit template", "googleDrive", {
        "operation": "copy",
        "fileId": {"__rl": True, "mode": "id", "value": KIT_TEMPLATE_ID},
        "name": "={{ $json.Brand_Name }} - Reporting Dashboard (LIVE)",
        "options": {}}, [X + 960, 400], creds=DRIVE, **API_FAIL))

    # Registry schema, mirroring the columns WF_Provision already writes.
    reg_cols = ["Brand_Name", "Platform", "Meta_Ad_Account_ID", "TikTok_Advertiser_ID",
                "Report_Email", "Raw_Sheet_ID", "Current_Month_Report_Sheet_ID",
                "Kit_Sheet_ID", "Status", "Discovered_At"]
    schema = [{"id": k, "displayName": k, "required": False, "defaultMatch": False,
               "display": True, "type": "string", "canBeUsedToMatch": k == "Brand_Name"}
              for k in reg_cols]
    n.append(node("Save Kit_Sheet_ID", "googleSheets", {
        "operation": "update",
        "documentId": {"__rl": True, "mode": "id", "value": REGISTRY_ID},
        "sheetName": {"__rl": True, "mode": "name", "value": "Sheet1"},
        "columns": {"mappingMode": "defineBelow",
                    "value": {"Brand_Name": "={{ $('Loop brands').item.json.Brand_Name }}",
                              "Kit_Sheet_ID": "={{ $json.id }}",
                              "row_number": 0},
                    "matchingColumns": ["Brand_Name"],
                    "schema": schema,
                    "attemptToConvertTypes": False, "convertFieldsToString": False},
        "options": {}}, [X + 1200, 400], creds=SHEETS, **SHEET_FAIL2))

    # Every registry row still holds the placeholder email, so guard the share:
    # sharing to PASTE_YOUR_EMAIL@example.com would fail for all twelve brands
    # and look like the workflow was broken.
    n.append(if_node("Has a real report email?", [
        cond("email", "={{ $('Loop brands').item.json.Report_Email }}",
             "notContains", "PASTE_YOUR_EMAIL", "string")], [X + 1440, 400]))

    n.append(node("Share kit with brand", "googleDrive", {
        "operation": "share",
        "fileId": {"__rl": True, "mode": "id",
                   "value": "={{ $('Copy kit template').item.json.id }}"},
        "permissionsUi": {"permissionsValues": {
            "role": "writer", "type": "user",
            "emailAddress": "={{ $('Loop brands').item.json.Report_Email }}"}},
        "options": {"sendNotificationEmail": True}},
        [X + 1680, 300], creds=DRIVE, **API_FAIL))

    n.append(email("Email copy failure",
                   "=Kit provisioning: copy failed - {{ $('Loop brands').item.json.Brand_Name }}",
                   "=Copying the dashboard template did not work, so no Kit_Sheet_ID was saved.\n\n"
                   "Brand: {{ $('Loop brands').item.json.Brand_Name }}\n"
                   "Template ID: " + KIT_TEMPLATE_ID + "\n"
                   "Error: {{ $json.error ? JSON.stringify($json.error) : ($json.message || 'see the n8n execution log') }}\n\n"
                   "Usual cause: the template was moved, renamed or trashed. The ID above must point at "
                   "'TEMPLATE - Client Reporting Dashboard (Meta + TikTok)'.", [X + 1200, 660]))

    n.append(email("Email registry failure",
                   "=Kit provisioning: registry not updated - {{ $('Loop brands').item.json.Brand_Name }}",
                   "=The dashboard was copied but Kit_Sheet_ID could not be written back to the registry.\n\n"
                   "Brand: {{ $('Loop brands').item.json.Brand_Name }}\n"
                   "New sheet ID: {{ $('Copy kit template').item.json.id }}\n\n"
                   "Paste that ID into the Kit_Sheet_ID column yourself, otherwise this workflow will "
                   "create a second dashboard for the same brand on its next run. The column must exist "
                   "and be spelled exactly Kit_Sheet_ID.", [X + 1440, 660]))

    n.append(node("Error Trigger", "errorTrigger", {}, [X, 40]))
    n.append(node("Send a message", "gmail", {
        "sendTo": OWNER_EMAIL,
        "subject": "Error in WF4 PROVISION CLIENT REPORTING KIT",
        "message": ("=Workflow: {{ $json.workflow.name }}\n"
                    "Failed node: {{ $json.execution.lastNodeExecuted }}\n"
                    "Error: {{ $json.execution.error.message }}\n"
                    "Execution: {{ $json.execution.url }}"),
        "options": {"appendAttribution": False}}, [X + 240, 40], creds=GMAIL))

    LOOP = ["Loop brands"]
    connect(c, "Manual Test", ["Read Brand Registry"])
    connect(c, "Daily 10:30", ["Read Brand Registry"])
    connect(c, "Read Brand Registry", ["Filter brands needing a kit"])
    connect(c, "Filter brands needing a kit", ["Loop brands"])
    connect(c, "Loop brands", [], ["Copy kit template"])
    connect(c, "Copy kit template", ["Save Kit_Sheet_ID"], ["Email copy failure"])
    connect(c, "Save Kit_Sheet_ID", ["Has a real report email?"], ["Email registry failure"])
    connect(c, "Has a real report email?", ["Share kit with brand"], LOOP)
    connect(c, "Share kit with brand", LOOP, LOOP)
    connect(c, "Email copy failure", LOOP)
    connect(c, "Email registry failure", LOOP)
    connect(c, "Error Trigger", ["Send a message"])

    return workflow("WF4 Provision Client Reporting Kit", n, c)


if __name__ == "__main__":
    for wf, fname in ((build_provision(), "WF4 Provision Client Reporting Kit.json"),
                      (build_refresh(), "WF5 Client Reporting Kit Nightly Refresh.json")):
        path = os.path.join(OUT_DIR, fname)
        with open(path, "w") as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)
        print(f"wrote {path}  ({len(wf['nodes'])} nodes, {len(wf['connections'])} wired)")
