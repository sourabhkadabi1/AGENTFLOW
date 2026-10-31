"""Independent verifier. Pure deterministic code. Treats provider output as UNTRUSTED. Never calls an LLM.
Ground truth comes from the INPUT data (ratings, ids, text), not from the provider's own claims."""
import json
from collections import Counter
from common.domain import norm, theme_hits, stars_to_label, THEMES

MAX_OUTPUT_BYTES = 2_000_000
import os
SENT_AGREEMENT_MIN = float(os.getenv("SENT_AGREEMENT_MIN", "0.75"))   # lower (e.g. 0.65) for real-world data; calibrate BEFORE the demo
THEME_TOL = 0.25

def verify(capability: str, task_input: dict, output, *, constraints: list[str] | None = None) -> dict:
    """Returns {passed, score, checks:[{name,ok,detail}], reason}"""
    checks = []
    def chk(name, ok, detail=""): checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:160]}); return ok
    try:
        if not chk("output_is_object", isinstance(output, dict), type(output).__name__): return _fin(checks)
        if not chk("size_limit", len(json.dumps(output)) <= MAX_OUTPUT_BYTES): return _fin(checks)
        {"clean_data": _clean, "sentiment": _sent, "report": _report}[capability](task_input, output, chk)
        # customer constraints checked AFTER deterministic checks (only on report — final customer-facing output)
        if constraints and capability == "report":
            _check_constraints(output, constraints, chk)
    except Exception as e:  # malformed structure must fail closed, never pass
        chk("no_exception", False, f"{type(e).__name__}: {e}")
    return _fin(checks)

def _fin(checks):
    ok = all(c["ok"] for c in checks)
    failed = [c["name"] for c in checks if not c["ok"]]
    return {"passed": ok, "score": round(sum(c["ok"] for c in checks) / max(1, len(checks)), 3), "checks": checks,
            "reason": "all_checks_passed" if ok else "failed:" + ",".join(failed)}

def _clean(inp, out, chk):
    src = {r["id"]: r for r in inp["reviews"]}
    rows = out.get("reviews")
    if not chk("has_reviews_list", isinstance(rows, list)): return
    ids = [r.get("id") for r in rows]
    chk("no_fabricated_ids", all(i in src for i in ids), f"{sum(i not in src for i in ids)} unknown ids")
    chk("no_duplicate_ids", len(ids) == len(set(ids)))
    srcnorm = {norm(r["text"]) for r in src.values()}
    chk("text_comes_from_input", all(norm(r.get("text", "")) in srcnorm for r in rows))
    chk("id_text_binding", all(norm(r.get("text", "")) == norm(src[r["id"]]["text"]) for r in rows if r.get("id") in src))
    texts = [norm(r.get("text", "")) for r in rows]
    chk("no_duplicate_text", len(texts) == len(set(texts)), f"{len(texts)-len(set(texts))} dup texts")
    chk("no_junk_left", all(len(t) >= 5 for t in texts))
    expected = len({norm(r["text"]) for r in src.values() if len(norm(r["text"])) >= 5})
    chk("completeness", len(rows) == expected, f"got {len(rows)} expected {expected}")
    chk("rating_preserved", all(r.get("rating") == src[r["id"]]["rating"] for r in rows if r.get("id") in src))

def _sent(inp, out, chk):
    src = {r["id"]: r for r in inp["reviews"]}
    labels = out.get("labels"); themes = out.get("complaint_themes")
    if not chk("has_labels_and_themes", isinstance(labels, list) and isinstance(themes, dict)): return
    ids = [l.get("id") for l in labels]
    chk("covers_every_review_once", sorted(ids) == sorted(src), f"{len(ids)} vs {len(src)}")
    chk("valid_label_values", all(l.get("label") in ("positive", "neutral", "negative") for l in labels))
    expected_score = {"positive": 1, "neutral": 0, "negative": -1}
    chk("score_matches_label", all(l.get("score", expected_score.get(l.get("label"))) == expected_score.get(l.get("label")) for l in labels))
    agree = sum(1 for l in labels if l.get("id") in src and l.get("label") == stars_to_label(src[l["id"]]["rating"])) / max(1, len(labels))
    chk("agreement_with_star_ratings", agree >= SENT_AGREEMENT_MIN, f"{agree:.2f} (min {SENT_AGREEMENT_MIN})")
    mine = Counter(t for r in src.values() if stars_to_label(r["rating"]) == "negative" for t in theme_hits(r["text"]))
    chk("known_themes_only", set(themes) <= set(THEMES), set(themes) - set(THEMES))
    ok = all(abs(themes.get(t, 0) - mine.get(t, 0)) <= max(2, THEME_TOL * max(1, mine.get(t, 0))) for t in set(mine) | set(themes))
    chk("theme_counts_match_recount", ok, f"claimed={dict(themes)} recount={dict(mine)}")

