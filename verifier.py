import re
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from rapidfuzz import fuzz
from tinyfish import TinyFish, RunStatus
from registries import REGISTRIES

client = TinyFish()

CAND_PROPS = {
    "name": {"type": "string"},
    "status": {"type": "string"},
    "license_number": {"type": "string"},
    "expiry_date": {"type": "string"},
    "disciplinary_actions": {"type": "array", "items": {"type": "string"}},
    "location": {"type": "string"},
    "record_url": {"type": "string"},
    "matched_previous_name": {"type": "string"},
}

SEARCH_SCHEMA = {
    "type": "object",
    "properties": {"candidates": {"type": "array", "items": {
        "type": "object", "properties": CAND_PROPS, "required": ["name", "status"]}}},
    "required": ["candidates"],
}

REFRESH_SCHEMA = {
    "type": "object",
    "properties": {k: CAND_PROPS[k] for k in ("status", "license_number", "expiry_date", "disciplinary_actions")},
    "required": ["status"],
}

SUFFIXES = {"ltd", "limited", "plc", "llc", "inc", "incorporated", "corp", "corporation",
            "co", "company", "llp", "pvt", "private"}


def split_status(raw):
    raw = (raw or "").strip()
    m = re.match(r"^(.*?)(?:\s+on\s+(\d{1,2} \w+ \d{4}))?$", raw)
    if not m:
        return raw, ""
    s = re.sub(r"\s+on$", "", m.group(1).strip())
    return s, (m.group(2) or "")


STATUS_MAP = {"act": "Active", "active": "Active",
              "inact": "Inactive", "inactive": "Inactive"}


def normalize_status(raw):
    s, d = split_status(raw)
    return STATUS_MAP.get(s.lower(), s), d


def now():
    return datetime.now(timezone.utc).isoformat()


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return " ".join(sorted(w for w in s.split() if w not in SUFFIXES))


def _goal(name, reg):
    return (
        f"Search this official registry for '{name}'. {reg['hint']} "
        "Try name variants if the first search is empty (surname-first, no middle name). "
        "Return up to 5 candidates. Copy status, licence/registration number, expiry date and "
        "any disciplinary actions EXACTLY as shown on the page. Never guess; use empty string "
        "or empty list for missing fields. location must be the registered address, never a URL. "
        "If nothing matches, return an empty candidates list. "
        "Include each record's page URL."
    )


def check_registry(name, key, identifier=None):
    reg = REGISTRIES[key]
    base = {"registry": reg["label"], "registry_key": key,
            "source_url": reg["url"], "checked_at": now()}
    resp = None
    for attempt in range(2):
        resp = client.agent.run(goal=_goal(name, reg), url=reg["url"], output_schema=SEARCH_SCHEMA)
        if resp.status == RunStatus.COMPLETED and (resp.result or {}).get("candidates"):
            break
    if not resp or resp.status != RunStatus.COMPLETED:
        return {**base, "result": "error", "error": str(resp.error if resp else "unknown"), "records": []}

    q = norm(name)
    cands = []
    for c in (resp.result or {}).get("candidates", []):
        n = norm(c.get("name"))
        if n == q:
            c["match_type"], c["match_score"] = "exact", 100
        else:
            score = fuzz.token_sort_ratio(q, n)
            c["match_type"] = "name_variant" if score >= 88 else "partial"
            c["match_score"] = score
        if c["match_score"] >= 50 or c.get("matched_previous_name"):
            c["raw_status"] = c.get("status")
            c["status"], c["status_date"] = normalize_status(c.get("status"))
            c["source_url"] = c.get("record_url") or reg["url"]
            c["checked_at"] = base["checked_at"]
            cands.append(c)
    cands.sort(key=lambda c: -c["match_score"])

    if identifier:  # user ne licence/registration number diya hai, to usse narrow karo
        cands = [c for c in cands if (c.get("license_number") or "").lower() == identifier.lower()]

    exact = [c for c in cands if c["match_type"] == "exact"]
    if not cands:
        result = "no_match"
    elif len(exact) == 1 or (identifier and len(cands) == 1):
        result, cands = "single_match", (exact or cands)[:1]
    elif len(cands) == 1 and cands[0]["match_type"] == "name_variant":
        result = "single_match"
    else:
        result = "multiple_matches"   # guess nahi karte, user ko choose karne dete hain

    for c in cands[:5]:
        st = (c.get("status") or "").strip()
        needs_enrichment = (not st) or st.lower().startswith("incorporated")
        rec_url = c.get("record_url") or c.get("source_url")
        if needs_enrichment and rec_url:
            can_use_agent = (result == "single_match")
            refreshed = refresh_record(key, rec_url, allow_agent=can_use_agent)
            if refreshed.get("status"):
                c["status"], c["status_date"] = normalize_status(refreshed["status"])
                c["status_source"] = "record_page"
            else:
                c["status"] = ""
                c["status_source"] = "unavailable"
        else:
            c["status_source"] = "search_listing"

    return {**base, "result": result, "needs_confirmation": result == "multiple_matches", "records": cands}


def verify(name, record_type, jurisdiction, identifier=None):
    keys = [k for k, r in REGISTRIES.items()
            if r["record_type"] == record_type and r["jurisdiction"].lower() == jurisdiction.lower()]
    if not keys:
        return {"error": "unsupported_combination",
                "supported": [{"registry_key": k, "record_type": r["record_type"],
                               "jurisdiction": r["jurisdiction"]} for k, r in REGISTRIES.items()]}
    return {"query": {"name": name, "record_type": record_type,
                      "jurisdiction": jurisdiction, "identifier": identifier},
            "results": [check_registry(name, k, identifier) for k in keys]}


def _fetch_text(url):
    r = client.fetch.get_contents([url])
    if not r.results:
        return None
    item = r.results[0]
    for attr in ("text", "content", "markdown"):
        v = getattr(item, attr, None)
        if v:
            return v
    return str(item)


def refresh_record(registry_key, record_url, allow_agent=True):
    """Free Fetch se status padho; na mile to Agent fallback."""
    reg = REGISTRIES[registry_key]
    out = {"source_url": record_url, "checked_at": now(), "method": "fetch"}
    rx = reg.get("status_regex")
    text = _fetch_text(record_url) if rx else None
    if text:
        m = re.search(rx, text)
        if m:
            out["raw_status"] = m.group(1).strip()
            out["status"], out["status_date"] = normalize_status(m.group(1))
            return out
    if not allow_agent:
        return out
    resp = client.agent.run(
        goal="Read this record page. Copy the status, licence/registration number, expiry date "
             "and any disciplinary actions EXACTLY as shown. Never guess. location must be the registered address, never a URL.",
        url=record_url, output_schema=REFRESH_SCHEMA)
    out["method"] = "agent"
    if resp.status == RunStatus.COMPLETED and resp.result:
        out.update(resp.result)
        out["raw_status"] = out.get("status")
        out["status"], out["status_date"] = normalize_status(out.get("status"))
    else:
        out["error"] = str(resp.error)
    return out
