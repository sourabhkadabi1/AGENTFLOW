"""Run a task on YOUR OWN review CSV (e.g. a public Amazon/Flipkart dataset). Needs columns for review text and 1-5 star rating.
  python scripts/load_reviews.py reviews.csv --text review_body --rating star_rating --limit 500 --budget 20
The verifier uses the star rating as ground truth, so a rating column is required."""
import argparse, csv, httpx, json, time
ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--text", default="text"); ap.add_argument("--rating", default="rating")
ap.add_argument("--limit", type=int, default=500); ap.add_argument("--budget", type=float, default=20); ap.add_argument("--base", default="http://127.0.0.1:8000"); a = ap.parse_args()
rows = []
with open(a.csv, newline="", encoding="utf-8") as f:
    for i, r in enumerate(csv.DictReader(f)):
        try: rows.append({"id": f"u{i:05d}", "text": r[a.text], "rating": int(float(r[a.rating]))})
        except (KeyError, ValueError): continue
        if len(rows) >= a.limit: break
print(f"loaded {len(rows)} reviews")
r = httpx.post(a.base + "/tasks", headers={"x-api-key": "dev-user-key"}, json={"goal": "Analyze these customer reviews and produce a report", "budget_inr": a.budget, "reviews": rows})
r.raise_for_status(); tid = r.json()["task_id"]
while (t := httpx.get(f"{a.base}/tasks/{tid}").json())["status"] not in ("COMPLETED", "FAILED"): time.sleep(1)
print(t["status"], "spent paise:", t["spent"]); print(json.dumps(t["result"].get("final", t["result"]), indent=2)[:2500])
