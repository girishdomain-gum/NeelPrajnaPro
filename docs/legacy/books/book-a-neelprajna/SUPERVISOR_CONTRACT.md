# SUPERVISOR CONTRACT — v1.1 (np_supervisor.py 1.1.0)

Owner-approved constitution for the trust anchor. Approve this, then the
code freezes. "Frozen" means: bound by this contract.

> **Amendment v1.1, adopted 2026-07-27 after signature (owner-endorsed).**
> Two rules added: firmware-style evolution (§5) and the ADR requirement
> (§7 step 0). Both make change *harder*, never easier, so the v1
> signature stands. Any future amendment that loosens a rule requires a
> fresh signature.

## 1. Responsibilities

The supervisor does exactly five things:

1. **Lifecycle** — start the runner, observe it, restart it after exit,
   stop it on a FAILED state, stop it on owner interrupt.
2. **Observation** — process alive, exit code, restart count, crash loop,
   heartbeat age, health-report age, free disk, orphaned work at startup.
3. **Adjudication** — combine those into `HEALTHY` / `DEGRADED` /
   `FAILED` / `STOPPED`.
4. **Publication** — write `supervisor.health.json` atomically each cycle.
5. **Attestation** — record its own SHA-256 and its config's SHA-256 in
   every report.

## 2. Non-responsibilities

It never: knows what an experiment is · knows MT5, MetaEditor, a broker,
a symbol or NeelPrajna · reads or writes job files · interprets the
*contents* of the runner's health report beyond §4 · deletes anything ·
compiles, deploys or tests · touches an account · decides scientific
questions.

## 3. Guarantees (invariants)

- **G-1 Silence is negative.** A missing or stale health report is
  DEGRADED, never "unknown".
- **G-2 Fail closed.** Free disk below the configured floor, or a crash
  loop, prevents the runner from being started at all.
- **G-3 Never guess a schema.** A health report whose `health_schema` is
  not the supported value is refused, not interpreted (§4).
- **G-4 Atomic publication.** Reports are written to `.tmp` and renamed.
  A reader never sees a half-written report.
- **G-5 Non-destructive.** Orphaned work found at startup is reported and
  left exactly where it is.
- **G-6 Attested.** Every report carries the supervisor and config hashes.
  Tamper-evident, not tamper-proof — this is stated, not implied.
- **G-7 Traceable.** Every negative verdict names the failing check, its
  observed value and its threshold. Never a bare "unhealthy".

## 4. Stable interfaces

**A. Config file** (owner-owned). Required keys: `runner_cmd`,
`health_dir`, `heartbeat_path`, `health_report_path`, `work_dirs`,
`min_free_gb`. Optional with defaults: `poll_secs`,
`max_heartbeat_age_s`, `max_health_age_s`, `restart_backoff_s`,
`crash_loop_count`, `crash_loop_window_s`. Missing required key →
refuse to start, exit 2.

**B. Runner health report — schema 1.** The *only* code-level coupling
between the two trust domains. The runner must write JSON containing:

```
{"health_schema": 1, "status": "HEALTHY" | "DEGRADED" | "FAILED", ...}
```

Everything else in that file is free for the runner to change without
consulting the supervisor. Adding a field is not a schema change; changing
the meaning of `status`, or of the two keys above, is — and requires
`health_schema: 2`, which the supervisor will refuse until the owner
upgrades it deliberately.

**C. Supervisor health report — schema 1.** Fields: `health_schema`,
`supervisor_version`, `supervisor_sha256`, `config_sha256`, `config_path`,
`time`, `state`, `runner_pid`, `runner_last_exit`, `restarts_recorded`,
`orphans_at_startup`, `stop_reason`, `checks[]`. Fields may be added;
existing fields never change meaning inside a schema version.

**D. Deployment.** The supervisor knows nothing about deployment. The
runner adopts new code by **exiting on its own file-hash change**; the
supervisor only observes an exit and restarts. This is deliberate and is
the mechanism by which runner updates need no human.

## 5. Versioning policy

- **Evolve it like firmware, not like software.** Valid reasons to change
  it: a security issue, a defect, or an operating-system/environment
  change. Not valid: "we thought of a better way." A supervisor that runs
  untouched for months is the system working, not the system neglected.
- Patch/minor: behaviour unchanged or strictly stricter. Contract stands.
- Any change to §3 or §4 requires a new contract version and owner
  approval **before** the code changes.
- The supervisor's hash changing without a matching contract version is,
  by definition, an incident.

## 6. Freeze criterion (the test that matters)

> **No future NeelPrajna feature may require a change to
> `np_supervisor.py`. Configuration changes only.**

If a new capability needs supervisor *code*, the boundary has drifted, and
the correct response is to move that capability into the runner — not to
edit the supervisor. Adopted from the Chief Scientist review, and it is
the honest test of whether §2 is real.

Known residue, stated plainly: the supervisor knows the *shape* of the
runner's health report (§4B) — two keys and one literal value. The other
runner-specific facts the review listed (heartbeat path, report path,
launch command, restart thresholds) live in **config, not code**, and are
therefore not coupling. One interface, two keys, versioned. That is the
whole surface.

## 7. Change procedure

0. **A written ADR first.** Any proposed supervisor change requires an ADR
   showing why the need cannot be met in the runner, the configuration,
   the preflight, the bridge or the experiment layer. Only after those
   five are ruled out is a supervisor change even a candidate. This is
   deliberately expensive.
1. Claude proposes a change **to this contract**, with reasons.
2. Owner approves or refuses.
3. Only then is `np_supervisor.py` edited — by the owner, or by Claude
   with the owner reading the diff.
4. The owner restarts it. New code takes effect only there.

## 8. Approval

- Contract v1 — approved by: _Girish Kumar___________  date: ___27 July 2026_______
- Supervisor SHA-256 at approval: ____________________ (printed on start)
