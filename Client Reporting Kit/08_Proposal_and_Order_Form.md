# Proposal & Order Form — Done-For-You Install

For Tier 3 and agency-licence sales. Fill the `[bracketed]` fields, delete the sections
that don't apply, export to PDF, send it. Do not send a blank template — at this price the
buyer expects it to be about them.

**Keep it to three pages.** If it runs longer you are writing a contract nobody reads;
move detail to an appendix.

---

**Prepared for:** [buyer / agency name]
**Prepared by:** [your name, business, email, country]
**Date:** [date] · **Valid until:** [date + 21 days]
**Reference:** [e.g. RF-2026-014]

---

## 1. What you told me

Two or three sentences in their own words. This section is why they sign.

> *[e.g. "You manage Meta and TikTok for eleven e-commerce clients. Reporting is built by
> hand each month in a spreadsheet per client, it takes the best part of two days, and you
> have twice been asked a margin question you couldn't answer because the report shows ROAS
> and not breakeven ROAS. You run n8n for data collection but nobody on the team wants to
> own the reporting automation."]*

## 2. What I'll deliver

| # | Deliverable | Detail |
|---|---|---|
| 1 | The Reporting Kit, installed | Five components: dashboard (11 tabs), client report (11 tabs), KPI calculator (6 tabs), monthly PDF template (5 pages), twelve AI prompts |
| 2 | Automation installed in your n8n | WF4 (provisions one dashboard per client) and WF5 (nightly refresh, 3 Sheets API calls per brand). Credentials created by you; I never hold them |
| 3 | Registry configured | `Kit_Sheet_ID` column added, your brands mapped, `Status` gating verified |
| 4 | Two clients onboarded end to end | From registry row to a filled, client-ready dashboard each |
| 5 | First nightly cycle run together | On a call, watching the execution log. I do not hand over an automation neither of us has seen run |
| 6 | Benchmarks tuned | `PLACEHOLDER` thresholds replaced with [client]'s real trailing data, per platform |
| 7 | Data-integrity review | Health Check reconciling ad-level against account-level totals for both platforms, with anything it flags explained in writing |
| 8 | WF2e patch (if you import TikTok by email) | Fixes duplicated ad-days and 16-digit Ad_ID rounding. Diagnosis + tested nodes + cleanup procedure |
| 9 | 60 days support | Email plus [2] calls. Covers your team, not your clients |
| 10 | Team walkthrough | [90] minutes, recorded, yours to keep |

## 3. Timeline

| | | |
|---|---|---|
| Kickoff call — access, cost inputs, brand list | 60 min | Day [1] |
| Install in your n8n + registry configured | — | Day [2–4] |
| Two clients onboarded, first cycle run together | 60 min call | Day [5–7] |
| Benchmarks tuned + integrity review delivered | — | Day [8–10] |
| Team walkthrough + handover | [90] min | Day [11–14] |

**Total: ~two weeks** from kickoff, assuming access arrives on day one. Support runs 60
days from handover.

## 4. What I need from you

Nothing starts until these arrive. Send this list with the proposal — it also pre-qualifies
the buyer.

1. **n8n access.** Admin invite to your instance, or a self-hosted instance I can reach.
   I'll tell you which credentials to create; you create them.
2. **Google account** for the Sheets + Drive OAuth credentials. Ideally a dedicated
   service account, not a personal one.
3. **Meta:** ad account IDs per brand, and system-user access token with `ads_read`.
4. **TikTok:** advertiser IDs per brand. If you import by scheduled email report, the
   mailbox and how the reports are configured (**CSV attachment preferred** — XLSX exports
   destroy 16-digit ad IDs before n8n ever sees them).
5. **Per brand, per platform:** [client]'s COGS %, other variable costs %, and average
   shipping cost per order in [currency]. Without these breakeven ROAS is a guess and I
   will label it as one in the sheet.
6. **Trailing 90 days of results** if you have them, for benchmark tuning.
7. **A named contact** who can answer a data question same-day for the first two weeks.

The intake form in `09_Delivery_Runbook.md` collects 3–6 in one pass. Send that instead of
this list if you prefer.

## 5. What's excluded

Say this out loud in the proposal. It prevents most scope creep.

- Ad account management, media strategy, creative production
- Building the upstream data-collection pipeline if you don't already have one — this
  installs on top of a pipeline that writes the four raw tabs. If you don't have one, that's
  a separate project and I'll scope it
- Onboarding clients beyond the two included (additional: [$250] each)
- Custom report tabs or metrics beyond the kit's schema (quoted separately)
- Ongoing monthly reporting to *your* clients — that's your service, this is your tool
- Anything requiring data I can't see, e.g. server-side or offline conversion setup

## 6. Known limitations, disclosed before you sign

I would rather lose the sale than have you discover these in month two.

- **The n8n workflows are logic-tested, not long-run.** The ingest node has been executed
  against real client data and matched a delivered workbook row for row; the scheduled
  end-to-end cycle is run with you in deliverable 5. If it fails there, I fix it before
  handover — that's what deliverable 5 is for.
- **TikTok's ad-level export under-reports spend** against its own account-level total (17.6%
  on the reference account). This is platform-side and not fixable by me. The kit's rule is
  to quote TikTok totals from account-level data and use ad-level only for ranking. Health
  Check surfaces the gap rather than hiding it.
