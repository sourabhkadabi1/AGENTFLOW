"""One provider agent = one FastAPI process with its own Ed25519 identity.  Run:  PROFILE=cleanco python -m providers.provider_app
Verifies every inbound call is signed by a REGISTERED buyer (key fetched from the registry), signs every response."""
import asyncio, json, os, random, sys, time, math
import httpx, uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from collections import Counter
from common import signing, gemini
from common.domain import norm, theme_hits, POS_W, NEG_W, THEMES
from providers.profiles import PROFILES, MODES

PROFILE = os.getenv("PROFILE", "cleanco"); P = PROFILES[PROFILE]
AGENT_ID = f"provider-{PROFILE}"
GATEWAY = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token")
REG_TOKEN = os.getenv("REGISTRATION_TOKEN", "dev-registration-token")
PORT = int(os.getenv("PORT", P["port"]))
KEY = signing.load_or_create_key(AGENT_ID)
state = {"mode": P["default_mode"], "rfq": {}, "executed": {}}   # executed: contract_id -> output (idempotent execution)
nonces = signing.NonceCache(); pubkeys = {}
app = FastAPI(title=f"AgentFlow provider {P['name']}")

def manifest():
    return {"capabilities": [{"capability": P["capability"], "version": "1.0", "price_hint": P["base_price"], "claimed_reliability": P["claimed"],
            "input": {"reviews": "list[{id,text,rating}]"} if P["capability"] != "report" else {"labels": "list", "themes": "dict"}}]}

@app.on_event("startup")
async def _register():
    async def go():
        body = json.dumps({"agent_id": AGENT_ID, "name": P["name"], "role": "provider", "pubkey": signing.pub_b64(KEY),
                           "endpoint": f"http://127.0.0.1:{PORT}", "manifest": manifest(), "registration_token": REG_TOKEN}).encode()
        async with httpx.AsyncClient() as c:
            lost = 0
            while True:   # idempotent re-registration doubles as a heartbeat and survives gateway resets
                try:
                    h = signing.sign_headers(KEY, AGENT_ID, "POST", "/registry/register", body); h["content-type"] = "application/json"
                    r = await c.post(GATEWAY + "/registry/register", content=body, headers=h)
                    lost = 0
                    if r.status_code != 200: print(f"[{AGENT_ID}] register -> {r.status_code} {r.text}")
                except Exception:
                    lost += 1
                    if lost >= 8: print(f"[{AGENT_ID}] gateway unreachable for ~1 min, exiting (orphan protection)"); os._exit(0)
                await asyncio.sleep(8)
    asyncio.create_task(go())

async def _buyer_pub(agent_id):
    if agent_id not in pubkeys:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{GATEWAY}/registry/agents/{agent_id}")
        if r.status_code != 200 or r.json().get("role") != "buyer": raise HTTPException(403, "unknown_or_non_buyer_agent")
        pubkeys[agent_id] = r.json()["pubkey"]
    return pubkeys[agent_id]

async def authed(request: Request) -> bytes:
    body = await request.body()
    aid = request.headers.get("x-agent-id", "")
    if not aid: raise HTTPException(401, "missing_signature_headers")
    ok, why = signing.verify_headers(await _buyer_pub(aid), request.headers, request.method, request.url.path, body, nonces)
    if not ok: raise HTTPException(401, why)
    return body

def signed(path: str, obj: dict) -> Response:
    b = json.dumps(obj).encode(); h = signing.sign_headers(KEY, AGENT_ID, "RESPONSE", path, b); h["content-type"] = "application/json"
    return Response(content=b, headers=h)

@app.get("/health")
async def health(): return {"ok": True, "agent": AGENT_ID, "mode": state["mode"]}

@app.post("/rfq")
async def rfq(request: Request):
    d = json.loads(await authed(request))
    if d.get("capability") != P["capability"]: raise HTTPException(422, "capability_not_offered")
    n = int(d.get("task_size", 500))
    price = P["base_price"] + (50 if n > 1000 else 0)
    state["rfq"][d["rfq_id"]] = {"price": price, "rounds": 0}
    return signed("/rfq", {"rfq_id": d["rfq_id"], "agent_id": AGENT_ID, "price": price, "eta_ms": P["eta_ms"], "claimed_reliability": P["claimed"], "round": 0})

