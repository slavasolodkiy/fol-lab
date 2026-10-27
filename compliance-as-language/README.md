# Compliance as a Language

**Research milestone 0.2 · 27 October 2026**

Can a bounded, useful part of compliance be expressed as reusable concepts, evidence and explicit rules, while preserving uncertainty and human judgement? This public research milestone implements a narrow transaction-evidence gate derived from [Algorithmic Sovereignty in Digital Banking: From Regulatory Obligations to Runtime Controls](https://doi.org/10.6084/m9.figshare.33427318) (Solodkiy, 3 September 2026, printed pp. 5, 9, 12–13). The supplied paper was read in full before this revision. It already states the conceptual thesis; this milestone tests part of its proposed implementation.

The distinction at the centre is simple: **a missing fact is not a negative fact; conflicting evidence is not a clear answer**. [Version 0.2](v2/) resolves the effective policy for supplied entity, jurisdiction, product and purpose; binds evidence to an exact transaction; evaluates evidence states; and writes a reconstructable receipt with rule identifiers and named follow-up tasks. It does not screen anyone, validate documents, discover ownership, authenticate sources, infer jurisdiction, execute transactions or prove regulatory compliance.

## Explore

- [Version 0.2: executable gate, fixtures and receipt/replay](v2/), with [formal specification](v2/FORMAL.md).
- [Research note and proposed formal vocabulary](RESEARCH.md): hypothesis, formulas, boundaries and broader applications.
- [Prior work and evidence trail](CONTEXT.md): how this relates to previous FOL, evidence-gate and authority experiments, with links and source limitations.
- Initial v0.1: [semantics](PROTOTYPE.md), [code](engine.py), [synthetic examples](examples/) and [tests](tests/). Preserved as the earlier limited experiment; it did not advance the conceptual thesis.

## Try it

Requires Python 3.10+ and no third-party packages. From this directory:

```bash
python v2/v2.py evaluate v2/case.json v2/policies.json > receipt.json
python v2/v2.py replay receipt.json
python -m unittest discover -s v2 -p 'test*.py' -v
```

Version 0.2 passes 24 tests, including a bounded enumeration of all 1,024 four-state assignments of its five example facts. Tests cover policy and revocation boundaries, transaction substitution, missing/conflicting evidence and replay/tampering. The fixtures demonstrate a policy change that adds an evidence requirement without changing a model; no model runs are claimed. The tests ran in the development environment, not on the author's DGX Spark.

The evaluator is deterministic Python, not a general first-order logic solver. Its evidence is supplied by the caller; an allowed source label is not a verified credential. Hashes support comparison and replay, not source authenticity or immutable audit storage. `allow` passes only the fictional evidence gate. Interpretation, policy approval and truth of upstream assertions remain outside this model. The cases test a narrow technical possibility, not overall legal validity or real-world performance.

The parent repository's [MIT licence](../LICENSE) applies. No customer data or real transactions are used.