def _report(inp, out, chk):
    """inp = {'labels':[...], 'themes':{...}} are the already-VERIFIED sentiment results. Every number must reconcile."""
    labels = Counter(l["label"] for l in inp["labels"]); n = sum(labels.values())
    br = out.get("sentiment_breakdown"); tc = out.get("top_complaints"); rec = out.get("recommendations"); summ = out.get("summary")
    if not chk("has_required_sections", isinstance(br, dict) and isinstance(tc, list) and isinstance(rec, list) and isinstance(summ, str)): return
    chk("breakdown_counts_exact", all(br.get(k) == labels.get(k, 0) for k in ("positive", "neutral", "negative")), f"claimed={br} actual={dict(labels)}")
    chk("breakdown_total_matches", sum(br.get(k, 0) for k in ("positive", "neutral", "negative")) == n)
    truth = sorted(inp["themes"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    got = [(c.get("theme"), c.get("count")) for c in tc]
    chk("top_complaints_match_ranking", got == truth, f"claimed={got} actual={truth}")
    chk("five_recommendations", len(rec) == 5 and all(isinstance(r, str) and len(r) > 10 for r in rec))
    chk("distinct_recommendations", isinstance(rec, list) and len({norm(r) for r in rec if isinstance(r, str)}) == 5)
    chk("summary_nonempty", 20 <= len(summ) <= 2000)
    nar = out.get("narrative")
    if nar is not None:     # LLM prose is untrusted: every number it states must exist in the verified data
        if chk("narrative_bounded_string", isinstance(nar, str) and 20 <= len(nar) <= 1200):
            import re
            allowed = {0, 1, 2, 3, 4, 5, n, *labels.values(), *inp["themes"].values()}
            for k in ("positive", "neutral", "negative"):
                pct = 100 * labels.get(k, 0) / max(1, n); allowed |= {pct, round(pct), round(pct, 1)}
            bad = [x for x in re.findall(r"\d+(?:\.\d+)?", nar) if not any(abs(float(x) - a) <= 0.051 for a in allowed)]
            chk("narrative_numbers_grounded", not bad, f"ungrounded numbers: {bad[:5]}")


def _check_constraints(output: dict, constraints: list[str], chk):
    """Deterministic customer-constraint checks on the final report. No LLM — keyword substring matching only.
    Each constraint is checked against the full serialized output text (summary, recommendations, narrative, themes)."""
    searchable = json.dumps(output).lower()
    for i, con in enumerate(constraints):
        raw = con.strip()
        words = raw.lower().split()
        if not words: continue
        # parse "minimum N recommendations" / "at least N recommendations"
        if len(words) >= 3 and words[0] in ("minimum", "at") and (words[1].isdigit() or (words[0] == "at" and len(words) >= 4 and words[1] == "least" and words[2].isdigit())):
            count = int(words[1]) if words[0] == "minimum" else int(words[2])
            target = " ".join(words[2:] if words[0] == "minimum" else words[3:])
            if "recommendation" in target:
                actual = len(output.get("recommendations", []))
                chk(f"constraint_{i+1}", actual >= count, f"'{raw}' — found {actual}, need ≥{count}")
                continue
            elif "complaint" in target or "theme" in target:
                actual = len(output.get("top_complaints", []))
                chk(f"constraint_{i+1}", actual >= count, f"'{raw}' — found {actual}, need ≥{count}")
                continue

        # natural language prefix stripping: "must mention battery", "must include bluetooth", etc.
        clean = raw.lower()
        for prefix in ("must mention ", "must include ", "must have ", "should mention ", "should include ", "should cover ", "requires ", "require ", "includes "):
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()
                break

        matched = (clean in searchable) or (all(w in searchable for w in clean.split() if len(w) > 3) if len(clean.split()) > 1 else False)
        chk(f"constraint_{i+1}", bool(matched), f"'{raw}' — not found in report output")
