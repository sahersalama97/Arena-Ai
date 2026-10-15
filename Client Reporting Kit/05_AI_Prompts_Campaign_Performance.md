# AI Prompts — Explaining Campaign Performance

Twelve prompts for turning ad platform data into language a client will read, understand and act on.

**Read this first.** These prompts do not make the analysis for you — they make the *writing* faster. You still need to know your numbers and what you did this month. An AI handed a table of metrics will confidently invent a reason for every movement. These prompts are built to stop that: they include explicit grounding rules, a ban on explaining causes that aren't in the data, and a required "what I can't tell from this data" line.

Two ground rules that apply to every prompt in this file:

1. **Never paste client-identifying or commercially sensitive data into a consumer AI tool** unless you have checked your tool's data policy and your client agreement. If in doubt, replace the brand name with "[the client]" and strip absolute revenue figures down to ratios.
2. **Every number an AI writes must exist in the data you gave it.** Verify before sending. If a prompt's output contains a figure you didn't supply, delete it.

---

## Contents

| # | Prompt | Use it when |
|---|--------|-------------|
| 1 | [The monthly narrative](#1-the-monthly-narrative) | End of month, before you write the report |
| 2 | [The "why did ROAS move" analysis](#2-the-why-did-roas-move-analysis) | ROAS moved and the client will ask why |
| 3 | [The weekly check-in](#3-the-weekly-check-in) | Every Monday, three sentences |
| 4 | [Explain a metric to a non-marketer](#4-explain-a-metric-to-a-non-marketer) | Client asks "what does CPM actually mean?" |
| 5 | [The bad month](#5-the-bad-month) | Performance dropped. Write it before they ask |
| 6 | [Creative learnings](#6-creative-learnings) | You have ad-level data and a story to tell |
| 7 | [The budget recommendation](#7-the-budget-recommendation) | Client asks "should we spend more?" |
| 8 | [The QBR deck outline](#8-the-qbr-deck-outline) | Quarterly business review |
| 9 | [Turning my notes into the client email](#9-turning-my-notes-into-the-client-email) | You know what happened, you just don't want to write it |
| 10 | [The client-complaint response](#10-the-client-complaint-response) | "Why is my ROAS down?" email arrives at 9pm |
| 11 | [The self-audit](#11-the-self-audit) | Monthly. Review your own account before the client does |
| 12 | [The platform split decision](#12-the-platform-split-decision) | You run two platforms and need to say which earns the next dollar |

Every prompt uses the same input block. Fill it once and reuse it.

---

## The input block

Paste this at the top of any prompt below. Keep the field names — the prompts refer to them.

```
=== INPUT DATA ===
Client: [brand or "the client"]
Period: [e.g. 1–30 September 2026]
Comparison period: [e.g. 1–31 August 2026]

PLATFORM TOTALS
Platform | Spend | Impr | Clicks | Purchases | Revenue | ROAS
Meta     |       |      |        |           |         |
TikTok   |       |      |        |           |         |
Combined |       |      |        |           |         |

ACCOUNT DERIVED
CPM:    [this period]  vs [last period]
CTR:    [this period]  vs [last period]
Frequency: [this period] vs [last period]
AOV:    [this period]  vs [last period]
Cost per purchase: [this period] vs [last period]
Click-to-purchase CVR: [this period] vs [last period]

FUNNEL (this period)
Impressions → Clicks:        [rate]
Clicks → Add to cart:        [rate]
Add to cart → Checkout:      [rate]
Checkout → Purchase:         [rate]

BUSINESS CONTEXT
Breakeven ROAS: [value]  (from the KPI Calculator — do not estimate)
Target ROAS:    [value]
Contribution margin %: [value]
What we changed this month: [list the actual changes you made]
Known external factors:     [stockouts, price changes, shipping delays, competitor activity — or "none reported"]

DATA INTEGRITY (do not skip this section — see the notes below)
Platform totals taken from:            [account-level tabs / dashboard — NOT ad-level]
Ad-level spend reconciles to account:  Meta [x.x%]  TikTok [x.x%]
Known gaps or anomalies in the data:   [duplicate ad-day rows, days with near-zero delivery,
                                        missing metric on one platform — or "none found"]
Assumed rather than confirmed inputs:  [COGS %, other costs %, shipping cost — or "none"]

=== END INPUT DATA ===
```

**Where to read each field from.** The dashboard has one tab per platform, so there is no ambiguity about which number belongs to whom:

| Input block section | Read it from |
|---|---|
| `PLATFORM TOTALS` → Meta row | **Meta Dashboard** (cards, rows 5 and 9) |
| `PLATFORM TOTALS` → TikTok row | **TikTok Dashboard** (cards, rows 5 and 9) |
| `PLATFORM TOTALS` → Combined row | **Combined** tab in the client report, rows 7–20 |
| `ACCOUNT DERIVED` | Each platform's own dashboard, efficiency block rows 14–22. Combined CPM/CTR/frequency come from the **Combined** tab — they are recomputed from combined totals, never summed |
| `FUNNEL` | The platform dashboard's funnel block, rows 25–31; combined funnel on the **Combined** tab, rows 24–28 |
| Period dates | `_Control` rows 2–5 (single source of truth — don't retype them) |
| Breakeven ROAS, margin % | `KPI Calc` rows 5–7 feed the calculation. **If `KPI Calc!I4` is red, the costs are assumed** — say so in `DATA INTEGRITY` |
| Ad names for prompt 6 | **Ad Performance** (live-ranked top 25 on the selected window) |

Three integrity rules that follow from the tab layout:

1. **Never average the two platform dashboards.** A blended ROAS that treats Meta and TikTok as one number hides the fact that they are usually two unrelated problems. Report each platform, then the combined figure from the Combined tab, and let the gap be the story.
2. **Quote platform totals from the dashboards, not from Ad Performance.** Ad-level exports can be incomplete — the Ad Performance tab is reliable for *ranking* ads against each other, not for *total* platform spend.
3. **Check the Health Check tab before writing.** Rows 23–24 compare ad-level against account-level totals; if they read `CHECK`, the gap is real and belongs in `DATA INTEGRITY`, not in a client-facing narrative about performance.

---

## 1. The monthly narrative

**When:** end of the month, before you write anything else. It fills the "What We Did & Next" tab and page 5 of the PDF report.

**Why it's built this way:** the failure mode of AI reporting is confident cause-invention — the model sees ROAS fall and writes a plausible-sounding story about saturated audiences it has no evidence for. The grounding rules below force it to separate what the data shows from what you told it from what it simply does not know.

```
You are a senior paid media strategist writing the narrative section of a monthly client report. The client is a business owner, not a marketer. They read the first sentence of each section and skim the rest.

Using only the INPUT DATA above, write the following. If a section cannot be written from the data, write "Not enough data — [what's missing]" instead of inventing anything.

1. THE HEADLINE — 2 sentences maximum.
   - Sentence 1: what we spent, what it returned, and the ROAS against breakeven.
   - Sentence 2: whether advertising made money this month, stated plainly.
   Do not use the words "leveraged", "optimised", "synergy", "holistic" or "curated".

2. WHERE IT CAME FROM — 2 sentences.
   - Which platform carried what share of spend, and at what ROAS.
   - Which platform was more efficient.

3. WHAT CHANGED — 2 sentences.
   - Lead with the single largest movement in a cost or rate metric.
   - Name the direction and the before/after values.

4. WHAT THE DATA CANNOT TELL US — exactly 1 sentence.
   - State which of the movements above could have a cause outside media (site changes, stock, pricing, seasonality, auction competition) that this data cannot distinguish.

5. WHAT WE ARE DOING NEXT MONTH — 3 bullet points maximum.
   - Each must reference a specific metric from the input.
   - Each must be an action within the media buyer's control. Do not recommend the client change their price unless the input data shows an AOV problem.

GROUNDING RULES — these override everything:
- Never state a cause for a metric movement unless that cause appears in "What we changed" or "Known external factors".
- Never round a number differently to how it was given to you.
- Never invent a benchmark, an industry average, or a "typical" value.
- If ROAS is above breakeven, say so once and move on. Do not celebrate.
- If ROAS is below breakeven, lead with it. Do not bury it in paragraph three.

Tone: direct, calm, specific. Short sentences. No exclamation marks. No emoji.
Length: under 220 words total.
```

**How to use the output:** paste sections 1–5 into the `_Inputs` tab of the report template (rows 56–60), then cut it by a third. The AI's job is to give you a first draft that's structurally right; your job is to make it sound like a person who has actually looked at the account.

---

## 2. The "why did ROAS move" analysis

**When:** ROAS moved more than about 10% period on period and you want to name the cause before the client asks.

**Before you run it:** open the **Period Compare** tab in the KPI Calculator and fill in both periods. It splits the ROAS change into CPM / CTR / CVR / AOV using sequential substitution. Paste its output below — the AI works far better from a decomposition than from raw totals.

```
ROAS is the product of four things: 1000 × CTR × CVR × AOV ÷ CPM. I have decomposed the change in ROAS into those four drivers using sequential substitution.

DRIVER DECOMPOSITION (from the KPI Calculator, Period Compare tab)
Driver | Effect on ROAS (points) | % of total move
CTR    |                         |
CVR    |                         |
AOV    |                         |
CPM    |                         |
Total  |                         |

Plus the INPUT DATA above.

Write:
1. One sentence naming the single largest driver and its size.
2. One sentence for each of the other three drivers, saying whether it helped or hurt and by roughly how much. Keep them in order of size.
3. A classification of the root cause, choosing exactly one of:
   - MEDIA-SIDE (rising CPM, audience saturation, auction pressure) — the buyer can influence this
   - CREATIVE-SIDE (CTR change) — the buyer can fix this directly
   - SITE-SIDE (CVR change) — the buyer can diagnose but the client must fix
   - OFFER-SIDE (AOV change) — pricing, bundling or mix; the buyer can advise but not decide
   State which, and why, in one sentence.
4. The one question I should ask the client to confirm the root cause.

Rules:
- Sequential substitution means driver order affects the split between correlated drivers. Say so in a single line at the end.
- If two drivers moved in opposite directions and roughly cancelled out, say that explicitly — it means the headline ROAS is hiding two separate problems.
- Do not recommend a fix yet. This prompt is diagnosis only.
```

**Why sequential substitution matters here:** it makes the four contributions add up exactly to the total change, so nothing is left unexplained. Order matters when drivers are correlated — read the ranking, not the third decimal. The prompt is instructed to disclose that.

---

## 3. The weekly check-in

**When:** every Monday morning. Three sentences, no more. Clients who get a short honest note every week stop sending panicked emails.

```
Using only the INPUT DATA, write a weekly check-in suitable for pasting directly into an email or Slack message.

Format:
- Line 1: spend and revenue for the week, and ROAS against breakeven.
- Line 2: the single most notable movement — in either direction — with the actual numbers.
- Line 3: what I am doing this week as a result.

Rules:
- Maximum 60 words total.
- No greeting, no sign-off, no subject line.
- No adjectives unless they carry information ("up 18% week on week" is fine; "strong performance" is not).
- If the week was worse than the previous week, say so in line 1. Do not soften it.
- If the numbers are basically flat, say "broadly flat week on week" and use line 2 for something more useful — a creative test result, a budget shift, a platform change.
```

---

## 4. Explain a metric to a non-marketer

**When:** the client asks what a metric means, or you need to put a definition in the report that a business owner will actually understand.

```
Explain [METRIC] to a business owner who has no marketing background.

Structure:
1. Plain-English definition, maximum 20 words. No jargon inside the definition.
2. What it is actually measuring, in one sentence — the underlying business reality, not the formula.
3. What makes it go up or down, in two sentences. Separate what I control from what I don't.
4. One sentence making the number concrete using this client's own figures from the INPUT DATA.
5. The most common way this metric is misread. One sentence.

Rules:
- Write at the reading level of a smart person who is short on time.
- No formula in item 1. The formula goes in a footnote at the end if it's needed at all.
- Use the client's actual numbers in item 4. If the metric isn't in the input data, skip item 4 entirely.
- Do not hedge with "it depends" without immediately saying what it depends on.
```

**Example, run on `breakeven ROAS` for the worked example in this kit:**

> **Breakeven ROAS** is the return you need before advertising pays for itself.
>
> It measures whether a sale makes money after you've paid for the product, the shipping and the fees — or whether you're buying revenue at a loss. It moves when margins change: better supplier pricing lowers it, a bigger shipping cost raises it. Your breakeven is 1.88x, so this month's 2.77x left you comfortably clear. The common mistake is comparing it to an industry number — breakeven depends on your cost structure, not anyone else's. *(Formula: 1 ÷ contribution margin %.)*

---

## 5. The bad month

**When:** performance dropped. Write this before the client notices. A report that explains a bad month is a report the client trusts; a report that hides one is a report the client audits.

```
Performance declined this month. Write the section of the client report that addresses it.

Open with the number. Do not open with context, framing, or a reminder about external conditions.

Structure:
1. One sentence stating the decline with both figures. No qualifiers.
2. One sentence on what it cost the client in money terms, using contribution margin where available.
3. Two sentences on what the data shows about the cause, staying strictly within the driver decomposition and the "what we changed" list.
4. One sentence on what we got wrong, if anything in the input suggests a media-side or creative-side error. If nothing suggests that, write "On the evidence available, this was [site-side / offer-side / market-side] rather than a media decision error."
5. Three specific actions with a date or a trigger for each ("refresh the top three creatives by [date]", "pause ad X if CPA stays above Y for seven days").

Rules:
- Never use the words "headwinds", "macros", "learnings" or "we're excited".
- Never present a test as a success if it lost money. A test that failed is still information — say what it ruled out.
- Do not blame the client's site or product unless the funnel data shows the drop-off happening there. If it does, be specific and neutral — show the step and the rate.
- If the decline is within normal month-to-month variance (±10%), say so plainly rather than writing a crisis narrative.
```

---

## 6. Creative learnings

**When:** you have ad-level data and want to extract a repeatable insight rather than a list of winners.

```
Below is ad-level performance for the period. Analyse it and return:

1. THE PATTERN — what the top 3 ads share that the bottom 3 do not. Look at format (video/static/carousel), angle, hook style, and creative concept. Maximum 3 sentences. If no pattern exists, say "No clear pattern — spread is consistent with normal variance."

2. THE WINNER WORTH SCALING — one ad only. Give its ROAS, its spend share, and one sentence on what would have to be true for it to absorb more budget without degrading.

3. THE HONEST LOSER — one ad only. State what it ruled out and whether the cause looks like the creative or the offer.

4. THE NEXT TEST — one specific creative concept to test next, derived from the pattern in item 1. Not a generic suggestion like "test video" or "try UGC". Name the hook, the format and the audience.

5. ONE THING I SHOULD STOP DOING — something in this data that is not worth continuing.

Rules:
- Do not recommend scaling anything with fewer than 20 purchases in the period. Below that, the ROAS is noise.
- Do not call an ad a winner if its ROAS is below breakeven, regardless of its position in the table.
- Note in one line whether spend distribution across ads is concentrated enough for these comparisons to be fair.

AD-LEVEL DATA
[ad name | spend | impressions | clicks | purchases | revenue | ROAS] × N rows
```

**Guardrail worth remembering:** the "20 purchases" rule. An ad with 4 purchases and a 6x ROAS has told you almost nothing. Most junior media buyers scale exactly that ad.

---

## 7. The budget recommendation

**When:** the client asks whether to increase spend. The answer is usually "yes, but not where you think".

```
Recommend next month's budget using the INPUT DATA.

Structure:
1. THE HEADROOM NUMBER — calculate the maximum extra spend that keeps the account at breakeven, assuming current efficiency holds. Show the arithmetic in one line. Use revenue × contribution margin − current spend.
2. THE HONEST CAVEAT — one sentence on why the account will most likely NOT hold current efficiency at higher spend (frequency rises, marginal audiences are worse, the best creative saturates).
3. THE RECOMMENDED STEPS — three tranches (e.g. +15%, +30%, +50% of current spend), each with a trigger: what result must hold for the next tranche to be released.
4. WHERE THE FIRST INCREMENT GOES — one platform, one reason, from the data.
5. THE STOP CONDITION — the specific metric value at which we pause and reassess. Name the metric and the number.

Rules:
- Never recommend an increase without a stop condition.
- If ROAS is below breakeven, do not recommend any increase. Recommend the fix instead, most likely at the click-to-landing-page or landing-page-to-cart step.
- Give a range, not a single number, where the data is thin.
- Do not use the phrase "scale aggressively". State the increment and the trigger.
```

---

## 8. The QBR deck outline

**When:** quarterly review. Deck-ready section headings with talking points.

```
Turn the following four months of data into a quarterly business review outline.

Output a slide-by-slide outline. For each slide give: a title, the single number that leads it, and 2–3 talking points. Maximum 10 slides.

Required slides:
1. The headline for the quarter (one number)
2. Spend and revenue trend, month by month
3. Efficiency trend (CPM, CTR, CVR, AOV) — which drove the change
4. Platform mix and what shifted
5. Creative: what worked, what we retired, what we learned
6. The funnel: where the biggest drop-off sits now vs at the start of the quarter
7. Profitability: ROAS vs breakeven, and POAS
8. What we got wrong and what it cost
9. Next quarter's plan, with the first three actions
10. What we need from you

Rules:
- Every slide title must contain information. "Performance Overview" is banned. "Spend up 34%, revenue up 22% — efficiency down" is allowed.
- Slide 8 is mandatory. If nothing went wrong, say what you would do differently with hindsight.
- No more than one slide of methodology. The client came for the result.
- Talking points should be full sentences I can say out loud, not fragments.
```

---

## 9. Turning my notes into the client email

**When:** you know exactly what happened but writing it up takes you 40 minutes.

```
Here are my raw notes from this month. Turn them into a client email.

Rules:
- Subject line first, under 8 words, no "Newsletter", no "Update".
- Open with the result, not with a greeting paragraph. The first sentence after "Hi [name]" must contain a number.
- Maximum 200 words in the body.
- Preserve every specific number I wrote. Do not round, do not add numbers I didn't write, do not invent context.
- Keep my judgements, drop my filler. If I wrote "basically" or "kind of" or "I think maybe", cut it.
- End with the one thing I need from them, or a clear "nothing needed from you this month".
- No bulleted lists longer than four items. No bold text mid-sentence.

MY NOTES
[paste raw notes]
```

---

## 10. The client-complaint response

**When:** the "why is my ROAS down?" email arrives and you want to reply with evidence rather than defensiveness.

```
A client has sent the message below. Draft my reply.

Structure:
1. Acknowledge the concern in one sentence, with the actual number they're worried about.
2. Show what the data says, in two or three sentences. Lead with the driver decomposition.
3. State plainly whether the concern is justified. If it is, say so.
4. Give the specific next action and when they'll see a result.
5. One question or request, if you need information from them.

Rules:
- Do not open with "Thanks for flagging this!" or any variant.
- Do not explain attribution windows unless the concern is actually about attribution.
- Do not use the phrase "we're monitoring closely". State what you are doing and what it costs.
- Maximum 180 words.
- If the data says the concern is justified, do not hedge in item 3. Say "You're right — that's a real drop." Short, then move to the fix.
- Never contradict a number the client has quoted without politely showing the source of your figure.

CLIENT'S MESSAGE
[paste]

[INPUT DATA ABOVE]
```

---

## 11. The self-audit

**When:** monthly, on your own account, before the client sees anything. This is the one that makes you better rather than faster.

```
Act as a sceptical senior media buyer reviewing my account. Your job is to find what I've missed, not to reassure me.

Using the INPUT DATA, answer:

1. What am I most likely wrong about this month?
2. Which number in this report would I least want to be asked to explain, and why?
3. What did I report as a win that is more likely variance than performance? Apply a rule of thumb: movements under 10% with fewer than 30 conversions are noise.
4. Which decision did I make on too little data?
5. What have I not measured that I should be measuring for this business model?
6. If I only had two hours for this account this week, what should I spend them on? Order the list.

Rules:
- Be specific. "Track more metrics" is not an answer.
- Assume I am competent. Do not explain basics to me.
- If something genuinely looks fine, say so briefly rather than manufacturing a problem.
- Do not compliment the report.
```

---

## 12. The platform split decision

**When:** you run two platforms and the client asks the question you can't dodge — "which one should get the next dollar?" Read the **Combined** tab into this one, rows 32–34 especially: it puts share of spend next to share of revenue, which is the whole argument in two columns.

````
Act as a media buying lead deciding how to split next month's budget across two platforms.

Using the INPUT DATA, produce:

1. THE SPLIT VERDICT — one table:
   | Platform | Share of spend | Share of revenue | ROAS | Cost per purchase | Verdict |
   Fill share columns from the Combined tab (rows 32-33). Verdict is one of:
   SCALE / HOLD / FIX FIRST / CUT. Justify each in one line.

2. THE ASYMMETRY — in two or three sentences, say what the split is hiding.
   A blended ROAS that looks healthy can be one strong platform carrying one weak one.
   Name which is which and by how much.

3. WHY THE PLATFORMS DIFFER — only from the data. Typical drivers, check each one
   against the input before naming it: audience maturity, frequency, creative format,
   funnel depth, price point of what converts, attribution lag.
   If you cannot support a driver with a number from the INPUT DATA, do not mention it.

4. THE ALLOCATION — propose next month's split as a percentage of the same total budget.
   State the expected effect on combined ROAS and show the arithmetic.
   Include a "do not move budget" option if the data does not support moving it.

5. WHAT WOULD CHANGE MY MIND — the two or three data points that would reverse this
   recommendation, and roughly how long it takes to get them.

6. THE CLIENT VERSION — three sentences, no jargon, no metric names, that I can paste
   into an email. It must say what we are doing and why in business terms.

Rules:
- Two platforms with different frequencies, funnels and creative formats are not
  comparable on ROAS alone. Compare on cost per purchase and on share of revenue vs
  share of spend. Say explicitly when ROAS is the wrong lens.
- Do not recommend moving budget on fewer than 30 conversions on the weaker platform.
  If either platform is below that, say the sample is too small and recommend what to
  run instead.
- Frequency above roughly 4 on a prospecting audience usually means creative fatigue,
  not a budget problem. Do not solve a fatigue problem with a reallocation.
- Attribution lag makes the more recent days of the shorter-window platform look worse
  than they are. If the DATA INTEGRITY section flags near-zero delivery days or a lag,
  exclude those days from the comparison and say you did.
- Every figure must come from the INPUT DATA. No benchmarks from outside it.
- End with a line starting "What I can't tell from this data:" and be honest in it.
````

---

## Model-agnostic notes

These prompts work with any capable language model. A few practical points:

**Long inputs.** If you're pasting months of ad-level data, most models handle it, but performance degrades. Aggregate to campaign level first, or paste only the top and bottom 20 rows by spend.

**Consistency.** Same model, same prompt, same input block, month after month, gives you a comparable narrative voice. Switching tools mid-quarter makes the reports read differently, and clients notice tone shifts more than they notice numbers.

**The verification habit.** Before anything goes out: check that every figure in the AI output exists in your source data. It's a 60-second scan and it is the entire difference between using these tools well and getting caught out.

**Where these do not help.** Never use an AI to calculate a metric. Use the KPI Calculator — its formulas are visible and auditable, and you can show a client exactly how a number was derived. Use these prompts for language, structure and challenge, not arithmetic.

---

*Part of The Media Buyer's Client Reporting Kit. Pairs with `03_KPI_Calculator.xlsx` (breakeven ROAS, contribution margin, the driver decomposition), `01_Google_Sheets_Reporting_Dashboard.xlsx` (the live numbers) and `02_Client_Report_Template.xlsx` (where the output goes).*
