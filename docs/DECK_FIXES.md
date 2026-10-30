# Your submission deck vs what is actually built. Fix these or a judge will find them.

| Deck says | Reality | Fix |
|---|---|---|
| Slide 7: "Dashboard: Next.js + Tailwind" | Single dependency-free HTML file served by FastAPI, SSE | Change the slide (preferred: zero build risk at the venue) or build Next.js |
| Slide 7: "Agents: separate FastAPI processes, buyer agent plus providers" | Providers are separate processes. Buyer and verifier run in the gateway process with their own keys | Say "providers are independent processes; buyer and verifier have separate identities" |
| Slide 5: "Each request carries an Ed25519 signature" | True buyer↔provider (requests and responses) and provider registration. User→gateway uses an API key | Say "all agent-to-agent calls" |
| Slide 7/8: "Gemini API with deterministic fallback" | Now true: goal interpretation + optional GemReport provider whose prose the verifier fact-checks; verified only against a mock, run Part 4 of the runbook with a real key before claiming it | Say "Gemini-backed provider, output fact-checked by the verifier" only after your real-key test |
| Slide 7: "Public product-review dataset" | Synthetic seeded data by default | Run `load_reviews.py` on a real dataset and name it, or say "synthetic" |
| Slide 4: competitor matrix | "Our reading of public documentation" and unverified here | Re-check x402, AP2, A2A, MCP, Fetch.ai against current docs the day before |
| Slide 9: "Not copied in 1 hour" | Marketing | Replace with the measured benchmark line |
| Slide 9/DEMO: any "saves money" claim | Benchmark: no cost savings vs cheapest+verification; savings are vs paying for bad work, plus time and fewer bad calls | Use the numbers in docs/BENCHMARK.md only |
| Slide 2: team placeholders | Empty | Fill in |
| Slide 3: "micro-payments: card fees swallow tiny jobs" | Motivation, not something this build proves | Keep as motivation, don't present as a result |
