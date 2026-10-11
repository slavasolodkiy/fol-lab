"""Small bounded formal-policy reference model.

This is intentionally not a general FOL theorem prover. It compiles the M1
fixtures to SMT-LIB and also provides a dependency-free reference decision.
"""
from __future__ import annotations


def validate_case(case):
    required = {"id", "nl_input", "facts", "policy", "expected"}
    errors = []
    missing = required - set(case)
    if missing:
        return [f"missing keys: {sorted(missing)}"]
    for key in ("facts", "policy", "expected"):
        if not isinstance(case[key], dict):
            errors.append(f"{key} must be an object")
    if case["expected"].get("decision") not in {"ALLOW", "BLOCK", "CONTRADICTION"}:
        errors.append("expected.decision must be ALLOW | BLOCK | CONTRADICTION")
    return errors


def reference_decision(case):
    facts = case["facts"]
    policy = case["policy"]
    if policy.get("kyc_unrestricted") and policy.get("review_threshold") is not None:
        return {"decision": "CONTRADICTION", "reason": "unrestricted corridor conflicts with threshold"}
    for name in policy.get("prohibitions", []):
        if facts.get(name):
            return {"decision": "BLOCK", "reason": f"prohibition:{name}"}
    threshold = policy.get("review_threshold")
    if threshold is not None and facts.get("amount", 0) > threshold and not facts.get("enhanced_review_complete", False):
        return {"decision": "BLOCK", "reason": f"threshold:{threshold}:review_missing"}
    return {"decision": "ALLOW", "reason": "within_mandate"}


def to_smt2(case):
    """Compile a fixture to a small QF_LIA/Bool consistency query.

    SAT means the facts satisfy the encoded policy. UNSAT means either a
    blocking fact or an explicit policy contradiction is present.
    """
    facts = case["facts"]
    policy = case["policy"]
    lines = ["(set-logic QF_LIA)"]
    lines += [
        "(declare-const amount Int)",
        "(declare-const enhanced_review_complete Bool)",
        "(declare-const bob_sanctioned Bool)",
        "(declare-const kyc_unrestricted Bool)",
    ]
    lines.append(f"(assert (= amount {int(facts.get('amount', 0))}))")
    lines.append(f"(assert (= enhanced_review_complete {'true' if facts.get('enhanced_review_complete', False) else 'false'}))")
    lines.append(f"(assert (= bob_sanctioned {'true' if facts.get('bob_sanctioned', False) else 'false'}))")
    lines.append(f"(assert (= kyc_unrestricted {'true' if policy.get('kyc_unrestricted', False) else 'false'}))")
    for prohibited in policy.get("prohibitions", []):
        if prohibited == "bob_sanctioned":
            lines.append("(assert (not bob_sanctioned))")
    threshold = policy.get("review_threshold")
    if threshold is not None:
        lines.append(f"(assert (=> (> amount {int(threshold)}) enhanced_review_complete))")
        lines.append("(assert (not kyc_unrestricted))")
    lines += ["(check-sat)", "(exit)"]
    return "\n".join(lines) + "\n"
