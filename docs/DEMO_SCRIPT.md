# Demo script (3.5 minutes). Rehearse until it works 3 times in a row. Fresh start: `./scripts/run_all.sh`, wait for 7 healthy providers.

**0:00 Problem (20s).** "Agents can think but can't safely buy. Who finds the provider, who checks the work, who pays only for good work?"

**0:20 Run 1, cold start (60s).** Budget ₹20, priority Balanced, policy AgentFlow, press Run. Narrate the tape as it moves:
- "Seven independent processes, each with its own key. Three of them are cheap and cheat. The buyer doesn't know yet: all reputations start equal, so price decides."
- Cheap provider wins the bid → contract signed, credits held in escrow → delivery → **verifier FAIL** (point at the exact failed checks: fabricated IDs, wrong totals) → **refund** → re-bid → honest provider → PASS → SETTLED.
- "That happened at every stage. The user paid ₹0 for bad work and did nothing."

**1:20 Learning (30s).** Point at the Providers table: "QuickClean claims 99%. Verified: 40%. The buyer only reads the verified column." Press Run again: "Run 2 goes straight to the honest providers. No failures."

**1:50 Why verification matters (30s).** Set policy to *Naive cheapest, pay on delivery*, Run. "Same providers. It pays for garbage and delivers a wrong report." Show the benchmark panel: correct deliverables 0% vs 100%.

**2:20 Failure injection (30s).** Set CleanCo to *timeout*, Run: "A provider hangs after signing. Escrow returned, next provider hired." Set it back to honest.

**(Optional, only with WITH_LLM=1 and a real key tested)** Set GemReport to *hallucinate* and the other report providers to *garbage*: the verifier rejects the invented "73%". "LLM output is untrusted."

**2:50 Tamper evidence (30s).** Click *Tamper*: "I just edited one old record directly in the database." Header turns red: "audit BROKEN at #N". "Every bid, verdict and ledger entry is hash-chained and the ledger reconciles against it."

**3:20 Close (10s).** "Not a wrapper, an economy with guardrails: payment only on proof, trust earned from verdicts, recovery inside a hard budget."

**If the browser dies:** `python scripts/demo_cli.py` tells the same story in the terminal. **If everything dies:** play the backup video.
**Never say:** "real payments", "blockchain", "unhackable", "production ready".
