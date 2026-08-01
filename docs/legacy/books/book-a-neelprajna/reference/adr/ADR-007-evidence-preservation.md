# ADR-007 — Evidence preservation

- Status: **ACCEPTED** — owner ruling recorded 2026-07-27 (§10). The §11
  question on behaviour when the secondary volume is absent was ruled on
  2026-07-28. **No items remain open.**
- Date: 2026-07-27
- Context: `F:\NeelPrajna\runs\` (A2) is about to become the archive of every
  sealed evidence bundle the laboratory produces. C:, E: and F: are
  partitions of **one** physical disk. From a reliability standpoint that is
  one copy, not three. A2 must not start until this is decided.
- Relates to: ADR-004 (evidence rules, INCOMPLETE is never repaired),
  ADR-005 (autonomy and governance), automation v2 design v1.1 + amendment
  v1.2, ADR-006 (git job — covers source, not evidence).

---

## 1. Why this is a scientific ADR and not an IT one

Every ADR so far has protected execution, governance, evidence, autonomy or
traceability. This one protects **persistence**, which sits underneath all of
them.

A sealed bundle has scientific value only if it survives. The project has
deliberately adopted the rule that an INCOMPLETE bundle is never repaired and
never reconstructed. That rule is what makes the evidence trustworthy — and
it is exactly what removes any recovery path if the disk dies. One hardware
failure would destroy every bundle, every baseline, every lineage and every
passport, with no legitimate way to rebuild them.

So backup is not convenience here. It is a precondition of the method.

## 2. Decision

> **A sealed evidence bundle is not considered preserved until it exists on
> at least two independent failure domains, and the second copy has been
> verified byte-for-byte against its manifest.**

Two folders are not two domains. Two partitions are not two domains. Two
physical devices are.

## 3. What "independent failure domain" honestly means

This must be stated precisely, or the rule will be satisfied on paper while
the risk remains.

| Failure mode | C:/E:/F: alone | + D: (external) | + offsite |
|---|---|---|---|
| Disk / controller failure | lost | **survives** | survives |
| Accidental delete, bad script | lost | lost (if attached) | survives |
| Ransomware / OS compromise | lost | lost (if attached) | survives |
| Fire, flood, theft, power surge | lost | lost | **survives** |

D: closes the failure mode that is by far the most likely — a disk dying —
and it closes it today, with hardware already on the desk. It does **not**
close site loss or logical destruction, because it lives in the same room, on
the same machine, under the same user account.

Therefore:

- **Tier 1 (adopt now):** D: — a second physical device. Satisfies §2.
- **Tier 2 (named, not yet scheduled):** an offsite copy, cloud object
  storage or a rotated drive kept elsewhere. Required before any result is
  treated as a permanent scientific record. Parked with a stage number, not
  forgotten.

Claiming Tier 1 is full preservation would be dishonest. It is one domain of
two that matter, and the better one to fix first.

## 4. The lifecycle changes

Current:

```
Run → Bundle COMPLETE → Seal
```

New:

```
Run → Bundle COMPLETE → Seal → Replicate → Verify → PRESERVED
```

**The experiment is not finished until preservation succeeds.** Replicate and
verify run as the final stage of the job, before the job reports done. "Done"
must mean preserved, or the word is misleading.

## 5. Preservation state is observable

Bundle status gains a second, independent field. Bundle state and
preservation state are never collapsed into one value.

```json
{
  "bundle_state": "COMPLETE",
  "preservation_state": "PRESERVED",
  "copies": [
    { "domain": "primary",   "path": "F:\\NeelPrajna\\runs\\<id>",  "verified": true },
    { "domain": "secondary", "path": "D:\\NeelPrajna\\runs\\<id>",  "verified": true }
  ],
  "verified_at": "2026-07-27T00:00:00Z"
}
```

Permitted values of `preservation_state`:

- `PRESERVED` — replicated and verified on a second domain.
- `PRESERVATION_PENDING` — sealed, but the second copy does not yet exist or
  has not verified.
- `PRESERVATION_FAILED` — verification ran and the copy did not match. This
  is a hardware or transfer fault and it is loud.

## 6. Verify means re-hash, not "the copy command returned 0"

Verification recomputes the hash of every file **at the destination** and
compares it against the sealed manifest. File size, timestamp and a zero exit
code are not evidence of a good copy; silent corruption is precisely the
failure this ADR exists to catch.

A copy that does not verify is not counted. `copies` records only verified
copies.

## 7. Fail-closed behaviour

If replication or verification fails:

- The bundle is **never deleted**.
- It is **never marked preserved**.
- It stays `PRESERVATION_PENDING` or `PRESERVATION_FAILED` and the laboratory
  reports, in plain words: *scientific evidence exists but has not yet been
  safely preserved.*
- The count of unpreserved bundles appears in the health output. A non-zero
  count is a standing defect, not a note.

## 8. Retrying a copy is not repairing evidence

This needs saying, because it looks like it collides with ADR-004.

- **Repairing a bundle is forbidden.** If a run produced an INCOMPLETE or
  corrupt bundle, that bundle stays broken forever. The experiment is re-run;
  the evidence is not edited.
- **Re-copying a bundle is allowed and encouraged.** The source bytes and the
  seal are unchanged. Replication is transport, not authorship. A `preserve`
  sweep may retry every `PRESERVATION_PENDING` bundle whenever the secondary
  domain returns.

The distinction: repair changes what the evidence says. Replication does not.

## 9. The secondary volume is identified by fingerprint, not by letter

`D:` is a drive letter, not an identity. Letters move when devices are
plugged in and out. The runner must not cheerfully write bundles to whatever
happens to be D: today.

- The secondary volume is recorded by **volume serial number plus label**,
  stored in the laboratory config, and checked before every replication.
- Wrong volume, or no volume: replication does not run, and the bundle goes
  `PRESERVATION_PENDING`. It never falls back to another path.
- Free space is checked with a floor (proposed 50 GB) exactly as the
  supervisor checks the primary disk today.
- Changing the secondary volume is recorded, the same way a broker or
  terminal-build change is recorded. It does not start a new experiment
  lineage — preservation is not part of the experimental environment — but it
  is logged.

**Secondary volume — confirmed 2026-07-27:**

| Field | Value |
|---|---|
| Label | `Transcend` |
| Volume serial | `DC1AE50A` |
| Drive letter (today) | `D:` — not an identity, see above |
| Physical disk | `1` — StoreJet Transcend, **BusType USB**, 2,000,398,934,016 bytes |
| Capacity | 2,000,396,283,904 bytes total / 1,261,087,834,112 free |

**Primary volumes — confirmed same physical disk:**

| Letter | Serial | Physical disk |
|---|---|---|
| C: | `DEACD42B` | `0` |
| E: | `42CAE9B1` | `0` |
| F: | `04DF275A` | `0` |

Physical disk 0 is a `ST1000DM003-1ER162` HDD, 1,000,204,886,016 bytes,
BusType RAID. C:, E: and F: are partitions of it. The premise of this ADR is
therefore measured, not assumed.

The serial `DC1AE50A` is written into `lab\supervisor.json` before A2 begins.

## 10. Owner ruling

The principle in §2 and the lifecycle in §4 originate with the owner
(2026-07-27). Recorded here for signature.

> Ruling: **ACCEPTED.** The principle in §2, the lifecycle in §4, the
> observable states in §5, and the fail-closed behaviour in §7 are adopted.
> A2 does not start until the archive is built against them.
>
> Date: 2026-07-27

## 11. Consequences for A2

A2 is amended before it starts, rather than built and retrofitted:

1. The archive layout is defined once and used identically on both domains.
2. The manifest gains the §5 fields.
3. Replication + verification become the closing stage of the bundle
   lifecycle, not a separate tool.
4. `np_preflight.py` gains a secondary-volume check (present, correct serial,
   enough free space).
5. A `preserve` sweep exists to retry pending bundles.
6. The health output reports the number of unpreserved bundles.

**Open question for the ruling.** If the secondary volume is absent when a
run is requested, should the run be refused, or allowed with the bundle
marked `PRESERVATION_PENDING`?

Recommendation: **allow the run, mark it pending, report it loudly, sweep it
later.** Refusing would make an unplugged USB cable stop the laboratory,
which trades a certain cost against an unlikely one. The evidence still
exists on the primary; it is the second copy that is late, and the state
field makes that visible rather than hidden.

---

## 12. Owner ruling on the §11 question

- Date: **2026-07-28**
- Ruling: **APPROVED — allow the run.**

> The laboratory shall permit execution when secondary preservation storage
> is unavailable, provided the evidence bundle is successfully sealed. Such
> bundles must be marked `PRESERVATION_PENDING` and remain visibly pending
> until replication and verification complete successfully.

**Reasoning recorded with the ruling.** The laboratory has two separable
responsibilities: produce scientifically valid evidence, and preserve it. An
absent secondary volume affects only the second. If sealing succeeded, the
hashes are correct and the manifest is complete, then the bundle is
scientifically valid — it has simply not yet satisfied the preservation
policy. That is a different condition from evidence corruption, and the two
must never be collapsed into one state. A six-hour experiment is not refused
because a USB cable was unplugged.

### 12.1 Required safeguard — no silent degradation

Pending preservation must be impossible to miss. Each of the following must
state it plainly, in words, not by omission:

- the health report
- the bundle's own preservation record
- the run summary
- the dashboard

Wording to carry: *preservation incomplete — secondary copy not yet
verified.* A bundle may never appear finished while its second copy is
missing. A non-zero count of unpreserved bundles is a standing defect (§7),
not a note.

### 12.2 Implementation note — where the state actually lives

Discovered during implementation, 2026-07-28. Sealed bundles are read-only
and append-only, so `preservation_state` **cannot** be written into the
sealed `manifest.json` as §5 depicts. It is written as a new file,
`preservation.json`, beside the manifest. This is consistent with the SEALED
marker's own rule that improvements are added as new files and nothing in a
sealed bundle is ever edited.

The §5 field names and permitted values are unchanged. Only their location
moves. Writing them into the manifest would have required editing a sealed
artifact, which ADR-004 and §8 of this ADR both forbid.

### 12.3 Volume monitoring — owner position, 2026-07-28

The supervisor stays **frozen**. Verifying free space on every volume that
can invalidate execution is a **runner / preflight** responsibility, not a
supervisor change. That preserves the architectural boundary in ADR-005 G3.

Volumes that can invalidate a run:

| Volume | Why it matters |
|---|---|
| `C:` | MT5 data directory, tester cache, real-tick history, `Common\Files` |
| `F:` | repo, `runs\`, bridge |
| `D:` | only when preservation is required during the run |

Today the supervisor checks free space **only on the volume holding
`health_dir`**, which is F:. For an MT5 run that writes its history cache and
logs to C:, that is the wrong failure signal: C: can fill to zero and the
supervisor will still report HEALTHY. Recorded 2026-07-28 with C: at 42.9 GB
free of 230.96 GB.
