import json, unittest
from pathlib import Path
from fol_lab.model import reference_decision, to_smt2, validate_case

ROOT = Path(__file__).resolve().parents[1]

class TestM1(unittest.TestCase):
    def cases(self):
        for path in sorted((ROOT / "cases").glob("*.json")):
            yield path, json.loads(path.read_text(encoding="utf-8"))

    def test_cases_validate(self):
        for path, case in self.cases():
            self.assertEqual(validate_case(case), [], path.name)

    def test_reference_decisions(self):
        for path, case in self.cases():
            self.assertEqual(reference_decision(case)["decision"], case["expected"]["decision"], path.name)

    def test_smt2_is_generated(self):
        for _, case in self.cases():
            text = to_smt2(case)
            self.assertIn("(check-sat)", text)
            self.assertNotIn(case["nl_input"], text)

if __name__ == "__main__":
    unittest.main(verbosity=2)
