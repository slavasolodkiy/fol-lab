import unittest
from copy import deepcopy
from engine import evaluate

NOW = "2026-10-27T12:00:00Z"

def ev(eid, fact, value=True, **changes):
    item = {"id": eid, "subject": "case-1", "fact": fact, "value": value,
            "source": "synthetic-source", "observed_at": "2026-10-01T00:00:00Z",
            "expires_at": "2026-11-01T00:00:00Z"}
    item.update(changes)
    return item

def case(kind, evidence):
    return {"case_type": kind, "subject": "case-1", "as_of": NOW, "evidence": evidence + [ev("no-stop", "policy_hard_stop", False)]}

class EvidenceRules(unittest.TestCase):
    def test_person_permit_requires_all_current_facts(self):
        c = case("person_onboarding", [ev("i", "identity_verified"), ev("s", "screening_clear")])
        self.assertEqual(evaluate(c)["decision"], "permit")
        c["evidence"].pop(1)
        self.assertEqual(evaluate(c)["decision"], "review")
        self.assertEqual(evaluate(c)["facts"]["screening_clear"]["state"], "unknown")

    def test_company_missing_owners_is_review(self):
        c = case("company_onboarding", [ev("r", "registration_verified"), ev("s", "screening_clear")])
        result = evaluate(c)
        self.assertEqual(result["decision"], "review")
        self.assertIn("beneficial_owners_verified:unknown", result["reasons"])

    def test_transaction_expiry_is_not_evidence_of_false(self):
        c = case("transaction", [ev("c", "customer_verified"), ev("f", "source_of_funds_supported", expires_at=NOW), ev("s", "screening_clear")])
        result = evaluate(c)
        self.assertEqual(result["decision"], "review")
        self.assertEqual(result["facts"]["source_of_funds_supported"]["state"], "unknown")
        self.assertEqual(result["excluded_evidence"], [{"id": "f", "reason": "expired"}])

    def test_contradiction_requires_review_and_provenance(self):
        c = case("person_onboarding", [ev("a", "identity_verified"), ev("b", "identity_verified", False), ev("s", "screening_clear")])
        result = evaluate(c)
        self.assertEqual(result["decision"], "review")
        self.assertEqual(result["facts"]["identity_verified"], {"state": "conflict", "evidence_ids": ["a", "b"]})

    def test_conflicting_screening_is_review_not_deny(self):
        c = case("person_onboarding", [ev("i", "identity_verified"), ev("s1", "screening_clear"), ev("s2", "screening_clear", False)])
        self.assertEqual(evaluate(c)["decision"], "review")

    def test_uncontested_explicit_hard_stop_denies_even_with_missing_other_evidence(self):
        c = case("person_onboarding", [ev("stop", "policy_hard_stop", True)])
        c["evidence"] = c["evidence"][:1]
        self.assertEqual(evaluate(c)["decision"], "deny")

    def test_screening_failure_alone_is_review(self):
        c = case("person_onboarding", [ev("i", "identity_verified"), ev("s", "screening_clear", False)])
        self.assertEqual(evaluate(c)["decision"], "review")

    def test_conflict_and_unknown_hard_stop_are_review(self):
        c = case("person_onboarding", [ev("i", "identity_verified"), ev("s", "screening_clear")])
        c["evidence"].append(ev("stop", "policy_hard_stop", True))
        self.assertEqual(evaluate(c)["decision"], "review")
        c["evidence"] = c["evidence"][:2]
        self.assertEqual(evaluate(c)["decision"], "review")

    def test_future_evidence_excluded(self):
        c = case("person_onboarding", [ev("i", "identity_verified", observed_at="2026-10-28T00:00:00Z"), ev("s", "screening_clear")])
        result = evaluate(c)
        self.assertEqual(result["decision"], "review")
        self.assertEqual(result["excluded_evidence"][0]["reason"], "not_yet_observed")

    def test_bad_inputs_are_errors_not_decisions(self):
        base = case("person_onboarding", [ev("i", "identity_verified")])
        cases = []
        c = deepcopy(base); c["evidence"][0]["subject"] = "another-person"; cases.append(c)
        c = deepcopy(base); c["evidence"][0]["value"] = "true"; cases.append(c)
        c = deepcopy(base); c["evidence"][0]["expires_at"] = "2026-10-01T00:00:00Z"; cases.append(c)
        c = deepcopy(base); c["as_of"] = "2026-10-27T12:00:00"; cases.append(c)
        c = deepcopy(base); c["evidence"].append(deepcopy(c["evidence"][0])); cases.append(c)
        for c in cases:
            with self.subTest(c=c), self.assertRaises(ValueError):
                evaluate(c)

if __name__ == "__main__":
    unittest.main()
