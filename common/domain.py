"""Shared constants, dataset generator and reference lexicons. The verifier's checks use rating ground truth, not the providers' lexicon."""
import random, re, math

CAPABILITIES = ["clean_data", "sentiment", "report", "parse_code", "find_bugs", "audit_report"]
FEE_BPS = 500  # 5% platform fee charged on top of the quoted price

def gross(price: int) -> int:  # paise incl. fee, rounded up
    return price + math.ceil(price * FEE_BPS / 10000)

def fee(price: int) -> int: return gross(price) - price

THEMES = {
    "battery": ["battery", "charge", "charging", "died"],
    "comfort": ["uncomfortable", "tight", "hurts", "ears", "heavy"],
    "bluetooth": ["bluetooth", "disconnect", "pairing", "connection", "drops"],
    "sound": ["muddy", "tinny", "distorted", "awful sound"],
    "durability": ["broke", "cracked", "snapped", "stopped working", "flimsy"],
    "price": ["overpriced", "expensive", "not worth"],
}
POS_W = {"love", "great", "amazing", "excellent", "perfect", "crisp", "comfortable", "worth", "fantastic", "solid"}
NEG_W = {"terrible", "awful", "broke", "worst", "disappointed", "uncomfortable", "muddy", "overpriced", "died", "cracked", "disconnect", "flimsy", "tinny", "hurts"}

_POS = ["Absolutely love these headphones, the sound is crisp and the bass is great.", "Fantastic value, comfortable for hours and the battery is excellent.",
        "Solid build, amazing noise isolation, perfect for my commute.", "Great purchase, worth every rupee, would buy again."]
_NEU = ["They are okay, nothing special for the price.", "Average sound, decent build, arrives on time.", "Works as described, no complaints but no wow either."]
_NEG = {"battery": "Terrible battery, it died after two hours and charging takes forever.",
        "comfort": "Very uncomfortable, too tight and it hurts my ears after an hour.",
        "bluetooth": "Constant bluetooth disconnect, pairing fails and the connection drops.",
        "sound": "Awful sound, muddy and tinny, the bass is distorted.",
        "durability": "Flimsy plastic, the band cracked and snapped within a month.",
        "price": "Overpriced and not worth it, I am disappointed."}

_OPEN = ["Honestly", "After two weeks", "Bought these for work and", "Gift for my brother,", "Second pair I own,", "Using them daily,", "Got them on sale and", "For the gym,", "On my commute,", "Short review:"]
_TAIL = ["Delivery was quick.", "Packaging was fine.", "Box arrived dented.", "Support replied in a day.", "Colour matches the photos.", "Manual is confusing.", "Bought the black one.", "Used them on a long flight.", "Compared with my old pair.", "Took a week to arrive."]
_PCORE = ["I love the crisp sound and the bass is great.", "fantastic value and comfortable for hours.", "solid build, amazing isolation, perfect for me.", "great purchase, excellent clarity, would buy again.", "the sound is crisp and the fit is comfortable.", "perfect for calls, great mic and solid build."]
_NCORE = ["they are okay, nothing special.", "average sound and decent build.", "works as described, no complaints, no wow.", "fine for the price, does the job.", "decent pair, arrived on time.", "standard quality, just okay."]
_XCORE = {"battery": ["terrible battery, it died after two hours.", "awful battery life, charging takes forever.", "the battery died within a month, terrible."],
          "comfort": ["very uncomfortable, it hurts my ears after an hour.", "uncomfortable and too tight, I am disappointed.", "terrible fit, uncomfortable on long use."],
          "bluetooth": ["constant bluetooth disconnect, awful pairing.", "terrible bluetooth, the connection drops every few minutes.", "pairing fails and I get a disconnect daily, worst."],
          "sound": ["awful sound, muddy and tinny.", "muddy bass and distorted vocals, disappointed.", "terrible sound, tinny and distorted."],
          "durability": ["flimsy plastic, the band cracked in a month.", "the hinge broke and it snapped, terrible build.", "cracked after a fall, flimsy and disappointing."],
          "price": ["overpriced and not worth it, disappointed.", "terrible value, overpriced for what you get.", "too expensive, not worth it, I am disappointed."]}

