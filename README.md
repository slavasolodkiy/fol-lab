# FOL-Lab — bounded formal policy experiments

> **The model drafts. Formal engines check. AI override is false.**

**Status: M1 public reference model.** This is deliberately smaller than the full research ambition. It publishes the case schema, deterministic reference semantics and SMT-LIB compiler now; direct Z3/cvc5 CLI checks are available when those tools are installed. Richer natural-language translation and mutation testing remain future work.

- [Canonical page](https://www.solodkiy.cv/FOL-Qwen.html)
- [Full research trail — Sovereign Agent Lab](https://www.solodkiy.cv/sovereign-agent-lab.html)

## Why publish this before it is “finished”

The useful boundary is already executable: natural-language text is retained as provenance, but the decision path consumes only structured facts and policy. Missing solvers are reported as `NOT_INSTALLED`; results are never fabricated.

## Included cases

- Case A — `ALLOW`: amount remains within the stated threshold.
- Case B — `BLOCK`: threshold crossed, enhanced review absent.
- Case C — `CONTRADICTION`: an unrestricted corridor conflicts with a simultaneous cap.

All cases are fictional. They are not statements of real law, sanctions policy or customer eligibility.

## Run

```bash
python3 -m unittest discover -s tests -v
python3 -m fol_lab cases/case_A.json --solver all --print-smt2
```

When `z3` or `cvc5` is installed, the command runs it against the generated SMT-LIB. Otherwise the output says `NOT_INSTALLED` and still returns the dependency-free reference decision.

## What this demonstrates

- The LLM/natural-language layer is not read at decision time.
- A bounded policy can be compiled to a solver-readable form.
- The same fixtures can be checked by a reference implementation and external solvers.
- Contradictions and blocked decisions are kept distinct.

## What is next, not claimed today

- M1.5: semantic mutation operators and boundary tests.
- Natural-language-to-spec translation evaluation.
- Independent critic/model comparisons.
- Broader FOL/Datalog fragments and proof objects.
- Any claim that solver agreement equals real-world compliance.

Formal logic did not fail: it checks consequences from encoded facts. It cannot manufacture trustworthy identity, mandate, provenance or institutional authority.

MIT licence.
