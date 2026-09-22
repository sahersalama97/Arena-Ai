# Connecting Google Drive (OAuth2) to self-hosted n8n

Target: n8n self-hosted (Docker or npm), `http://localhost:5678` or your own domain.
Managed OAuth2 ("Sign in with Google" with no console setup) is **n8n Cloud only** — self-hosted must use Custom OAuth2.

---

## Step 0 — Know your callback URL before you start

Google rejects the flow unless the redirect URI matches **character for character**. n8n builds it from the URL your browser used, so decide now how you open n8n:

| You open n8n at | Authorized redirect URI to register in Google |
|---|---|
| `http://localhost:5678` | `http://localhost:5678/rest/oauth2-credential/callback` |
| `http://127.0.0.1:5678` | `http://127.0.0.1:5678/rest/oauth2-credential/callback` |
| `http://192.168.1.20:5678` | `http://192.168.1.20:5678/rest/oauth2-credential/callback` |
| `https://n8n.yourdomain.com` | `https://n8n.yourdomain.com/rest/oauth2-credential/callback` |

`localhost` is allowed by Google for development — no domain, SSL cert, or port forwarding needed.
**Always copy the URL from the n8n credential panel** (labelled **OAuth Redirect URL** on recent versions, **OAuth callback URL** on older ones) rather than typing it.

If behind a reverse proxy and n8n shows `http://` where you use `https://`, see “Proxy” below.

---

## Step 1 — Project + enable the APIs

1. https://console.cloud.google.com/projectcreate → name it e.g. `n8n-automation` → **Create**. Select it in the top project picker.
2. Enable **both** APIs (Drive is required even for Sheets/Docs/Slides):
   - https://console.cloud.google.com/apis/api/drive.googleapis.com → **Enable**
   - https://console.cloud.google.com/apis/api/sheets.googleapis.com → **Enable** (only if Sheets nodes are in the same project)
3. No billing account needed for OAuth.

> Reuse the project that already backs your working **Google Sheets** credential. One Google OAuth client can serve every Google node.

## Step 2 — Google Auth Platform (the renamed "OAuth consent screen")

This lives at https://console.cloud.google.com/auth/overview now — the old *APIs & Services → OAuth consent screen* link redirects here. A fresh project shows “Google Auth Platform not configured yet” → **Get started**.

1. **App Information** — App name (`n8n-automation`), User support email → **Next**.
2. **Audience / User type** — pick one:
   - **External** — any Google account; starts in **Testing** mode. Pick this for a personal Gmail.
   - **Internal** — only accounts inside your Google Workspace org. **No 7-day expiry, no verification.** Pick this if your ads/agency account is a Workspace account and you don't mind it being org-only.
