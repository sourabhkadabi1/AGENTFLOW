"""Shared constants, dataset generator and reference lexicons. The verifier's checks use rating ground truth, not the providers' lexicon."""
import random, re, math

CAPABILITIES = ["clean_data", "sentiment", "report"]
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
