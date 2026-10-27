# Compliance as a language: a bounded research note

## The question

Compliance is often presented either as a checklist of documents or as a decision to be automated. This project explores a different proposition: **some compliance work can be expressed as a reusable language of entities, relationships, claims, evidence, obligations and decisions**. That language can make a decision inspectable without pretending that all law, risk or human judgement has become an equation.

The working hypothesis is deliberately falsifiable in parts: for a defined policy and case, can we represent the relevant facts, evidence status and decision conditions clearly enough that independent reviewers can reproduce the result and identify what is missing? We also ask which parts resist that treatment. A toy implementation can show that a representation is executable; it cannot establish that a policy is lawful, complete, effective, fair, or suitable for a particular institution.

The initial v0.1 prototype in this directory is a **small synthetic experiment**, not a complete compliance language. It evaluates pre-labelled facts for a person, a company or a transaction. It does not read passports, determine beneficial ownership, screen a sanctions list, interpret law, assess source of funds, or perform due diligence.

## What the earlier paper already established

This note rests on [*Algorithmic Sovereignty in Digital Banking: From Regulatory Obligations to Runtime Controls*](https://doi.org/10.6084/m9.figshare.33427318), **Vladislav (Slava) Solodkiy, 3 September 2026**. Its full author-supplied PDF has now been read. References here use printed page numbers, one below the PDF page numbers. The paper already argues for partial executable compliance, separates legal interpretation from implementation and proof of operation, and rejects the idea that formal proofs automatically establish lawful conduct. The v0.1 note and evaluator therefore do not constitute a new statement or validation of that thesis.

On **pages 5–7**, the paper describes scoped obligation records, versioned policies, decision-level evidence, separate probabilistic/policy/evidence planes and meaningful human oversight. On **pages 7–9**, it explains the different roles and limits of formal tools and proposes typed normalisation, effective-time policy evaluation, escalation/enforcement and receipts containing input hashes, versions, reasons, actions and overrides. On **pages 12–13**, it identifies typed facts, a tested policy bundle and determining-rule receipts as a useful narrow prototype, with replay, counterexamples, reviewer agreement and controlled changes as acceptance criteria.

A [v0.2 implementation](v2/) moves a selected part of that proposal into code: a typed transaction-evidence gate, policy applicability by declared scope and effective time, a versioned policy bundle, determining rule identifiers and a reconstructable receipt/replay. It passes 24 synthetic tests, including 1,024 bounded evidence-state assignments. This is a narrower contribution than a general compliance language; it does not implement the paper's complete architecture. The synthetic provenance-label allowlist filters fixture claims only. It does not authenticate a source cryptographically, validate a document or prove an assertion's truth. Source reliability, interpretation and approval of rules remain external assertions and institutional responsibilities. The full source paper is not copied into this directory, and this revision makes no new claim about current law. See [the v0.2 specification](v2/FORMAL.md) for its distinct action/task semantics; the simplified three-outcome sketch below describes v0.1.

## A vocabulary before an answer

A useful model separates:

1. **Entities and relationships:** persons, legal entities, accounts, counterparties, ownership, control and relevant service chains.
2. **Claims:** propositions about these entities, such as “the company's registration is verified” or “the stated source of funds is supported.”
3. **Evidence and provenance:** the source, subject, observation time, validity period and what a piece of evidence supports or contradicts. A document is evidence for a claim, not automatically the claim itself.
4. **Rules and their context:** the applicable jurisdiction, institution's policy, product, relationship and point in time. A company's rule must not be silently presented as a universal legal requirement.
5. **Actions and obligations:** request more evidence, perform an investigation, escalate, review later, preserve an audit record, or make a decision. These cannot always be reduced to one yes/no answer.
6. **Judgement and accountability:** who may decide an unresolved case, what they considered, and how they can challenge or correct an earlier assessment.

The same evidence might be relevant to more than one decision, but reuse is conditional: its purpose, provenance, age, scope, access and applicability require assessment. The model must not assume that one organisation's approval automatically satisfies another's obligations.

## A bounded formal sketch

Let `p` be a scoped claim, `E` the evidence set presented for a decision, and `t` the evaluation time. Define:

```text
S+(p, E, t) := there exists e in E that supports p and is applicable at t
S−(p, E, t) := there exists e in E that refutes p and is applicable at t
```

These are claims **about evidence**, not an assertion of both `p` and `not p` in classical first-order logic. Their combination gives four states:

| Evidence in the presented set | State | Illustrative action |
| --- | --- | --- |
| Support only | Supported | Can satisfy a defined positive requirement |
| Refutation only | Refuted | Investigate or apply an explicitly specified rule |
| Both | Conflict | Review and resolve the discrepancy |
| Neither | Unknown | Request evidence or review |

For a required positive claim, `Established(p,E,t) := S+(p,E,t) AND NOT S−(p,E,t)`. Here `NOT S−` means only “no applicable refuting evidence was supplied in this finite set”; it does **not** prove that refuting evidence does not exist in the world. In particular, absent screening evidence does not mean a person is clear, and a potential screening match is not automatically a confirmed prohibition.

For a specific synthetic case `c`, let `Required(c)` be a finite set of positive claims and `H` a separately recorded policy-hard-stop claim. The v0.1 prototype's fictional decision policy is:

```text
DENY   if H is supported and not refuted in E at t
PERMIT if H is refuted and not supported in E at t,
          and every p in Required(c) is supported and not refuted
REVIEW otherwise
```

The negative hard-stop evidence means an explicit input that the selected hard stop is absent under this demonstration policy; a missing record is not enough. A conflict over a hard stop goes to review. The evaluator trusts the supplied labels: it does **not** independently verify their source, authority, quality, or legal applicability. Expired and not-yet-observed evidence are excluded at evaluation time; its intervals are `[observed_at, expires_at)`. The code is a deterministic finite evaluator inspired by these ideas, **not a general FOL theorem prover**. A policy result is not an instruction to execute a real payment or a legal opinion.

Beyond the v0.1 evaluator, a richer language could express `Request(evidence_type, case)`, `Review(case, responsible_role)` or `Reassess(case, event)`. These are proposed extensions; v0.1 emits review reasons and a generic human-action description, not an obligation workflow or a temporal-logic implementation.

## Where the language may help — and where it meets its limits

| Area | Possible formal units | What v0.1 actually does / what remains |
| --- | --- | --- |
| Identity and KYC | Subject, attribute claim, verification method, evidence provenance, expiry and discrepancy | Accepts a supplied `identity_verified` claim; authenticity, identity matching and suitability of methods remain outside the engine. |
| KYB and beneficial ownership | Legal entity, ownership/control relationships, scoped claim about verification | Accepts supplied `registration_verified` and `beneficial_owners_verified`; does not calculate ownership, resolve chains, determine applicable thresholds or detect undisclosed control. |
| KYCC | Customer, downstream customer, intermediary, responsibility, permitted evidence sharing and coverage | Not implemented. A graph can express relationships and missing links; responsibility, availability of information and privacy constraints are contextual. Avoid assuming access to an intermediary's whole customer base. |
| pKYC / ongoing monitoring | Events, review triggers, expiry, changes in ownership or customer activity | The evaluator considers observation and expiry times only. Event detection, ongoing monitoring and reassessment scheduling are future work. Here pKYC is used in the sense of perpetual/ongoing KYC, subject to confirmation of intended terminology. |
| Transactions and provenance | Sender, recipient, relevant transaction purpose, sources and supporting records, time and linked cases | Accepts supplied `customer_verified` and `source_of_funds_supported` labels; it neither verifies money flows nor proves provenance. Missing supporting records can trigger review in an appropriately defined policy. |
| AML and EDD | Risk indicators, triggers, case history, evidence requests, follow-up duties | Rules can surface specified triggers and trace evidence. Determining relevance, proportionality, suspiciousness and escalation pathways depends on policy, facts and context; none is implemented in full. |
| Sanctions | A screening result, its identity match, list/version, jurisdiction and a separately determined applicable restriction | A negative `screening_clear` input leads to review unless a separately supported, unconflicted policy hard stop takes precedence; it is not itself automatically DENY. The engine has no sanctions data or matching system. |
| KYE | Adversarial scenarios, attack indicators, provenance and challenge cases | A future research/test context, not an implemented claim or proof of malicious intent. The intended expansion of KYE should be confirmed. |

Formalisation can expose assumptions, contradictions and missing evidence. It does not eliminate the choice of what to measure, how much weight to give it, which jurisdiction or policy applies, or whether an exception is justified. Those choices themselves can sometimes be recorded as structured rules or evidence, but recording a choice does not validate it.

## What would count as a stronger result?

The v0.1 tests show the behaviour of a small model on synthetic cases, including missing, expired and conflicting evidence and the difference between a review and a confirmed policy hard stop. They test implementation against specified expectations; they do not demonstrate that real cases were assessed correctly or that the rules capture regulatory obligations.

Next validation should compare the representation and its outputs with independently reviewed, appropriately anonymised cases, including difficult exceptions; document policy ownership, source quality and jurisdiction; test changing evidence and policy versions; and measure disagreement, review burden, false assurances and reproducibility. It may reveal that a proposed rule is too coarse or that human review is required at a different point. Such a result would narrow or challenge the hypothesis rather than invalidate the whole idea by itself.

## Continuity with previous work

This experiment builds on the author's earlier public work without claiming to reproduce it:

- [FOL languages](https://www.solodkiy.cv/fol-languages.html): an earlier exploration of formal-language approaches, including illustrative payment rules. Negation by absence should not be mistaken for positive proof.
- [Nemotron + FOL](https://www.solodkiy.cv/Nemotron-FOL.html): a synthetic evidence-extraction and verification example in which readable passport fields still produced discrepancies requiring better evidence.
- [AI regulation and FOL](https://www.solodkiy.cv/AI-Regulation-FOL.html): the distinction between a proved property and the completeness or legal correctness of the formalisation.
- [Revolut FOL / sovereign](https://www.revolut.hot/revolut-FOL-sovereign.html): earlier exploration of runtime policy, evidence, escalation and human oversight.
- [Sovereign Agent Lab](https://www.solodkiy.cv/sovereign-agent-lab.html) and [AuthorityClaw](https://www.solodkiy.cv/authorityclaw.html): related lines of work on evidence and authority; their results should be assessed on their own stated test boundaries.
- [Algorithmic Sovereignty in Digital Banking: From Regulatory Obligations to Runtime Controls](https://doi.org/10.6084/m9.figshare.33427318), Vladislav (Slava) Solodkiy, 3 September 2026: full author-supplied PDF read; its conceptual and implementation requirements are integrated above. This supersedes the earlier statement that this DOI had not been read.
- Earlier DOI references [10.6084/m9.figshare.30296236](https://doi.org/10.6084/m9.figshare.30296236) and [10.6084/m9.figshare.30695645](https://doi.org/10.6084/m9.figshare.30695645) preserve the wider research trail. Their full texts remain unverified in this sprint; no detailed claims about their contents are made here.

This sprint does not settle how an AI agent compares with a company as an entity; that question is reserved for a separate investigation.