- **Benchmarks ship as placeholders.** They're labelled as such in-sheet. Tuning them is
  deliverable 6, but they need your trailing data to be meaningful.
- **Initiate Checkout can exceed Add to Cart.** On the reference account it ran at 199%.
  That's a tracking or business-model question (buy-now flows skipping the cart, or a
  mis-mapped event), not a formula error. I'll flag it, not patch around it.
- **Google Sheets only.** The manual path uses `IMPORTRANGE`, which does not exist in Excel.
- **Currency defaults to EGP.** One cell changes it; if you bill in something else we do it
  at install.

## 7. Investment

| | |
|---|---|
| Install and onboarding (one-time) | **[$1,500]** |
| Support and updates | **[$79]/month**, first month included |
| Agency licence — white-label, unlimited clients, up to [5] internal seats | **[+$1,200]** one-time |
| Additional client onboarding | [$250] each |
| **Total due at signature** | **[$1,500]** |
| **Recurring from month 2** | **[$79]/month** |

Prices in **USD**. [Regional pricing available on request.] VAT/sales tax [handled at
checkout / not applicable / added at invoicing].

**Payment:** [50%] at signature, [50%] at handover. Or 100% at signature for a [5]%
discount. [Bank transfer / Stripe / Wise]. Work starts on cleared funds.

**The monthly is cancellable with 30 days' notice.** Say so — it removes the main objection
to recurring, and it costs you nothing because the product doesn't degrade on cancellation.

## 8. Data protection

Non-negotiable, and it's the reason agencies sign rather than shop around.

- I access **only** what's listed in §4, **only** for the duration in §3.
- You create every credential. I never receive, store or copy a password, token or API key.
- Client ad data stays in your Google account. I do not export it to my own storage, and I
  do not train anything on it.
- On handover you revoke my access. I'll confirm in writing that no copy is retained.
- I may use **aggregate, non-identifiable** findings (e.g. "a TikTok ad-level export ran
  17.6% short") in my marketing. Never a client name, never a brand, never an absolute
  revenue figure. If you want even that excluded, say so and I'll strike it.
- If you need a formal DPA or NDA, I'll sign yours.

## 9. Warranty and acceptance

- **14 days from handover:** if any deliverable in §2 does not work as described, I fix it
  at no cost.
- **Acceptance** is you confirming, in writing, that both onboarded clients produce a
  correct dashboard on a scheduled nightly run. That's a concrete test, not a vibe.
- After acceptance, §9's 60-day support covers breakage from my work. It does not cover
  breakage from your edits, Google or platform API changes, or new brands you add yourself
  (though I'll always tell you what I'd do).
- **Refunds:** full refund before kickoff. After kickoff, refund pro-rata against
  undelivered items in §2. I don't do partial refunds on delivered work — you keep the files.

## 10. Next step

> Reply to this email with **"go"** and I'll send the intake form and two kickoff slots.
> Nothing is due until the intake form comes back and we've both confirmed the date.

**[Your name]** · [email] · [phone/WhatsApp] · [calendar link] · [portfolio/demo link]

---

### Signature

| | |
|---|---|
| For [buyer] | Name, title, signature, date |
| For [you] | Name, signature, date |

*A signed copy or a reply of "agreed" to this email both count. Don't let paperwork delay a
start.*
