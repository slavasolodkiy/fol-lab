<!-- ============================================================
     FOL-LAB · README
     Teenage-Engineering × Nothing × acid-glitch aesthetic
     Sovereign Agent Lab · design system v2
     ============================================================ -->

<div align="center">

<pre>
███████╗ ██████╗ ██╗
██╔════╝██╔═══██╗██║
█████╗  ██║   ██║██║
██╔══╝  ██║   ██║██║
██║     ╚██████╔╝███████╗
╚═╝      ╚═════╝ ╚══════╝
 ██╗      █████╗ ██████╗
 ██║     ██╔══██╗██╔══██╗
 ██║     ███████║██████╔╝
 ██║     ██╔══██║██╔══██╗
 ███████╗██║  ██║██████╔╝
 ╚══════╝╚═╝  ╚═╝╚═════╝
</pre>

# `FOL-LAB`

**Bounded formal policy experiments.**

> **The model drafts. Formal engines check. AI override is false.**

<img src="https://img.shields.io/badge/STATUS-M1%20public%20reference%20model-c8ff00?style=for-the-badge&labelColor=0b0d11" alt="status">
<img src="https://img.shields.io/badge/NL%20LAYER-provenance%20only-ff2d9a?style=for-the-badge&labelColor=0b0d11" alt="nl layer">
<img src="https://img.shields.io/badge/SOLVERS-SMT--LIB%20%C2%B7%20optional%20Z3%20%2F%20cvc5-35f2ff?style=for-the-badge&labelColor=0b0d11" alt="solvers">
<img src="https://img.shields.io/badge/CASES-ALLOW%20%C2%B7%20BLOCK%20%C2%B7%20CONTRADICTION-9b7bff?style=for-the-badge&labelColor=0b0d11" alt="cases">
<img src="https://img.shields.io/badge/LICENCE-MIT-00e676?style=for-the-badge&labelColor=0b0d11" alt="mit">

[Canonical page](https://www.solodkiy.cv/FOL-Qwen.html) · [Full research trail — Sovereign Agent Lab](https://www.solodkiy.cv/sovereign-agent-lab.html)

</div>

---

## ▚ STATUS

**M1 public reference model.** This is deliberately smaller than the full research ambition. It publishes the case schema, deterministic reference semantics and SMT-LIB compiler now; direct Z3/cvc5 CLI checks are available when those tools are installed. Richer natural-language translation and mutation testing remain future work.

## ▚ WHY PUBLISH THIS BEFORE IT IS “FINISHED”

The useful boundary is already executable: natural-language text is retained as provenance, but the decision path consumes only structured facts and policy. Missing solvers are reported as `NOT_INSTALLED`; results are never fabricated.

```text
 NATURAL LANGUAGE          CASE SCHEMA           REFERENCE SEMANTICS
 ┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐
 │ model-drafted│      │ structured   │      │ deterministic        │
 │ policy text  │─────►│ facts +      │─────►│ dependency-free      │
 │ provenance   │      │ policy       │      │ decision             │
 │ ONLY ──╳     │      │ ONLY ──✓     │      │ ALLOW/BLOCK/CONTRAD. │
 └──────────────┘      └──────────────┘      └──────────┬───────────┘
                                                       │
                            SMT-LIB COMPILER           ▼
                            ┌────────────────────────────────────────┐
                            │ z3 ✓ │ cvc5 ✓ │ missing → NOT_INSTALLED │
                            │ external check when available           │
                            └────────────────────────────────────────┘
```

## ▚ INCLUDED CASES

| CASE | DECISION | SHAPE |
|---|---|---|
| `A` | `ALLOW` | amount remains within the stated threshold |
| `B` | `BLOCK` | threshold crossed, enhanced review absent |
| `C` | `CONTRADICTION` | an unrestricted corridor conflicts with a simultaneous cap |

All cases are fictional. They are not statements of real law, sanctions policy or customer eligibility.

## ▚ RUN

```bash
python3 -m unittest discover -s tests -v
python3 -m fol_lab cases/case_A.json --solver all --print-smt2
```

When `z3` or `cvc5` is installed, the command runs it against the generated SMT-LIB. Otherwise the output says `NOT_INSTALLED` and still returns the dependency-free reference decision.

## ▚ WHAT THIS DEMONSTRATES

- The LLM/natural-language layer is not read at decision time.
- A bounded policy can be compiled to a solver-readable form.
- The same fixtures can be checked by a reference implementation and external solvers.
- Contradictions and blocked decisions are kept distinct.

## ▚ WHAT IS NEXT, NOT CLAIMED TODAY

- M1.5: semantic mutation operators and boundary tests.
- Natural-language-to-spec translation evaluation.
- Independent critic/model comparisons.
- Broader FOL/Datalog fragments and proof objects.
- Any claim that solver agreement equals real-world compliance.

## ▚ COLOPHON

> Formal logic did not fail: it checks consequences from encoded facts. It cannot manufacture trustworthy identity, mandate, provenance or institutional authority.

MIT licence.

<div align="center">

`THE MODEL DRAFTS · FORMAL ENGINES CHECK · AI OVERRIDE IS FALSE`

</div>
