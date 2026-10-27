# A versioned transaction-evidence gate

This synthetic example implements one bounded continuation of *Algorithmic Sovereignty in Digital Banking: From Regulatory Obligations to Runtime Controls* (Solodkiy, 3 September 2026, DOI [10.6084/m9.figshare.33427318](https://doi.org/10.6084/m9.figshare.33427318)), especially printed pages 5, 9 and 13: a typed fact interface, a tested policy bundle and a reconstructable decision receipt.

The [formal specification](FORMAL.md) defines evidence admissibility, four states, rule priority and replay boundaries. The independent test suite has 24 passing tests, including 1,024 bounded evidence-state assignments. These are synthetic implementation checks, not real-case or legal validation.

It evaluates whether supplied, pre-labelled evidence satisfies a fictional transaction-evidence policy. It does not decide that a payment is lawful or authorised, independently establish facts, run an AI model, authenticate a source, or execute a payment. `allow` means only that this gate's recorded requirements passed.

## Run

Python 3.10+; no third-party libraries. From this directory:

```sh
python v2.py evaluate case.json policies.json > receipt.json
python v2.py replay receipt.json
python v2.py evaluate case_missing_purpose.json policies.json
python v2.py evaluate case_before_change.json policies.json
python -m unittest discover -s . -p 'test*.py' -v
```

The complete fixture returns `allow` under policy version 2. Removing the purpose evidence returns `request_information`. The earlier-dated case uses version 1, whose fictional requirements did not include purpose evidence, and returns `allow`. These are demonstration choices, not a claim about any legal threshold or current UK law. `DEMO-UK` is a deliberately fictional scope identifier.

## Policy resolution

The engine requires exactly one policy matching the supplied regulated entity, jurisdiction, product, transaction purpose and evaluation time. Time intervals are `[effective_from, effective_to)`. An absent or ambiguous policy yields `require_human_review`, with the resolution rule identifier and a `resolve_policy` obligation. Invalid case or policy configuration raises an input error; it never becomes an approval.

A policy records its identifier, version, source reference, fictional interpretation status, control owner, required positive facts, accepted source labels per fact and determining rule IDs. The engine accepts fictional policies only. These are caller-controlled records, not authenticated proof that the owner approved the policy. Source names cannot be declared acceptable by an evidence record: the allowlist comes from the selected policy.

## Bound evidence

Each evidence record must bind to all six transaction fields: identifier, customer, exact decimal-string amount, uppercase three-letter currency, beneficiary and purpose. Amounts must be positive, finite decimal strings; booleans and floating-point numbers are rejected. Strings are compared exactly, so `1250.0` does not substitute for `1250.00`. These deliberate constraints favour visible mismatch over silent equivalence.

Evidence must carry a unique ID, a supported predicate, a Boolean value, an accepted source label, observation time and expiry time. An optional `revoked_at` excludes the record at and after revocation. Evidence is usable from observation (inclusive) to expiry (exclusive). Invalid, duplicated, untrusted-label, mismatched, future, expired and revoked evidence is excluded with a reason. Both copies of a duplicate ID are excluded. Unrecognised or not-required facts are not used.

The resulting fact states are `true`, `false`, `conflict` and `unknown`: both values mean conflict, and no accepted current value means unknown. `true` means only that the supplied set contains uncontested accepted support; it is not an assertion of verified real-world truth.

## Decision and obligations

Priority is explicit:

1. Uncontested `policy_hard_stop=true` yields `deny`, even if other facts are incomplete or conflicting. This means an external process already asserted a prohibition; this engine does not determine its legal applicability.
2. Otherwise, a conflict in a required fact or the hard-stop assertion yields `require_human_review` and fact-specific investigation obligations.
3. A negative required positive fact, including `screening_clear=false`, yields `require_human_review`, not denial.
4. Missing facts yield `request_information`, with named evidence-collection obligations.
5. All required positive facts true plus an explicit uncontested hard-stop false yield `allow`.

Obligations are output records, not an implemented case-management workflow. `action_executed` remains false in every outcome. No human override is implemented.

## Receipt and replay

The receipt embeds the case and policy-bundle snapshots, selected policy metadata, hashes of the case/bundle/selected policy, fact states, evidence IDs, excluded-record reasons, determining rule IDs, obligations and evaluator schema version. It is deterministic for identical JSON data; dictionary key order does not change its canonical hashes.

`replay` checks the receipt digest and re-evaluates the embedded snapshots, requiring exact equality with the recorded receipt. It detects changed recorded bytes or mismatched results; it does not verify the original source's identity or that the snapshot represents the real historic state. A party able to replace all data and recompute hashes can forge a receipt. Signed provenance, trusted time, immutable storage, policy approval, clock control, evidence truth and governance remain external. Real customer evidence should not be copied into public receipts; these fixtures are synthetic.
