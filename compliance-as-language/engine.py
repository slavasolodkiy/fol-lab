"""Illustrative evidence evaluator. It is not a legal rule or production system."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# These are fictional policy choices, not universal regulatory requirements.
REQUIRED = {
    "person_onboarding": ("identity_verified", "screening_clear", "policy_hard_stop"),
    "company_onboarding": ("registration_verified", "beneficial_owners_verified", "screening_clear", "policy_hard_stop"),
    "transaction": ("customer_verified", "source_of_funds_supported", "screening_clear", "policy_hard_stop"),
}


def timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO 8601 string with a timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value}") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return result.astimezone(timezone.utc)


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one case as of a supplied time; invalid input raises ValueError.

    Evidence must explicitly identify the case subject and carry an observation and
    expiry time. Both truth values in the current window produce conflict; no current
    evidence produces unknown. This deliberately does not infer that missing is false.
    """
    kind = case.get("case_type")
    if kind not in REQUIRED:
        raise ValueError("unknown case_type")
    subject = case.get("subject")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject must be a non-empty string")
    now = timestamp(case.get("as_of"))
    evidence = case.get("evidence")
    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list")
    seen_ids: set[str] = set()
    current: dict[str, list[dict[str, Any]]] = {name: [] for name in REQUIRED[kind]}
    excluded: list[dict[str, str]] = []
    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError("each evidence item must be an object")
        eid = item.get("id")
        if not isinstance(eid, str) or not eid.strip() or eid in seen_ids:
            raise ValueError("evidence ids must be non-empty and unique")
        seen_ids.add(eid)
        fact = item.get("fact")
        if fact not in current:
            raise ValueError(f"unsupported fact for {kind}: {fact}")
        if item.get("subject") != subject:
            raise ValueError(f"evidence {eid} has wrong subject")
        if type(item.get("value")) is not bool:
            raise ValueError(f"evidence {eid} value must be boolean")
        if not isinstance(item.get("source"), str) or not item["source"].strip():
            raise ValueError(f"evidence {eid} needs a source")
        observed, expires = timestamp(item.get("observed_at")), timestamp(item.get("expires_at"))
        if expires <= observed:
            raise ValueError(f"evidence {eid} must expire after observation")
        if now < observed:
            excluded.append({"id": eid, "reason": "not_yet_observed"})
        elif now >= expires:
            excluded.append({"id": eid, "reason": "expired"})
        else:
            current[fact].append(item)

    facts: dict[str, dict[str, Any]] = {}
    for fact, items in current.items():
        values = {item["value"] for item in items}
        state = "unknown" if not values else "conflict" if len(values) == 2 else "true" if True in values else "false"
        facts[fact] = {"state": state, "evidence_ids": [item["id"] for item in items]}
    # A hard stop is a separately recorded policy conclusion, not a screening hit.
    # The prototype does not independently validate the source or that conclusion.
    hard_stop = facts["policy_hard_stop"]["state"]
    if hard_stop == "true":
        decision = "deny"
        reasons = ["explicit_current_policy_hard_stop"]
    elif hard_stop == "false" and all(item["state"] == "true" for name, item in facts.items() if name != "policy_hard_stop"):
        decision = "permit"
        reasons = ["all_required_facts_supported_and_no_hard_stop"]
    else:
        decision = "review"
        reasons = [f"{name}:{item['state']}" for name, item in facts.items()
                   if (name == "policy_hard_stop" and item["state"] != "false")
                   or (name != "policy_hard_stop" and item["state"] != "true")]
    return {"case_type": kind, "subject": subject, "as_of": now.isoformat(),
            "decision": decision, "reasons": reasons, "facts": facts, "excluded_evidence": excluded,
            "human_action": "Investigate and resolve evidence before a decision" if decision == "review" else "Policy result; human governance still applies"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="path to one JSON case")
    args = parser.parse_args()
    try:
        case = json.loads(args.case.read_text(encoding="utf-8"))
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        print(json.dumps(evaluate(case), indent=2, ensure_ascii=False))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Invalid case: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