def generate_reviews(n=500, seed=7):
    """Synthetic, seeded, rating-labelled reviews: thousands of distinct texts, ~8% exact duplicates, ~3% junk.
    Swap for a real dataset with scripts/load_reviews.py."""
    r = random.Random(seed); out = []
    for i in range(n):
        x = r.random()
        if x < 0.55: core, s = r.choice(_PCORE), r.choice([4, 5])
        elif x < 0.72: core, s = r.choice(_NCORE), 3
        else: core, s = r.choice(_XCORE[r.choice(list(_XCORE))]), r.choice([1, 2])
        t = f"{r.choice(_OPEN)} {core} {r.choice(_TAIL)} (order {r.randint(10000, 99999)})"
        out.append({"id": f"r{i:04d}", "text": t, "rating": s})
    for _ in range(int(n * 0.08)):
        d = dict(r.choice(out)); d["id"] = f"r{len(out):04d}"; out.append(d)
    for _ in range(int(n * 0.03)):
        out.append({"id": f"r{len(out):04d}", "text": r.choice(["", "  ", "ok", "!!"]), "rating": 3})
    r.shuffle(out); return out

def norm(t: str) -> str: return re.sub(r"\s+", " ", (t or "").strip().lower())

def theme_hits(text: str) -> list:
    t = norm(text); return [k for k, ws in THEMES.items() if any(w in t for w in ws)]

def stars_to_label(s: int) -> str: return "positive" if s >= 4 else ("negative" if s <= 2 else "neutral")

# ---- Code audit domain ----
BUG_CATEGORIES = {
    "sql_injection": ["execute(", "f\"SELECT", "f'SELECT"],
    "xss": ["innerHTML", "document.write("],
    "hardcoded_secret": ["password=", "password =", "api_key", "secret=", "secret =", "token =", "token=", "aws_secret"],
    "insecure_random": ["random.random()", "random.randint("],
    "missing_auth": ["# todo: add auth", "# no auth"],
    "race_condition": ["global ", "# not thread safe"],
}

def detect_bugs(code: str) -> list[dict]:
    """Deterministic static analysis scanner that finds vulnerabilities in code."""
    lines = code.split("\n")
    found = []
    for cat, patterns in BUG_CATEGORIES.items():
        cnt = sum(1 for line in lines if any(pat.lower() in line.lower() for pat in patterns))
        if cnt > 0:
            sev = "high" if cat in ("sql_injection", "xss", "hardcoded_secret") else "medium"
            found.append({"category": cat, "count": cnt, "severity": sev})
    return found

_CODE_TEMPLATES = [
    {"file": "auth.py", "code": 'def login(user, pw):\n    cursor.execute(f"SELECT * FROM users WHERE name=\'{user}\'")\n    return cursor.fetchone()'},
    {"file": "api.py", "code": 'API_KEY = "sk-hardcoded-12345"\ndef get_data():\n    # no auth\n    return db.query("SELECT *")'},
    {"file": "render.js", "code": 'function show(data) {\n    document.getElementById("out").innerHTML = data.user_input;\n}'},
    {"file": "utils.py", "code": 'import random\ndef gen_token():\n    return str(random.random())'},
    {"file": "worker.py", "code": 'count = 0\ndef inc():\n    global count\n    # not thread safe\n    count += 1'},
    {"file": "payment.py", "code": 'def charge(amount):\n    password="admin123"\n    api_key="pk_live_abc"\n    return process(amount)'},
    {"file": "search.py", "code": 'def find(q):\n    cursor.execute(f"SELECT * FROM items WHERE name LIKE \'%{q}%\'")\n    return cursor.fetchall()'},
    {"file": "dashboard.js", "code": 'function render(html) {\n    document.write(html);\n    el.innerHTML = getUserInput();\n}'},
    {"file": "config.py", "code": 'AWS_SECRET = "wJalrXUtnFEMI"\ntoken = "ghp_xxxxxxxxxxxx"\ndef connect(): pass'},
    {"file": "scheduler.py", "code": 'import random, time\ndef jitter():\n    time.sleep(random.random())\n    # TODO: add auth\n    return run_job()'},
    {"file": "clean.py", "code": 'def sanitize(text):\n    return text.strip().lower()  # safe helper'},
    {"file": "logger.py", "code": 'import logging\ndef setup():\n    logging.basicConfig(level="INFO")\n    return logging.getLogger(__name__)'},
]

def generate_code_snippets(n=12, seed=42):
    """Synthetic code snippets with KNOWN bugs for deterministic verification.
    Each snippet has ground-truth bug annotations the verifier checks against."""
    r = random.Random(seed)
    out = []
    templates = list(_CODE_TEMPLATES)
    r.shuffle(templates)
    for i, t in enumerate(templates[:n]):
        bugs_dict = {b["category"]: b["count"] for b in detect_bugs(t["code"])}
        out.append({"id": f"f{i:03d}", "file": t["file"], "code": t["code"], "ground_truth_bugs": bugs_dict})
    return out
