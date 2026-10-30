# Benchmark (measured, reproducible)

`python scripts/benchmark.py 8` — 3 buyer policies, same 7 providers, 150 reviews, ₹20 budget. DB is reset before each arm, so no arm inherits another's reputation.

| Policy | Runs | Correct deliverable | Avg spent | Avg paid for bad work | Avg bad deliveries/task | Avg time | Bad deliveries, last 3 runs |
|---|---|---|---|---|---|---|---|
| naive | 8 | 0.0% | ₹4.2 | ₹4.2 | 3 | 1.5s | 3 |
| cheapest_verified | 8 | 100.0% | ₹8.4 | ₹0.0 | 3 | 5.6s | 3 |
| agentflow | 8 | 100.0% | ₹8.74 | ₹0.0 | 0.5 | 2.9s | 0 |

Providers: 3 of 7 are cheap fabricators (QuickClean, BargainSent, CheapReport) that undercut honest peers by 50-60%.

## What this proves
- **Pay-on-proof matters.** A buyer that pays on delivery without verification paid for 100% bad work and delivered 0% correct reports.
- **AgentFlow vs cheapest+verification:** both deliver 100% correct work and pay ₹0 for bad work (escrow + verifier protect the money in both). AgentFlow's measured edge is **learning**: bad deliveries fall from 3/task (first run) to 0/task (last 3 runs) and wall time halves, while cheapest+verification keeps re-hiring the same cheats forever (3/task every run).
- AgentFlow spends slightly MORE per task (~₹0.34): it pays honest providers instead of undercutters. That is the price of reliability. Do not claim cost savings over the verified baseline; there are none in this setup.

## What this does NOT prove
- Providers are simulated by us. The cheats are known cheat types the verifier was written to catch. An adversary who studies the verifier is out of scope.
- Synthetic, rating-labelled data (honest lexicon provider is near-perfect on it by construction). Real data needs threshold calibration (`SENT_AGREEMENT_MIN`).
- 8 runs per arm, one machine. Treat as a demonstration, not statistics.
