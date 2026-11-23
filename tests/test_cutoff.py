import io
import json
import pathlib
import subprocess
import tempfile
import unittest
import sys

from cutoff_check import audit, instant

HEADER = "observation_id,period_end_at,available_at,decision_at\n"
P = "2026-09-30T20:00:00Z"
A = "2026-11-09T13:30:00Z"
ROW = f"first,{P},{A},{A}\n"

class CutoffTests(unittest.TestCase):
    def check(self, rows):
        return audit(io.StringIO(HEADER+rows))

    def test_exact_instant_allowed(self):
        self.assertEqual(self.check(ROW)["violations"], [])

    def test_future_revision(self):
        rows = ROW + f"revision,{P},2026-11-09T13:30:00.000001Z,{A}\n"
        self.assertEqual([x["observation_id"] for x in self.check(rows)["violations"]], ["revision"])

    def test_winter_and_summer_offsets(self):
        self.assertEqual(instant("2026-11-09T08:30:00-05:00"),instant(A))
        self.assertEqual(instant("2026-07-01T08:30:00-04:00"),instant("2026-07-01T12:30:00Z"))

    def test_dst_repeated_local_clock_is_two_instants(self):
        self.assertLess(instant("2026-11-01T01:30:00-04:00"),instant("2026-11-01T01:30:00-05:00"))

    def test_duplicate_in_different_offsets(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            self.check(ROW + f"first,{P},{A},2026-11-09T08:30:00-05:00\n")

    def test_same_vintage_cannot_backdate_availability_for_earlier_decision(self):
        inconsistent = f"first,{P},2026-11-09T13:29:00Z,2026-11-09T13:29:00Z\n"
        with self.assertRaisesRegex(ValueError,"conflicting metadata"):
            self.check(ROW + inconsistent)

    def test_same_vintage_can_feed_later_decision_in_another_offset(self):
        later = f"first,{P},2026-11-09T08:30:00-05:00,2026-11-09T08:31:00-05:00\n"
        self.assertEqual(self.check(ROW+later)["violations"],[])

    def test_missing_naive_malformed_or_unknown(self):
        for bad in ("", "2026-11-09T08:30:00","2026-11-09T08:30:00+00:60","2026-11-09T08:30:00-00:00", "2026-02-30T08:30:00Z","2026-11-09T08:30:00.0000001Z"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.check(f"first,{P},{bad},{A}\n")

    def test_available_before_period_is_invalid(self):
        with self.assertRaisesRegex(ValueError,"before completed period"):
            self.check(f"first,{A},{P},{A}\n")

    def test_empty_and_bad_columns_fail(self):
        for s in (HEADER, "wrong,fields\n", HEADER+"only,three,fields\n", HEADER+'"unclosed\n'):
            with self.subTest(s=s), self.assertRaises((ValueError, __import__("csv").Error)):
                audit(io.StringIO(s))

    def test_cli_codes_and_machine_readable_outcomes(self):
        script = pathlib.Path(__file__).resolve().parents[1]/"cutoff_check.py"
        for body, code, key in ((HEADER+ROW,0,"rows"),
                (HEADER+f"late,{P},2026-11-10T13:30:00Z,{A}\n",1,"violations"),
                (HEADER,2,"input_error")):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as d:
                path = pathlib.Path(d)/"input.csv"
                path.write_text(body, encoding="utf-8")
                r = subprocess.run([sys.executable,str(script),str(path)],capture_output=True,text=True)
                self.assertEqual(r.returncode,code,r.stderr)
                self.assertIn(key,json.loads(r.stdout))

if __name__ == "__main__":
    unittest.main()
