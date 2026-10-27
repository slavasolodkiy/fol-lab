"""Independent counterexamples for the fictional transaction-evidence gate."""
from copy import deepcopy
import hashlib
from itertools import product
import json
import unittest

try:
    from v2.v2 import evaluate, replay
except ModuleNotFoundError:
    from v2 import evaluate, replay


BEFORE = "2026-10-27T11:59:59Z"
BOUNDARY = "2026-10-27T12:00:00Z"


def policy(version="1", start="2026-10-01T00:00:00Z", end=BOUNDARY):
    facts = ["customer_verified", "source_of_funds_supported", "screening_clear"]
    if version == "2":
        facts.append("purpose_supported")
    return {
        "policy_id": "FICTIONAL-EVIDENCE",
        "version": version,
        "source_ref": "Synthetic test policy; not a statement of law",
        "interpretation_status": "fictional",
        "control_owner": "fictional-compliance-team",
        "scope": {"regulated_entity": "bank-demo", "jurisdiction": "DEMO", "product": "transfer", "purpose": "invoice"},
        "effective_from": start,
        "effective_to": end,
        "required_facts": facts,
        "sources": {fact: ["approved-test-reviewer"] for fact in facts + ["policy_hard_stop"]},
        "rule_ids": {key: "FICTIONAL-V" + version + "-" + key.upper() for key in ["deny", "conflict", "negative", "missing", "allow"]},
    }


def evidence(case, fact, value=True, eid=None):
    return {
        "id": eid or fact,
        "fact": fact,
        "value": value,
        "source": "approved-test-reviewer",
        "observed_at": "2026-10-01T00:00:00Z",
        "expires_at": "2026-11-01T00:00:00Z",
        "binding": deepcopy(case["transaction"]),
    }


def case():
    result = {
        "as_of": BEFORE,
        "context": {"regulated_entity": "bank-demo", "jurisdiction": "DEMO", "product": "transfer"},
        "transaction": {"id": "tx-demo-1", "customer": "customer-demo", "amount": "100.00", "currency": "GBP", "beneficiary": "supplier-demo", "purpose": "invoice"},
        "evidence": [],
    }
    result["evidence"] = [evidence(result, fact) for fact in ["customer_verified", "source_of_funds_supported", "screening_clear"]]
    result["evidence"].append(evidence(result, "policy_hard_stop", False))
    return result


