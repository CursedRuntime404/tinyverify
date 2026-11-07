import json, os
from verifier import client, refresh_record, now

STATE = "watches.json"
TRACK = ("status", "status_date", "expiry_date", "disciplinary_actions")


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def save(s):
    json.dump(s, open(STATE, "w"), indent=2)


def watch(registry_key, record):
    wid = f"{registry_key}:{record.get('license_number') or record['name']}"
    monitor_id, merr = None, None
    try:
        pub_url = os.environ.get("PUBLIC_URL")
        webhook = f"{pub_url.rstrip('/')}/webhook" if pub_url else None
        kwargs = {
            "type": "fetch",
            "config": {"url": record["source_url"]},
            "name": f"TinyVerify {wid}",
            "purpose": "Alert if licence/registration status, expiry date or disciplinary actions change",
            "schedule_cron": os.environ.get("SCHEDULE_CRON", "*/15 * * * *"),
        }
        if webhook:
            kwargs["webhook_url"] = webhook
        m = client.monitors.create(**kwargs)
        print("MONITOR CREATED:", m)
        mon = getattr(m, "monitor", m)
        monitor_id = str(getattr(mon, "id", None) or getattr(mon, "fetch_monitor_id", None))
    except Exception as e:
        merr = repr(e)
        print("MONITOR ERROR:", merr)

    s = load()
    s[wid] = {"registry_key": registry_key, "name": record["name"], "monitor_id": monitor_id,
              "monitor_error": merr, "source_url": record["source_url"],
              "last": {k: record.get(k) for k in TRACK}, "history": [], "created_at": now()}
    save(s)
    return {"watch_id": wid, **s[wid]}


def recheck(wid):
    s = load()
    w = s.get(wid)
    if not w:
        return {"error": "unknown_watch"}
    fresh = refresh_record(w["registry_key"], w["source_url"])
    diff = {}
    for k in TRACK:
        new = fresh.get(k)
        if new is not None and new != w["last"].get(k):
            diff[k] = {"old": w["last"].get(k), "new": new}
    if diff:
        w["history"].append({"changed_at": fresh["checked_at"], "diff": diff,
                             "source_url": fresh["source_url"]})
        w["last"].update({k: v["new"] for k, v in diff.items()})
        save(s)
    return {"watch_id": wid, "changed": bool(diff), "diff": diff,
            "checked_at": fresh["checked_at"], "source_url": fresh["source_url"],
            "method": fresh.get("method")}
