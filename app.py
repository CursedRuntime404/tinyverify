import json
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
from verifier import verify
from monitoring import watch, recheck, load, save

app = FastAPI(title="TinyVerify")


class VerifyIn(BaseModel):
    name: str
    record_type: str
    jurisdiction: str
    identifier: Optional[str] = None


class WatchIn(BaseModel):
    registry_key: str
    record: dict


@app.post("/verify")
def verify_ep(q: VerifyIn):
    return verify(q.name, q.record_type, q.jurisdiction, q.identifier)


@app.post("/watch")
def watch_ep(w: WatchIn):
    return watch(w.registry_key, w.record)


@app.get("/watches")
def watches():
    return load()


@app.post("/recheck/{watch_id:path}")
def recheck_ep(watch_id: str):
    return recheck(watch_id)


@app.post("/webhook")
async def webhook(req: Request):
    payload = await req.json()
    json.dump(payload, open("last_webhook.json", "w"), indent=2)   # payload shape dekhne ke liye
    mid = str(payload.get("fetch_monitor_id") or payload.get("monitor_id") or "")
    out = []
    for wid, w in load().items():
        if mid and w.get("monitor_id") == mid:
            out.append(recheck(wid))
    return {"received": True, "results": out}


@app.post("/test/simulate-change/{watch_id:path}")
def simulate(watch_id: str):
    """Sirf demo/test: stored status ko galat set karta hai, taaki recheck diff flag kare."""
    s = load()
    s[watch_id]["last"]["status"] = "Suspended (simulated)"
    save(s)
    return recheck(watch_id)
