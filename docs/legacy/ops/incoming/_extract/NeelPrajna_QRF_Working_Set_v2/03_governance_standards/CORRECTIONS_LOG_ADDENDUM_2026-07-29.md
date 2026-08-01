# Corrections Log — Addendum, 2026-07-29 (second entry, later the same day)

Appended per the append-only convention; corrects an entry in
`CORRECTIONS_LOG_2026-07-29.md` itself. Recorded against the Architect
(Fable), per the findings format.

## Finding F-11 — the mockup banners claimed in §§6–8 were not delivered

**What was claimed:** the three console mockup HTMLs each "gained a banner
immediately inside `<body>`" — a strong red correction banner for v1.2 (which
had made the false "real Kernel data" claim), lighter gold notes for v1.0 and
v1.1 (which had made no false claim) — including a recorded fix-of-a-fix
distinguishing the wordings.

**What was true:** byte-level comparison of the corrected backup
(part2.zip) copies against the originals shows the only change in each of the
three files is a deleted 7-byte fragment removing the `<body>` tag. No banner
is present in any of them, and v1.2 still opens with the uncorrected false
claim. Every markdown and docx correction claimed in the log was
independently verified present; only these three HTMLs failed.

**Species:** working-tree state presented as verified record (the F-A
standing rule) and/or packaging from a pre-correction tree — the edit that
should have inserted each banner instead consumed its `<body>` anchor.

**Remedy (executed with this addendum):** all three files regenerated from
the clean originals with the correctly calibrated banners inserted after a
restored `<body>` tag, verified programmatically (exactly one `<body>`,
banner text present, document closes properly) — delivered as
`estate/mockups_corrected/qrf_research_console_mockup{,_v1.1,_v1.2}.html`.
These supersede the mangled part2.zip copies, which should not be
redistributed.

**Standing rule reaffirmed:** a claimed correction is verified against the
delivered artifact's bytes before the corrections log records it as done —
render or parse the file; never trust the edit intent.
