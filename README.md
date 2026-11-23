# Cutoff Check

An offline, dependency-free Python check for point-in-time data contracts. It flags a completed-period observation or revision used before its declared availability, even when all train/test rows are in chronological order.

Example: September's release can arrive in November. A model deciding on November 9 at 13:30 UTC may use a release made available at 13:30 UTC under the inclusive rule, but not the revision at 13:31 UTC. A September period-end date is not evidence of September availability.

## Run

Python 3.10+. No API keys, network, database or package installation needed.

```sh
python3 cutoff_check.py examples/mixed.csv
python3 -m unittest discover -s tests -v
```

The mixed example intentionally exits **1**. All examples are synthetic.

| Exit | Meaning |
|---|---|
| 0 | All declared observations pass the availability check. |
| 1 | At least one observation arrived after its decision cutoff. |
| 2 | Input error. Do not treat the report as a pass. |

The four case-sensitive CSV headers are `observation_id,period_end_at,available_at,decision_at`. The observation ID should identify a series, period and vintage in your input, independently of the decision timestamp. `available_at` is the earliest evidenced availability to **your** system: if both release and ingestion timing matter, supply the later of those two times, not a vendor's most recent update. Use UTC or timestamps with known explicit offsets; leap seconds, naive clocks and unknown offsets are rejected. Equal timestamps pass; impose any trading or processing lag when constructing your input. This release checks observations of completed periods, not forecasts. Duplicate ID plus decision instant, or conflicting period/availability for one ID, fails closed. For different ingestion systems use separate audits rather than mixing incompatible availability for the same ID. A JSON report is emitted to stdout.

**Scope.** This checks supplied metadata, not whether it is truthful or complete. It does not select vintages, detect every form of leakage, certify backtests, execute trades, or produce alpha estimates. A pass means only that the supplied rows meet this rule. Compared with time-ordered splitters or strategy-level lookahead detectors, this acts earlier, at the per-observation input boundary. Use the methods together, not as substitutes.

[Guía breve en español](README.es.md) · [Apache-2.0](LICENSE), proposed for this release.