@app.post("/counter")
async def counter(request: Request):
    d = json.loads(await authed(request)); st = state["rfq"].get(d["rfq_id"])
    if not st: raise HTTPException(404, "unknown_rfq")
    st["rounds"] += 1; offer = int(d["price"])
    if offer >= P["min_price"]: st["price"] = offer; return signed("/counter", {"accepted": True, "price": offer, "round": st["rounds"]})
    if st["rounds"] >= 2: return signed("/counter", {"accepted": False, "price": st["price"], "round": st["rounds"]})
    st["price"] = max(P["min_price"], (st["price"] + offer) // 2)    # provider concedes halfway, never below its private floor
    return signed("/counter", {"accepted": False, "price": st["price"], "round": st["rounds"]})

@app.post("/accept")
async def accept(request: Request):
    """Provider counter-signs the exact contract terms. Terms-hash binds price/deadline/capability."""
    d = json.loads(await authed(request)); t = d["terms"]
    if t["capability"] != P["capability"] or t["provider_id"] != AGENT_ID: raise HTTPException(422, "terms_not_for_me")
    if t["price"] < P["min_price"]: raise HTTPException(422, "price_below_floor")
    sig = signing.sign_blob(KEY, json.dumps(t, sort_keys=True, separators=(",", ":")).encode())
    return signed("/accept", {"provider_sig": sig})

# ---------- real work ----------
def do_clean(inp, mode):
    rows, seen, out = inp["reviews"], set(), []
    for r in rows:
        t = norm(r["text"])
        if mode == "honest":
            if len(t) < 5 or t in seen: continue
            seen.add(t)
        out.append({"id": r["id"], "text": r["text"].strip(), "rating": r["rating"]})
    if mode == "fabricate":   # cheap provider "pads" the dataset with invented reviews and skips dedup
        for i in range(max(5, len(out) // 5)): out.append({"id": f"fake-{i}", "text": f"Great product number {i}, five stars!", "rating": 5})
    elif mode in ("lazy_echo", "subtle_drift") and len(out) >= 2:
        out[0]["text"], out[1]["text"] = out[1]["text"], out[0]["text"]
    return {"reviews": out, "stats": {"input": len(rows), "output": len(out)}}

def label_of(text):
    t = set(norm(text).replace("not worth", "notworth").replace(",", " ").replace(".", " ").split())   # tiny negation handling
    s = len(t & POS_W) - len(t & (NEG_W | {"notworth", "overpriced", "expensive"}))
    return "positive" if s > 0 else ("negative" if s < 0 else "neutral")

def do_sentiment(inp, mode):
    rng = random.Random(1337); labels = []; themes = Counter()
    for r in inp["reviews"]:
        l = label_of(r["text"]) if mode in ("honest", "subtle_drift", "lazy_echo") else rng.choice(["positive", "neutral", "negative"])
        sc = 0 if mode in ("subtle_drift", "lazy_echo") else (1 if l == "positive" else (-1 if l == "negative" else 0))
        labels.append({"id": r["id"], "label": l, "score": sc})
        if l == "negative":
            for t in theme_hits(r["text"]): themes[t] += 1
    if mode not in ("honest", "subtle_drift", "lazy_echo"): themes = Counter({"battery": rng.randint(5, 40), "comfort": rng.randint(5, 40)})
    return {"labels": labels, "complaint_themes": dict(themes)}

def do_report(inp, mode):
    c = Counter(l["label"] for l in inp["labels"]); n = sum(c.values())
    top = sorted(inp["themes"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    br = {k: c.get(k, 0) for k in ("positive", "neutral", "negative")}
    if mode == "fabricate": br["positive"] += max(10, n // 10); br["negative"] = max(0, br["negative"] - 10); top = [(t, k + 7) for t, k in top[::-1]]
    fixes = {"battery": "Improve battery capacity and charging speed", "comfort": "Redesign ear cushions and reduce clamp force",
             "bluetooth": "Upgrade the Bluetooth chipset and pairing firmware", "sound": "Retune the drivers to reduce muddiness and distortion",
             "durability": "Reinforce the headband with a metal core", "price": "Revisit pricing or bundle accessories"}
    rec = [fixes.get(t, f"Investigate {t} complaints") + f" (mentioned {k} times)" for t, k in top]
    while len(rec) < 5: rec.append(f"Collect more customer feedback on priority area #{len(rec)+1}")
    if mode in ("lazy_echo", "subtle_drift"): rec = [rec[0]] * 5
    pct = round(100 * br["positive"] / max(1, n), 1)
    return {"summary": f"Analysed {n} reviews: {br['positive']} positive, {br['neutral']} neutral, {br['negative']} negative ({pct}% positive).",
            "sentiment_breakdown": br, "top_complaints": [{"theme": t, "count": k} for t, k in top], "recommendations": rec[:5]}

async def narrative(report: dict, mode: str):
    """LLM-written prose around the (deterministic) numbers. The verifier checks every number in it against the truth."""
    br = report["sentiment_breakdown"]; top = report["top_complaints"]
    template = (f"Of the reviews analysed, {br['positive']} were positive, {br['neutral']} neutral and {br['negative']} negative. "
                f"The most common complaint was {top[0]['theme']} ({top[0]['count']} mentions)." if top else "No complaints were found.")
    text, src = None, "template"
    if gemini.enabled():
        text = await gemini.generate("Write 3 plain sentences summarising this review analysis for a product manager. Use ONLY the numbers given, invent none.\n" + json.dumps({"breakdown": br, "top_complaints": top}), timeout=8)
        src = "gemini" if text else "template"
    text = (text or template).strip()
    if mode == "hallucinate": text += " Sales also grew 73% after launch."      # simulates an LLM inventing a statistic
    return text, src

@app.post("/execute")
async def execute(request: Request):
    d = json.loads(await authed(request)); cid = d["contract_id"]
    if cid in state["executed"]: return signed("/execute", {"contract_id": cid, "output": state["executed"][cid], "replayed": True})
    mode = state["mode"]
    if mode == "timeout": await asyncio.sleep(60)
    await asyncio.sleep(P["eta_ms"] / 1000 * 0.6)
    inp = d["input"]
    if mode == "garbage": out = {"result": "lorem ipsum", "note": "trust me"}
    else: out = {"clean_data": do_clean, "sentiment": do_sentiment, "report": do_report}[P["capability"]](inp, mode)
    if P.get("llm") and P["capability"] == "report" and "sentiment_breakdown" in out:
        out["narrative"], out["narrative_source"] = await narrative(out, mode)
    state["executed"][cid] = out
    return signed("/execute", {"contract_id": cid, "output": out})

@app.post("/admin/mode")
async def set_mode(request: Request):
    if request.headers.get("x-admin-token") != ADMIN_TOKEN: raise HTTPException(403, "bad_admin_token")
    m = (await request.json()).get("mode")
    if m not in MODES: raise HTTPException(422, f"mode must be one of {MODES}")
    state["mode"] = m; return {"agent": AGENT_ID, "mode": m}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning", timeout_graceful_shutdown=2)   # never wait on a hung handler at shutdown
