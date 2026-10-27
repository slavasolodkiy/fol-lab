# Bounded formal specification

This specification describes the fictional policy in `policies.json`. It is a finite evidence calculus, not a claim that a law or the world's facts have been formalised. The Python implementation does not invoke a FOL/SMT solver.

## Policy and evidence applicability

For case `c` at supplied time `t`, let the matching policy set be:

```text
M(c,t) = { b in Bundle :
  b.scope = (c.entity, c.jurisdiction, c.product, c.transaction.purpose)
  and b.effective_from <= t < b.effective_to }
```

Selection succeeds only when `|M(c,t)| = 1`. Zero or multiple matching policies return `require_human_review` with `GATE-POLICY-RESOLUTION`. The engine does not infer scope or choose an arbitrary latest policy.

Given the selected policy `b`, evidence `e` for fact `p` is admissible when its shape is valid, its ID is unique within the case, its fact is required, its binding equals the entire transaction tuple, its source label is allowed for that fact by `b`, and:

```text
e.observed_at <= t < e.expires_at
and (e.revoked_at is absent or t < e.revoked_at)
```

The transaction tuple is `(id, customer, amount, currency, beneficiary, purpose)`. Amount is an exact positive decimal string. Source labels, policy ownership, revocation records and time are supplied data; this model authenticates none of them.

## Evidence states

```text
S+(p,c,b,t) <=> exists admissible e: e.fact = p and e.value = true
S-(p,c,b,t) <=> exists admissible e: e.fact = p and e.value = false

True(p)     <=> S+(p) and not S-(p)
False(p)    <=> S-(p) and not S+(p)
Conflict(p) <=> S+(p) and S-(p)
Unknown(p)  <=> not S+(p) and not S-(p)
```

Negation here tests membership in the supplied finite evidence set. `not S-` does not establish that refuting evidence cannot exist elsewhere. Conflict is a pair of recorded evidence states; the engine does not assert both `p` and classical `not p` and derive arbitrary conclusions.

## Decision and task derivation

Let `R = b.required_facts` and `H = policy_hard_stop`. Evaluate in this priority order:

| Condition | Gate result | Output task |
| --- | --- | --- |
| `True(H)` | `deny` | Record determining prohibition rule; no payment action |
| Some `p` in `R union {H}` has `Conflict(p)` | `require_human_review` | Investigate the named conflicts |
| Some `p` in `R` has `False(p)` | `require_human_review` | Investigate the named negative assertions |
| Some `p` in `R union {H}` has `Unknown(p)` | `request_information` | Collect evidence for the named missing facts |
| Otherwise | `allow` | Gate conditions satisfied; no payment action |

Consequently `allow` requires every fact in `R` to be True and `H` to be False. `screening_clear = false` alone cannot yield `deny`. A separately supplied uncontradicted hard stop has priority even if other facts conflict. The hard-stop assertion is an external conclusion; the engine does not determine sanctions applicability or legal prohibition.

Tasks are structured output records, not completed human reviews or implemented case-management workflows. After a task is completed, corrected/new evidence must be supplied and the case evaluated again. The receipt does not pretend a human saw or resolved anything.

## What is checked

Counterexample tests exercise transaction substitution, policy scope and date boundaries, conflicting/expired/revoked evidence and receipt modification. A bounded enumeration checks all 1,024 four-state assignments of the five facts in the example version-2 policy against these invariants:

```text
allow iff (all required positive facts are True and H is False)
deny iff H is True
Conflict(H) implies neither allow nor deny
```

This is a finite implementation check under this example policy, not a proof of general FOL validity, legal fidelity, real-world evidence quality, fairness, source authenticity or operational safety.

## Replay boundary

A receipt contains snapshots of the case and bundle, the selected policy, rule IDs, determining evidence and output. Canonical SHA-256 hashes make comparisons reproducible; replay recomputes both the hashes and the decision. Hash equality is not a signature, proof of origin or immutable storage. A party that replaces all inputs, results and hashes can manufacture another internally consistent receipt.
