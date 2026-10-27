# Executable evidence-policy example

Run with Python 3.10 or newer; no external libraries:

```sh
python engine.py examples/person_permit.json
python engine.py examples/company_review.json
python engine.py examples/transaction_expired_review.json
python engine.py examples/transaction_hard_stop.json
python -m unittest discover -s tests -v
```

All inputs are invented. The programme demonstrates one fictional policy for three types of case; it does not encode a jurisdiction's legal requirements, conduct screening, establish identity, authenticate evidence, or determine who is a beneficial owner. `customer_verified` is an input assertion, not proof that a complete KYC/KYB chain exists. `source` is a recorded string: no trust, identity, authenticity or accuracy checks are performed. A production application needs safeguards and domain/legal review.

Each required fact can be `true`, `false`, `unknown` or `conflict`. Evidence counts only between its observation time (inclusive) and expiry time (exclusive). Contradictory current claims produce `conflict`; missing, expired and future claims do not become `false`. Input errors halt the run without a decision. Outputs list evidence identifiers, excluded items and reasons. A supplied `as_of` allows repeatable evaluation; it is not checked against the real clock.

`policy_hard_stop=true` means a separately determined, applicable prohibition is already asserted by an external process. An uncontradicted current assertion produces the fictional outcome `deny`; the evaluator cannot validate the asserted conclusion. `screening_clear=false` alone produces `review`, not denial. An absent or contradictory hard-stop assertion requires `review`. `permit` requires supported positive values for all other required facts and a supported `false` for the hard stop. All remaining conditions mean `review`. The output is a policy result for human governance, not a real-world authorization or legal decision. This is a small deliberately explicit rules evaluator, not an implementation of a FOL theorem prover.
