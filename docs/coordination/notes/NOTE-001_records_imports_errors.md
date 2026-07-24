# NOTE-001 · FYI · Sprint 1 · 2026-07-24
Author: developer (claude-code)
Refs: Blueprint §3 (Import rules), §6 (errors.py), ARCH-001

## Discovery (no reply needed)
Blueprint §3 lists two import rules that lightly tension for the records layer:

- "`kernel.records` imports nothing from qrf (leaf)."
- errors live at `qrf/kernel/errors.py` (i.e. `qrf.kernel.errors`), and
  `store.py`/`schemas.py` must raise `SchemaViolation`, `UnknownParentError`,
  `UnknownRecordError`, `LedgerIntegrityError` (Blueprint §4.1 / §6).

To raise those typed errors, `qrf.kernel.records.*` imports
`qrf.kernel.errors`. Taken literally, that is an import "from qrf", so the
"leaf" phrasing is slightly imprecise.

## Interpretation applied
I read "leaf" as: records depends on no *other kernel subsystem* (instruments,
battery, belief, protocol, …) and on no domain code — keeping it foundational.
The shared error taxonomy is itself a stdlib-only leaf module, so
`records → errors` is a benign, acyclic dependency and the only `qrf` import in
the records layer.

This is consistent with the *enforced* contract: the Sprint-1 kernel firewall
test (tests/test_kernel_firewall.py) forbids `qrf.trading` imports and domain
vocabulary tokens only — it does not forbid intra-kernel imports, and the tree
passes. No architecture change requested; flagging in case the Architect wants
to tighten the Blueprint wording (e.g. "records imports no kernel subsystem
beyond `errors`").
