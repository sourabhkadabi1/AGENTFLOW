"""Independent provider agents. Prices in paise. `default_mode` is how the provider behaves unless the demo injects a failure.
claimed_reliability is the provider's own marketing: the buyer IGNORES it (shown on the dashboard next to verified reliability)."""
PROFILES = {
    "cleanco":   dict(name="CleanCo",      capability="clean_data", base_price=200, min_price=160, eta_ms=900,  claimed=0.97, default_mode="honest",    port=9101),
    "quickclean":dict(name="QuickClean",   capability="clean_data", base_price=100, min_price=80,  eta_ms=500,  claimed=0.99, default_mode="fabricate", port=9102),
    "sentipro":  dict(name="SentiPro",     capability="sentiment",  base_price=500, min_price=420, eta_ms=1500, claimed=0.96, default_mode="honest",    port=9103),
    "bargainsent":dict(name="BargainSent", capability="sentiment",  base_price=200, min_price=150, eta_ms=800,  claimed=0.99, default_mode="random",    port=9104),
    "slowsent":  dict(name="SlowSent",     capability="sentiment",  base_price=300, min_price=260, eta_ms=4500, claimed=0.90, default_mode="honest",    port=9105),
    "reportwriter":dict(name="ReportWriter",capability="report",    base_price=300, min_price=250, eta_ms=1200, claimed=0.95, default_mode="honest",    port=9106),
    "gemreport": dict(name="GemReport",    capability="report",     base_price=400, min_price=350, eta_ms=2500, claimed=0.95, default_mode="honest",    port=9108, llm=True),   # optional: WITH_LLM=1
    "cheapreport":dict(name="CheapReport", capability="report",     base_price=100, min_price=90,  eta_ms=600,  claimed=0.99, default_mode="fabricate", port=9107),
}
MODES = ["honest", "fabricate", "random", "timeout", "garbage", "hallucinate", "lazy_echo", "subtle_drift"]   # hallucinate: correct numbers + an invented statistic in the LLM narrative
