import csv
import io
import pathlib
import unittest
from cutoff_check import FIELDS, audit, instant

def evaluate(*row):
    f = io.StringIO()
    w = csv.writer(f)
    w.writerow(FIELDS)
    w.writerow(row)
    f.seek(0)
    try:
        return "late" if audit(f)["violations"] else "on_time"
    except ValueError:
        return "invalid"

class CorpusTests(unittest.TestCase):
    def test_frozen_synthetic_cases(self):
        fixture = pathlib.Path(__file__).with_name("synthetic_cases.csv")
        with fixture.open(newline="", encoding="utf-8") as f:
            cases = list(csv.DictReader(f))
        self.assertEqual(len(cases), 30)
        self.assertEqual(len({c["case"] for c in cases}),30)
        for c in cases:
            with self.subTest(case=c["case"]):
                self.assertEqual(evaluate(c["case"],*(c[x] for x in FIELDS[1:])),c["expected"])

if __name__ == "__main__":
    unittest.main()
