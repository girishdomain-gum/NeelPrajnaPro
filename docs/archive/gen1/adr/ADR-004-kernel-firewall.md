# ADR-004 — Domain-Blind Kernel with Mechanical Firewall

**Status:** Accepted · 2026-07-24 · Owner: Architecture (frozen in v1.1)

## Decision
`qrf/kernel/**` contains no trading vocabulary and may not import
`qrf/trading/**`. Enforced by a CI test (AST import scan + forbidden
identifier tokens). Physical package extraction is deferred until a
second domain exists.

## Reason
The honesty rules are the scientific method, not house policy; keeping
them domain-blind makes them harder to bend on a disappointing trading
week. Deferring extraction avoids baking trading assumptions into
"general" code — abstractions are earned from the second example.

## Alternatives rejected
- Immediate two-package split: premature abstraction from one instance.
- Convention without CI: conventions decay; the firewall must be a test.

## Consequences
`tests/test_kernel_firewall.py` is a Sprint-1 deliverable and a
permanent CI gate. IVF applies the same mechanism (ivf/ never imports
qrf).
