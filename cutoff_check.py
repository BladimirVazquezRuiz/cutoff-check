"""Strict offline check of observation availability at a decision cutoff."""
import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone

FIELDS = ("observation_id", "period_end_at", "available_at", "decision_at")
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", re.ASCII)
RULE_VERSION = "1"

def instant(s):
    if not isinstance(s, str) or not TS.fullmatch(s) or s.endswith("-00:00"):
        raise ValueError("expected RFC3339 timestamp with known explicit UTC offset")
    if not s.endswith("Z") and int(s[-2:]) > 59:
        raise ValueError("invalid offset minutes")
    value = datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    return value.astimezone(timezone.utc)

def audit(stream):
    reader = csv.reader(stream, strict=True)
    if tuple(next(reader, ())) != FIELDS:
        raise ValueError("expected header: " + ",".join(FIELDS))
    seen, vintages, problems = set(), {}, []
    rows = 0
    for row in reader:
        line = reader.line_num
        rows += 1
        if len(row) != len(FIELDS):
            raise ValueError(f"line {line}: wrong column count")
        oid, raw_period, raw_available, raw_decision = row
        if not oid or oid != oid.strip():
            raise ValueError(f"line {line}: blank or whitespace-padded observation_id")
        try:
            period, available, decision = (instant(t) for t in (raw_period, raw_available, raw_decision))
        except (ValueError, OverflowError) as e:
            raise ValueError(f"line {line}: {e}") from e
        key = (oid, decision)
        if key in seen:
            raise ValueError(f"line {line}: duplicate observation_id and decision instant")
        seen.add(key)
        if oid in vintages and vintages[oid] != (period, available):
            raise ValueError(f"line {line}: conflicting metadata for the same observation_id")
        vintages[oid] = (period, available)
        if available < period:
            raise ValueError(f"line {line}: availability before completed period")
        if available > decision:
            problems.append({"line":line, "observation_id":oid,
                             "reason":"available_after_decision",
                             "available_at_utc":available.isoformat(),
                             "decision_at_utc":decision.isoformat()})
    if not rows:
        raise ValueError("no observations; refusing a vacuous pass")
    return {"rule_version":RULE_VERSION,"rows":rows,"violations":problems}

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", help="local UTF-8 CSV to audit")
    args = p.parse_args(argv)
    try:
        with open(args.csv, encoding="utf-8", newline="") as f:
            report = audit(f)
    except (ValueError, OSError, csv.Error) as e:
        print(json.dumps({"input_error": str(e)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return int(bool(report["violations"]))

if __name__ == "__main__":
    sys.exit(main())