3. **Contact Information** — email → **Create**.
4. **Branding → Authorized domains** → add your n8n host (`localhost` is fine for dev; add `n8n.yourdomain.com` in production) → **Save**.
5. **Audience → Test users** → add the exact Gmail address you will sign in with. Anything else gets `Error 403: access_denied`.
6. **Data access → Add or remove scopes** → add these (they're what n8n's Google Drive node requests — read off n8n's own source, `GoogleDriveOAuth2Api.credentials.ts`):

```
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/drive.appdata
https://www.googleapis.com/auth/drive.photos.readonly
```

   Least-privilege alternative for “n8n only touches files it creates” (uploading a report, writing a sheet):

```
https://www.googleapis.com/auth/drive.file
```

   Read-only reporting/folder-listing without write: `https://www.googleapis.com/auth/drive.readonly`.
   `drive` / `drive.readonly` / `drive` full access are **sensitive/restricted** scopes → Google verification is required to publish. `drive.file` and `drive.appdata` are lighter. For personal self-use the unverified warning is harmless (see Step 4).

7. If your project also runs Sheets nodes, keep the Sheets scopes present:

```
https://www.googleapis.com/auth/spreadsheets
https://www.googleapis.com/auth/drive.file
https://www.googleapis.com/auth/drive.metadata
```

## Step 3 — Create the OAuth client

1. https://console.cloud.google.com/auth/clients → **Create clients** (or *APIs & Services → Credentials → + Create credentials → OAuth client ID*).
2. **Application type: Web application** (not “Desktop app”, not “TV/Limited input”).
3. Name: `n8n-web`.
4. **Authorized redirect URIs → Add URI** → paste the URL from Step 0. Exact string, right protocol, right port, no trailing `/`.
5. **Create** → copy **Client ID** and **Client Secret** immediately.

> ⚠️ Google now masks the secret in the console shortly after creation — you cannot re-read it later. Paste both into n8n, or hit **Download JSON**, before closing that dialog. A lost secret = “Add client secret” → new secret → update n8n.
> “Authorized JavaScript origins” can stay empty — that's for browser-only SPAs, not n8n.

## Step 4 — Finish in n8n

1. n8n → **Credentials → Add credential → Google Drive OAuth2 API** (search “Drive”).
   Picking the *Drive* credential type is what gives you a Drive-capable token; your existing **Google Sheets account** credential is a different type and won't be selectable in a Drive node — even though both can share the same Client ID/Secret.
2. Paste **Client ID** + **Client Secret**.
3. Leave **Custom Scopes** off to take n8n's defaults, or turn it on and put exactly one line in **Enabled Scopes**:
   `https://www.googleapis.com/auth/drive.file`
4. **Sign in with Google** → pick the account registered as a test user in Step 2.5.
5. Google shows **“Google hasn’t verified this app”** for unverified external apps. That is expected: **Details → Go to … (unsafe)**. It is not a security hole in your setup — it just means you skipped Google's paid review, which is meaningless for an app only you use.
6. n8n returns to the credential modal, shows “Connected”. **Save**. Name it `Google Drive account`.
7. Test: add a **Google Drive** node → *Operations → Search/List files* → execute → real files come back.

n8n already sets `access_type=offline&prompt=consent` for Google, so a refresh token is always issued — you don't need to configure that.

---

## Step 5 — Stop the 7-day expiry

**External + Testing** = consent and refresh tokens die after **7 days**. Your workflows will silently start failing every Monday-ish with `invalid_grant`. Options:

| fix | do this |
|---|---|
| **Publish the app** (best if you only use non-sensitive scopes like `drive.file`) | **Auth Platform → Audience → Publish app**. No review needed for non-sensitive scopes; sensitive ones need verification. |
| **Workspace org** | recreate the brand as **Internal** — no expiry, no verification, org-only |
| **Stay in Testing** | re-authorize the credential every ≤7 days (unsuitable for a scheduled report) |

---

## Self-host specifics that break this flow

**Reverse proxy showing the wrong callback URL.** n8n derives the redirect from the incoming request, so a proxy that doesn't forward scheme/host produces a mismatch. Add to the container/service and restart:

```
N8N_HOST=n8n.yourdomain.com
N8N_PROTOCOL=https
WEBHOOK_URL=https://n8n.yourdomain.com/
N8N_EDITOR_BASE_URL=https://n8n.yourdomain.com/
N8N_PROXY_HOPS=1
```

Docker compose:

```yaml
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    environment:
      N8N_HOST: n8n.yourdomain.com
      N8N_PROTOCOL: https
      WEBHOOK_URL: https://n8n.yourdomain.com/
      N8N_PROXY_HOPS: 1
      N8N_ENCRYPTION_KEY: <keep-this-stable-and-backed-up>
    volumes:
      - n8n_data:/home/node/.n8n
```

- **`N8N_ENCRYPTION_KEY`**: all stored credentials are encrypted with it. If it isn't pinned (a fresh key per container recreation), your Google credential silently dies after every deploy/recreate. Set it once, back it up.
- **Egress**: the container must reach `oauth2.googleapis.com` and `www.googleapis.com`. Verify from inside:
  ```bash
  docker exec -it n8n wget -qO- https://oauth2.googleapis.com/.well-known/openid-configuration >/dev/null && echo "google reachable"
  ```
- **Clock skew**: token endpoints reject signatures on a host whose clock drifts more than a minute. Check `timedatectl` / NTP on the host.

---

## Reuse one Google app for everything

One OAuth client (ID + secret) can back Sheets, Drive, Gmail, Calendar credentials — just register **one** redirect URI and list **all** scopes the union of those nodes needs in Data access. Each n8n credential then only differs in *type*, which decides the default scope set it requests.

Practical note for your reports workflow: the Sheets scopes already include `drive.file`, so anything you do to the report spreadsheet needs no Drive credential. You need Drive only for things the Sheets node can't do: moving/copying/renaming the file, listing a folder of CSVs to feed the workflow, setting sharing permissions, uploading a generated PDF/CSV alongside it, or a Drive *trigger* on a folder.

## Error table

| error | cause | fix |
|---|---|---|
| `redirect_uri_mismatch` | URI in Google ≠ URI n8n sent | re-copy from n8n into Google; check `http` vs `https`, port, trailing `/`; proxy env vars above |
| `Error 403: access_denied` / “app not verified” | app in Testing and this Google address isn't a test user | Audience → Test users → add it; or Publish app |
| `invalid_grant` days after it worked | External+Testing 7-day expiry (or user revoked, or 6-month idle) | Publish app / reconnect the credential |
| `invalid_client` | wrong ID or secret, trailing space | re-paste both from the console |
| 403 on a Drive call, token itself fine | scope not granted / not in Data access | add scope in Auth Platform → Data access, then **re-run “Sign in with Google”** (existing tokens keep old scopes) |
| `ACCESS_TOKEN_SCOPE_INSUFFICIENT` | granular consent skipped that permission | re-authorize and tick the permission |
| Credential gone after redeploy | `N8N_ENCRYPTION_KEY` not pinned | set it in the environment and restore |
| Works in Chrome, fails in another browser | same host but different URL (e.g. `127.0.0.1` vs `localhost`) | register both URIs, or always use one |

Changing a scope in the Google console does **not** apply to an already-issued token. After any scope edit: n8n credential → **Sign in with Google** again.
