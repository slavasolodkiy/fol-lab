"""Synthetic, versioned transaction evidence gate; no legal or source authentication.

Run: python v2.py evaluate case.json policies.json
     python v2.py replay receipt.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from typing import Any

VERSION = "cal-transaction-gate-0.2"
POSITIVE_FACTS = {"customer_verified", "purpose_supported", "source_of_funds_supported", "screening_clear"}
HARD_STOP = "policy_hard_stop"
TRANSACTION_FIELDS = ("id", "customer", "amount", "currency", "beneficiary", "purpose")
SCOPE_FIELDS = ("regulated_entity", "jurisdiction", "product", "purpose")
RULE_FIELDS = ("deny", "conflict", "negative", "missing", "allow")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp needs a timezone")
    return result.astimezone(timezone.utc)


def text_fields(obj: Any, fields: tuple[str, ...], label: str) -> None:
    if not isinstance(obj, dict):
        raise ValueError(f"{label} must be an object")
    for field in fields:
        if not isinstance(obj.get(field), str) or not obj[field].strip():
            raise ValueError(f"{label}.{field} must be a nonempty string")


def validate_case(case: Any) -> datetime:
    if not isinstance(case, dict):
        raise ValueError("case must be an object")
    now = timestamp(case.get("as_of"))
    text_fields(case.get("context"), SCOPE_FIELDS[:3], "context")
    tx = case.get("transaction")
    text_fields(tx, TRANSACTION_FIELDS, "transaction")
    # Exact decimal strings avoid binary floating point and normalisation surprises.
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", tx["amount"]):
        raise ValueError("transaction.amount must be a positive decimal string")
    try:
        if Decimal(tx["amount"]) <= 0:
            raise ValueError("transaction.amount must be positive")
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc
    if not re.fullmatch(r"[A-Z]{3}", tx["currency"]):
        raise ValueError("currency must be three uppercase letters")
    if not isinstance(case.get("evidence"), list):
        raise ValueError("evidence must be a list")
    return now


def validate_policies(policies: Any) -> None:
    if not isinstance(policies, list):
        raise ValueError("policies must be a list")
    for policy in policies:
        text_fields(policy, ("policy_id", "version", "source_ref", "control_owner"), "policy")
        if policy.get("interpretation_status") != "fictional":
            raise ValueError("this research gate accepts fictional policies only")
        text_fields(policy.get("scope"), SCOPE_FIELDS, "policy.scope")
        start, end = timestamp(policy.get("effective_from")), timestamp(policy.get("effective_to"))
        if end <= start:
            raise ValueError("policy effective_to must follow effective_from")
        required = policy.get("required_facts")
        if not isinstance(required, list) or not required or any(not isinstance(f, str) or f not in POSITIVE_FACTS for f in required) or len(set(required)) != len(required):
            raise ValueError("required_facts must be unique supported positive facts")
        sources = policy.get("sources")
        if not isinstance(sources, dict):
            raise ValueError("policy.sources must be an object")
        for fact in [*required, HARD_STOP]:
            names = sources.get(fact)
            if not isinstance(names, list) or not names or any(not isinstance(s, str) or not s.strip() for s in names) or len(set(names)) != len(names):
                raise ValueError(f"policy.sources.{fact} must be a nonempty unique source list")
        text_fields(policy.get("rule_ids"), RULE_FIELDS, "rule_ids")
        if len(set(policy["rule_ids"][r] for r in RULE_FIELDS)) != len(RULE_FIELDS):
            raise ValueError("policy rule IDs must be unique")


def applicable(policy: dict[str, Any], case: dict[str, Any], now: datetime) -> bool:
    scope = {**case["context"], "purpose": case["transaction"]["purpose"]}
    return all(scope.get(f) == policy["scope"][f] for f in SCOPE_FIELDS) and timestamp(policy["effective_from"]) <= now < timestamp(policy["effective_to"])


def run_policy(case: dict[str, Any], policy: dict[str, Any], now: datetime) -> dict[str, Any]:
    required = policy["required_facts"]
    fact_names = [*required, HARD_STOP]
    accepted: dict[str, list[dict[str, Any]]] = {fact: [] for fact in fact_names}
    excluded: list[dict[str, Any]] = []
    ids = Counter(e["id"] for e in case["evidence"] if isinstance(e, dict) and isinstance(e.get("id"), str))
    for index, item in enumerate(case["evidence"]):
        eid = item.get("id") if isinstance(item, dict) else None
        reason = None
        if not isinstance(item, dict):
            reason = "not_an_object"
        elif not isinstance(eid, str) or not eid.strip():
            reason = "invalid_evidence_id"
        elif ids[eid] > 1:
            reason = "duplicate_evidence_id"
        elif not isinstance(item.get("fact"), str) or item["fact"] not in accepted:
            reason = "unsupported_or_not_required_fact"
        elif type(item.get("value")) is not bool:
            reason = "value_must_be_boolean"
        elif not isinstance(item.get("binding"), dict) or set(item["binding"]) != set(TRANSACTION_FIELDS) or any(item["binding"].get(k) != case["transaction"][k] for k in TRANSACTION_FIELDS):
            reason = "transaction_binding_mismatch"
        elif item.get("source") not in policy["sources"][item["fact"]]:
            reason = "source_not_allowed"
        else:
            try:
                observed, expires = timestamp(item.get("observed_at")), timestamp(item.get("expires_at"))
                revoked = timestamp(item["revoked_at"]) if "revoked_at" in item else None
                if expires <= observed:
                    reason = "invalid_evidence_window"
                elif revoked is not None and revoked < observed:
                    reason = "invalid_revocation_time"
                elif now < observed:
                    reason = "not_yet_observed"
                elif now >= expires:
                    reason = "expired"
                elif revoked is not None and now >= revoked:
                    reason = "revoked"
            except (ValueError, TypeError):
                reason = "invalid_evidence_time"
        if reason:
            excluded.append({"index": index, "id": eid, "reason": reason})
        else:
            accepted[item["fact"]].append(item)
    states = {}
    for name, items in accepted.items():
        values = {i["value"] for i in items}
        state = "unknown" if not values else "conflict" if len(values) == 2 else "true" if True in values else "false"
        states[name] = {"state": state, "evidence_ids": [i["id"] for i in items]}
    stop = states[HARD_STOP]["state"]
    conflicts = [name for name, item in states.items() if item["state"] == "conflict"]
    negatives = [name for name in required if states[name]["state"] == "false"]
    missing = [name for name, item in states.items() if item["state"] == "unknown"]
    if stop == "true":
        decision, rule, reasons, obligations = "deny", "deny", ["explicit_current_policy_hard_stop"], []
    elif conflicts:
        decision, rule, reasons = "require_human_review", "conflict", [f"conflict:{n}" for n in conflicts]
        obligations = [{"action": "investigate", "fact": n, "owner": policy["control_owner"]} for n in conflicts]
    elif negatives:
        decision, rule, reasons = "require_human_review", "negative", [f"negative:{n}" for n in negatives]
        obligations = [{"action": "investigate", "fact": n, "owner": policy["control_owner"]} for n in negatives]
    elif missing:
        decision, rule, reasons = "request_information", "missing", [f"missing:{n}" for n in missing]
        obligations = [{"action": "collect_evidence", "fact": n, "owner": policy["control_owner"]} for n in missing]
    else:
        decision, rule, reasons, obligations = "allow", "allow", ["required_facts_supported_and_hard_stop_explicitly_false"], []
    return {"decision": decision, "rule_ids": [policy["rule_ids"][rule]], "reasons": reasons,
            "obligations": obligations, "facts": states, "excluded_evidence": excluded,
            "action_executed": False}


def evaluate(case: dict[str, Any], policies: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate synthetic inputs; malformed case/policy raises ValueError.

    Malformed evidence is excluded with a reason. Source identities, assertions and
    policy ownership are recorded labels, not authenticated. Supplied time is not
    checked against a trusted clock. 'allow' only passes this evidence gate.
    """
    now = validate_case(case)
    validate_policies(policies)
    matches = [p for p in policies if applicable(p, case, now)]
    selected = matches[0] if len(matches) == 1 else None
    if selected:
        result = run_policy(case, selected, now)
    else:
        reason = "policy_not_found" if not matches else "ambiguous_applicable_policy"
        result = {"decision": "require_human_review", "rule_ids": ["GATE-POLICY-RESOLUTION"],
                  "reasons": [reason], "obligations": [{"action": "resolve_policy", "owner": "policy_governance"}],
                  "facts": {}, "excluded_evidence": [], "action_executed": False}
    receipt = {"schema_version": VERSION,
               "as_of": now.isoformat(),
               "transaction_id": case["transaction"]["id"],
               "policy": {"id": selected["policy_id"], "version": selected["version"],
                          "source_ref": selected["source_ref"], "interpretation_status": selected["interpretation_status"],
                          "control_owner": selected["control_owner"]} if selected else None,
               "hashes": {"case": digest(case), "policy_bundle": digest(policies),
                          "selected_policy": digest(selected) if selected else None},
               "snapshots": {"case": deepcopy(case), "policies": deepcopy(policies)},
               "result": result}
    receipt["receipt_hash"] = digest(receipt)
    return receipt


def replay(receipt: dict[str, Any]) -> bool:
    """Detect changed recorded data and reproduce result, not prove authenticity.

    Anyone who can replace the whole receipt and recompute hashes can forge it;
    signatures, immutable storage and independent authority checks are absent.
    """
    if not isinstance(receipt, dict) or receipt.get("schema_version") != VERSION:
        raise ValueError("unsupported receipt")
    stored = deepcopy(receipt)
    expected_hash = stored.pop("receipt_hash", None)
    if digest(stored) != expected_hash:
        raise ValueError("receipt digest mismatch")
    try:
        repeated = evaluate(receipt["snapshots"]["case"], receipt["snapshots"]["policies"])
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid receipt snapshots") from exc
    if canonical(repeated) != canonical(receipt):
        raise ValueError("receipt does not match evaluator replay")
    return True


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON constant: {value}")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("evaluate")
    check.add_argument("case", type=Path)
    check.add_argument("policies", type=Path)
    again = commands.add_parser("replay")
    again.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        output = evaluate(load(args.case), load(args.policies)) if args.command == "evaluate" else {"replay_verified": replay(load(args.receipt)), "authenticity_verified": False}
        print(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Invalid input: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
