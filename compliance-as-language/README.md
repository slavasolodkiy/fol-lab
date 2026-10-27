# Compliance as a Language

**Research milestone 0.1 · 27 October 2026**

Can a bounded, useful part of compliance be expressed as reusable concepts, evidence and explicit rules, while preserving uncertainty and human judgement? This public research prototype explores that question with fictional person onboarding, company onboarding and transaction-evidence cases. It is an experiment, not a complete compliance system or a claim about legal requirements.

The distinction at the centre is simple: **a missing fact is not a negative fact; conflicting evidence is not a clear answer**. An evaluation can return `permit`, `review` or `deny` under one invented policy. It does not screen anyone, validate documents, discover ownership, authenticate sources, infer jurisdiction, execute transactions or prove regulatory compliance.

## Explore

- [Research note and proposed formal vocabulary](RESEARCH.md): hypothesis, formulas, boundaries and broader applications.
- [Prior work and evidence trail](CONTEXT.md): how this relates to previous FOL, evidence-gate and authority experiments, with links and source limitations.
- [Prototype semantics and execution](PROTOTYPE.md): decisions, evidence records, examples and tests.
- [Code](engine.py), [synthetic examples](examples/) and [tests](tests/).

## Try it

Requires Python 3.10+ and no third-party packages. From this directory:

```bash
python engine.py examples/company_review.json
python engine.py examples/transaction_hard_stop.json
python -m unittest discover -s tests -v
```

The evaluator is deterministic Python, not a general first-order logic solver. Its evidence is supplied by the caller; a source is just a label, not a verified credential. Conclusions are only as sound as the selected policy, inputs and modelling assumptions. The cases test a narrow technical possibility, not overall legal validity or real-world performance.

The parent repository's [MIT licence](../LICENSE) applies. No customer data or real transactions are used.
