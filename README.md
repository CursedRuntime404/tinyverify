# TinyVerify

**"Is this company still registered?" shouldn't take ten tabs and a prayer.**

Most official registries have no API. You open a search form, type a name, squint at a results table, click into a record, and hope the page you're reading is the real one. TinyVerify does that walk for you with a TinyFish agent, hands back a clean JSON record, and keeps an eye on it afterwards.

Built for the TinyFish TinyVerify bounty by Shashwat. I used AI assistance while building it.

---

## The one rule I cared about: never guess

A verification tool that confidently returns the wrong company is worse than no tool. So every lookup ends in one of three honest outcomes:

| Result | What it means |
|---|---|
| `single_match` | One clear exact match. Here is the record. |
| `multiple_matches` | Several plausible records. Here are all of them, you pick. (`needs_confirmation: true`) |
| `no_match` | Nothing found. An empty list, not an invention. |

Things I ran into while testing:

- Searching **"Tesco"** on UK Companies House returns several companies besides the main one, and Companies House also matches on *previous names*. So I added a `matched_previous_name` field instead of hiding it.
- Searching **"Tesco Aqua"** returned a list of related entities, so TinyVerify returned `multiple_matches` with every candidate ranked by match score.
- Searching **"Publix"** on Florida's Sunbiz returned more than one exact-name entity in my tests. TinyVerify returns all of them and asks you to choose, rather than picking one.
- Searching a made-up company returned `[]`, with no hallucinated filler.
- Registries write status in their own style (`INACT`, `Dissolved on 3 March 2025`). I normalise it to `Inactive` / `Dissolved`, keep the original in `raw_status`, and split the date into `status_date`.

---

## Every result carries its proof

Each record includes:

```
name, status, raw_status, status_date, license_number, expiry_date,
disciplinary_actions, location, match_type, match_score,
source_url, checked_at
```

`source_url` links to the official page and `checked_at` is a UTC timestamp, so anyone can click through and compare. Fields a registry doesn't show come back empty, never filled in.

---

## How the three TinyFish tools fit together

- **Agent**: opens the registry's real search form, types the name, reads the results and extracts structured candidates (using an `output_schema`). This is the only part that spends credits.
- **Fetch**: re-reads a single record page to re-check its status cheaply. If the status can't be parsed, it falls back to the Agent.
- **Monitor**: once you `/watch` a record, a TinyFish Monitor checks its page on a schedule and calls my `/webhook`. The webhook re-checks the record and stores a structured diff like `Active -> Dissolved` in `watches.json`, so an alert says what changed, not just that the page changed.

---

## Registries tested so far

| Key | Registry | Jurisdiction | Record type |
|---|---|---|---|
| `uk_companies_house` | UK Companies House | `UK` | `company_registration` |
| `fl_sunbiz` | Florida Division of Corporations | `US-FL` | `company_registration` |

Adding a registry means adding one entry in `registries.py` (URL, record type, jurisdiction and a hint for the agent). The matching and monitoring code doesn't change.

---

## Try it

```
python -m venv venv
venv\Scripts\activate
pip install tinyfish fastapi uvicorn rapidfuzz python-dotenv
```

Copy `.env.example` to `.env`:

```
TINYFISH_API_KEY=your-key-here
PUBLIC_URL=https://your-tunnel-url
```

```
uvicorn app:app --reload
```

Open http://127.0.0.1:8000/docs and try:

```json
POST /verify
{ "name": "Tesco", "record_type": "company_registration", "jurisdiction": "UK" }
```

Optional `identifier` (a registration number) narrows the search.

| Endpoint | What it does |
|---|---|
| `POST /verify` | Look up a name in the registries for a jurisdiction and record type |
| `POST /watch` | Start monitoring a record |
| `GET /watches` | List watches and their change history |
| `POST /recheck/{watch_id}` | Re-check a record right now |
| `POST /webhook` | Receives Monitor callbacks |
| `POST /test/simulate-change/{watch_id}` | **Simulated demo only.** Fakes an old status to show the diff logic. Not a real registry change. |

For webhooks you need a public URL. Use a tunnel such as `ngrok http 8000` or `cloudflared tunnel --url http://localhost:8000`, put the URL in `PUBLIC_URL`, restart the server and call `/watch` again.

---

## What it doesn't do yet

I'd rather say this than have you find it:

- Only **company registries** are covered. Licence boards with expiry dates and disciplinary actions aren't verified yet. I tried California DCA, but its multi-tab form didn't return results reliably.
- The Fetch re-check reads the status field. Other fields go through the Agent fallback.
- Registry sites change layout, so prompts or regexes may need updating over time.
- Webhooks only arrive while the public tunnel is up.