class TransactionGateCounterexamples(unittest.TestCase):
    def decide(self, item, policies=None):
        return evaluate(item, [policy()] if policies is None else policies)["result"]["decision"]

    def test_complete_current_scoped_test_evidence_permits(self):
        self.assertEqual(self.decide(case()), "allow")

    def test_missing_fact_requests_review(self):
        item = case()
        item["evidence"] = [e for e in item["evidence"] if e["fact"] != "source_of_funds_supported"]
        self.assertEqual(self.decide(item), "request_information")

    def test_expiry_is_exclusive_and_observation_is_not_retroactive(self):
        item = case()
        item["evidence"][0]["expires_at"] = BEFORE
        self.assertEqual(self.decide(item), "request_information")
        item = case()
        item["evidence"][0]["observed_at"] = BOUNDARY
        self.assertEqual(self.decide(item), "request_information")

    def test_conflicting_current_fact_cannot_permit(self):
        item = case()
        item["evidence"].append(evidence(item, "source_of_funds_supported", False, "contradictory-funds"))
        self.assertEqual(self.decide(item), "require_human_review")

    def test_negative_screening_is_not_a_confirmed_policy_prohibition(self):
        item = case()
        next(e for e in item["evidence"] if e["fact"] == "screening_clear")["value"] = False
        self.assertEqual(self.decide(item), "require_human_review")

    def test_separate_uncontested_hard_stop_denies(self):
        item = case()
        item["evidence"] = [evidence(item, "policy_hard_stop", True)]
        self.assertEqual(self.decide(item), "deny")

    def test_conflicting_hard_stop_is_review(self):
        item = case()
        item["evidence"].append(evidence(item, "policy_hard_stop", True, "contradictory-stop"))
        self.assertEqual(self.decide(item), "require_human_review")

    def test_reusing_attestations_for_changed_transaction_cannot_permit(self):
        changes = {"id": "different-id", "customer": "other-customer", "amount": "101.00", "currency": "EUR", "beneficiary": "other-supplier", "purpose": "gift"}
        for field, value in changes.items():
            with self.subTest(field=field):
                item = case()
                item["transaction"][field] = value
                self.assertNotEqual(self.decide(item), "allow")

    def test_unapproved_source_cannot_satisfy_required_fact(self):
        item = case()
        item["evidence"][0]["source"] = "unknown-model-output"
        self.assertEqual(self.decide(item), "request_information")

    def test_unapproved_prohibition_cannot_create_denial(self):
        item = case()
        forged = evidence(item, "policy_hard_stop", True, "unapproved-prohibition")
        forged["source"] = "unknown-model-output"
        item["evidence"].append(forged)
        self.assertNotEqual(self.decide(item), "deny")

    def test_revocation_takes_effect_at_boundary(self):
        item = case()
        item["evidence"][0]["revoked_at"] = BEFORE
        self.assertEqual(self.decide(item), "request_information")
        item["evidence"][0]["revoked_at"] = BOUNDARY
        self.assertEqual(self.decide(item), "allow")

    def test_policy_scope_does_not_silently_fall_back(self):
        for key in ["regulated_entity", "jurisdiction", "product"]:
            with self.subTest(key=key):
                item = case()
                item["context"][key] = "different-scope"
                self.assertNotEqual(self.decide(item), "allow")

    def test_policy_gap_and_ambiguity_cannot_permit(self):
        self.assertNotEqual(self.decide(case(), []), "allow")
        first = policy()
        overlapping = policy("2", "2026-10-01T00:00:00Z", "2026-11-01T00:00:00Z")
        self.assertNotEqual(self.decide(case(), [first, overlapping]), "allow")

    def test_effective_policy_boundary_changes_requirements(self):
        policies = [policy(), policy("2", BOUNDARY, "2026-11-01T00:00:00Z")]
        item = case()
        self.assertEqual(self.decide(item, policies), "allow")
        item["as_of"] = BOUNDARY
        self.assertEqual(self.decide(item, policies), "request_information")
        item["evidence"].append(evidence(item, "purpose_supported"))
        self.assertEqual(self.decide(item, policies), "allow")

    def test_receipt_replays_and_detects_changed_output(self):
        receipt = evaluate(case(), [policy()])
        self.assertTrue(replay(receipt))
        tampered = deepcopy(receipt)
        tampered["result"]["decision"] = "deny"
        with self.assertRaises(ValueError):
            replay(tampered)

    def test_recomputed_digest_does_not_hide_inconsistent_decision(self):
        # Integrity hashing is not authenticity. Replay still needs to recompute
        # the result rather than merely accepting a freshly calculated digest.
        tampered = evaluate(case(), [policy()])
        tampered["result"]["decision"] = "deny"
        del tampered["receipt_hash"]
        encoded = json.dumps(tampered, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        tampered["receipt_hash"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        with self.assertRaises(ValueError):
            replay(tampered)

    def test_receipt_detects_snapshot_or_policy_substitution(self):
        original = evaluate(case(), [policy()])
        tampered = deepcopy(original)
        tampered["snapshots"]["case"]["transaction"]["amount"] = "999.00"
        with self.assertRaises(ValueError):
            replay(tampered)
        tampered = deepcopy(original)
        tampered["snapshots"]["policies"][0]["control_owner"] = "different-owner"
        with self.assertRaises(ValueError):
            replay(tampered)

    def test_mapping_order_does_not_change_reproducible_receipt(self):
        item = case()
        first = evaluate(item, [policy()])
        reordered = {k: deepcopy(v) for k, v in reversed(list(item.items()))}
        second = evaluate(reordered, [policy()])
        self.assertEqual(first, second)

    def test_malformed_evidence_is_excluded_and_does_not_satisfy_fact(self):
        for field, value in [("fact", []), ("value", "true"), ("source", None), ("observed_at", "not-a-date")]:
            with self.subTest(field=field):
                item = case()
                item["evidence"][0][field] = value
                receipt = evaluate(item, [policy()])
                self.assertEqual(receipt["result"]["decision"], "request_information")
                self.assertEqual(receipt["result"]["facts"]["customer_verified"]["state"], "unknown")
                self.assertEqual(len(receipt["result"]["excluded_evidence"]), 1)

    def test_duplicate_evidence_ids_cannot_mask_conflicting_records(self):
        item = case()
        duplicate = deepcopy(item["evidence"][0])
        duplicate["value"] = False
        item["evidence"].append(duplicate)
        receipt = evaluate(item, [policy()])
        self.assertEqual(receipt["result"]["decision"], "request_information")
        self.assertEqual(receipt["result"]["facts"]["customer_verified"]["state"], "unknown")
        self.assertEqual(len(receipt["result"]["excluded_evidence"]), 2)

    def test_receipt_records_determining_rule_and_actionable_missing_fact(self):
        item = case()
        item["evidence"] = [e for e in item["evidence"] if e["fact"] != "source_of_funds_supported"]
        receipt = evaluate(item, [policy()])
        self.assertEqual(receipt["result"]["rule_ids"], ["FICTIONAL-V1-MISSING"])
        self.assertIn({"action": "collect_evidence", "fact": "source_of_funds_supported", "owner": "fictional-compliance-team"}, receipt["result"]["obligations"])
        self.assertFalse(receipt["result"]["action_executed"])

    def test_receipt_list_mutation_is_detected(self):
        receipt = evaluate(case(), [policy()])
        receipt["snapshots"]["case"]["evidence"].pop()
        with self.assertRaises(ValueError):
            replay(receipt)

    def test_amount_and_time_input_tricks_are_not_accepted_as_facts(self):
        for value in [True, 100, "NaN", "Infinity", "-1.00"]:
            with self.subTest(amount=value):
                item = case()
                item["transaction"]["amount"] = value
                with self.assertRaises(ValueError):
                    evaluate(item, [policy()])
        item = case()
        item["as_of"] = "2026-10-27T11:59:59"
        with self.assertRaises(ValueError):
            evaluate(item, [policy()])

    def test_bounded_invariants_over_1024_four_state_valuations(self):
        # Exhaustive only for this finite synthetic policy. This is neither a
        # general FOL proof nor a validation of real-world legal requirements.
        positive = ["customer_verified", "source_of_funds_supported", "screening_clear", "purpose_supported"]
        names = positive + ["policy_hard_stop"]
        values = {"true": [True], "false": [False], "unknown": [], "conflict": [True, False]}
        selected_policy = policy("2", "2026-10-01T00:00:00Z", "2026-11-01T00:00:00Z")
        checked = 0
        for states in product(values, repeat=len(names)):
            assignment = dict(zip(names, states))
            item = case()
            item["evidence"] = [
                evidence(item, name, value, name + "-" + str(index))
                for name in names
                for index, value in enumerate(values[assignment[name]])
            ]
            result = evaluate(item, [selected_policy])["result"]
            expected_allow = assignment["policy_hard_stop"] == "false" and all(assignment[name] == "true" for name in positive)
            expected_deny = assignment["policy_hard_stop"] == "true"
            with self.subTest(assignment=assignment):
                self.assertEqual(result["decision"] == "allow", expected_allow)
                self.assertEqual(result["decision"] == "deny", expected_deny)
                if assignment["policy_hard_stop"] == "conflict":
                    self.assertNotIn(result["decision"], ["allow", "deny"])
                self.assertEqual({name: fact["state"] for name, fact in result["facts"].items()}, assignment)
                self.assertFalse(result["action_executed"])
            checked += 1
        self.assertEqual(checked, 1024)


if __name__ == "__main__":
    unittest.main()
